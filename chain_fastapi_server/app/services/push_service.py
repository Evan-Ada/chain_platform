"""PushService：推送服务。

负责将当日内容打包为 PushMessage，并根据 PushPreference
分发到 email / app 渠道。
"""

import smtplib
from datetime import date, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from app.core.config import settings
from app.models import ContentRecord, PushMessage, PushPreference, Subscription


class PushService:
    """推送服务。"""

    @staticmethod
    async def push_immediate_for_records(
        user_id: int,
        subscription_id: int,
        record_ids: list[int],
        *,
        db: Session,
        console: bool | None = None,
    ) -> int:
        """为本次新增内容即时生成 PushMessage，并可选终端打印。"""
        if not record_ids:
            return 0

        pref = db.get(PushPreference, user_id)
        if not pref:
            pref = PushPreference(
                id=user_id,
                channels={"email": False, "app": True},
                push_time="08:30:00",
                timezone="Asia/Shanghai",
                daily_digest=True,
                importance_filter=["high", "medium"],
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)

        records = list(
            db.exec(
                select(ContentRecord).where(ContentRecord.id.in_(record_ids))
            ).all()
        )
        pushable = [r for r in records if r.keywords_matched]
        if not pushable:
            return 0

        today = date.today()
        count = 0
        for record in pushable:
            tags = record.keywords_matched or []
            tag_label = tags[0] if tags else "未分类"
            msg = PushMessage(
                user_id=user_id,
                subscription_id=subscription_id,
                content_record_id=record.id,
                title=record.title,
                summary=(record.content or record.title or "")[:500],
                tags=tags,
                importance="medium",
                channel="app",
                status="sent",
                sent_at=datetime.now(timezone.utc),
                push_date=today,
            )
            db.add(msg)
            count += 1

        db.commit()

        use_console = settings.PUSH_CONSOLE if console is None else console
        if use_console and pref.daily_digest:
            PushService._print_console_digest(subscription_id, pushable)
        elif use_console:
            for record in pushable:
                tags = record.keywords_matched or []
                tag_label = tags[0] if tags else "未分类"
                logger.info(f"[PUSH] [{tag_label}] {record.title}")

        logger.info(
            f"即时推送 subscription_id={subscription_id}, "
            f"写入 pushmessage {count} 条"
        )
        return count

    @staticmethod
    def _print_console_digest(subscription_id: int, records: list[ContentRecord]) -> None:
        """终端打印合并摘要。"""
        lines = [f"[PUSH] 36kr 订阅 #{subscription_id} | 新增 {len(records)} 条"]
        for record in records:
            tags = record.keywords_matched or []
            tag_label = tags[0] if tags else "未分类"
            title = (record.title or "")[:80]
            lines.append(f"  - [{tag_label}] {title}")
        block = "\n".join(lines)
        logger.info(f"\n{block}")

    @staticmethod
    async def dispatch_daily(user_id: int, push_date: date) -> int:
        """生成当日推送消息。"""
        from app.core.db import engine

        with Session(engine) as db:
            pref: PushPreference | None = db.get(PushPreference, user_id)
            if not pref:
                pref = PushPreference(id=user_id)
                db.add(pref)
                db.commit()
                db.refresh(pref)

            importance_filter = pref.importance_filter or ["high", "medium"]
            sub_ids = [
                s.id
                for s in db.exec(
                    select(Subscription).where(Subscription.user_id == user_id)
                ).all()
            ]

            if not sub_ids:
                return 0

            records = db.exec(
                select(ContentRecord).where(
                    ContentRecord.subscription_id.in_(sub_ids),
                    ContentRecord.created_at.has(push_date=push_date),
                )
            ).all()

            filtered = [r for r in records if (r.llm_tags or {}).get("importance", "medium") in importance_filter]

            if not filtered:
                return 0

            count = 0
            from collections import defaultdict

            by_sub: dict = defaultdict(list)
            for r in filtered:
                by_sub[r.subscription_id].append(r)

            for sub_id, recs in by_sub.items():
                for r in recs:
                    tags = (r.llm_tags or {}).get("tags", [])
                    importance = (r.llm_tags or {}).get("importance", "medium")
                    msg = PushMessage(
                        user_id=user_id,
                        subscription_id=sub_id,
                        content_record_id=r.id,
                        title=r.title,
                        summary=(r.content or "")[:500],
                        tags=tags,
                        importance=importance,
                        channel="app",
                        status="pending",
                        push_date=push_date,
                    )
                    db.add(msg)
                    count += 1

            if pref.daily_digest:
                titles = [r.title for r in filtered[:10]]
                summary_text = "\n".join(f"- {t}" for t in titles)
                digest_msg = PushMessage(
                    user_id=user_id,
                    title="每日内容摘要",
                    summary=summary_text,
                    tags=[],
                    importance="medium",
                    channel="email",
                    status="pending",
                    push_date=push_date,
                )
                db.add(digest_msg)
                count += 1

            db.commit()
            logger.info(f"生成推送消息 {count} 条 for user={user_id}, date={push_date}")
            return count

    @staticmethod
    async def run_pending() -> dict[str, int]:
        """处理所有 pending 的 PushMessage。"""
        from app.core.db import engine

        batch_size = settings.PUSH_BATCH_SIZE
        sent_count = 0
        failed_count = 0

        with Session(engine) as db:
            while True:
                msgs = db.exec(
                    select(PushMessage)
                    .where(PushMessage.status == "pending")
                    .limit(batch_size)
                ).all()

                if not msgs:
                    break

                for msg in msgs:
                    if msg.channel == "email":
                        ok = PushService.send_email(msg.user_id, [msg.id])
                        msg.status = "sent" if ok else "failed"
                    else:
                        msg.status = "sent"

                    if msg.status == "sent":
                        sent_count += 1
                    else:
                        failed_count += 1

                    db.add(msg)

                db.commit()

        logger.info(f"推送处理完成: 发送 {sent_count}, 失败 {failed_count}")
        return {"sent": sent_count, "failed": failed_count}

    @staticmethod
    def send_email(user_id: int, message_ids: list) -> bool:
        """发送邮件。"""
        if not settings.ENABLE_EMAIL_PUSH:
            from app.core.db import engine

            with Session(engine) as db:
                for mid in message_ids:
                    msg = db.get(PushMessage, mid)
                    if msg:
                        msg.status = "failed"
                        db.add(msg)
                db.commit()
            logger.warning("邮件发送已禁用 (ENABLE_EMAIL_PUSH=False)")
            return False

        from app.core.db import engine
        from sqlmodel import Session
        from app.models import User

        with Session(engine) as db:
            user = db.get(User, user_id)
            if not user or not user.email:
                logger.warning(f"用户 {user_id} 没有邮箱地址")
                return False

            messages = [db.get(PushMessage, mid) for mid in message_ids]
            messages = [m for m in messages if m]

            html_parts = []
            for msg in messages:
                tags_html = (
                    ", ".join(f"<span>{t}</span>" for t in (msg.tags or []))
                    or "无"
                )
                html_parts.append(
                    f"""
                    <div style="margin-bottom:16px;border-bottom:1px solid #eee;padding-bottom:12px;">
                        <h3 style="margin:0 0 8px;">{msg.title}</h3>
                        <p style="margin:0 0 8px;color:#666;">{msg.summary[:200]}</p>
                        <div>标签: {tags_html}</div>
                        <div>重要程度: {msg.importance}</div>
                    </div>
                    """
                )

            html_body = f"""
            <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
                <h2>每日内容推送</h2>
                {"".join(html_parts)}
            </body></html>
            """

            try:
                msg_root = MIMEMultipart("alternative")
                msg_root["Subject"] = f"每日内容推送 - {date.today().isoformat()}"
                msg_root["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
                msg_root["To"] = user.email
                msg_root.attach(MIMEText(html_body, "html", "utf-8"))

                if settings.SMTP_SSL:
                    server = smtplib.SMTP_SSL(settings.SMTP_HOST or "", settings.SMTP_PORT or 465)
                else:
                    server = smtplib.SMTP(settings.SMTP_HOST or "", settings.SMTP_PORT or 587)
                    if settings.SMTP_TLS:
                        server.starttls()

                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                server.sendmail(
                    settings.EMAILS_FROM_EMAIL,
                    [user.email],
                    msg_root.as_string(),
                )
                server.quit()
                logger.info(f"邮件发送成功 to={user.email}")
                return True
            except Exception as e:
                logger.error(f"邮件发送失败 to={user.email}, error={e}")
                for mid in message_ids:
                    push_msg = db.get(PushMessage, mid)
                    if push_msg:
                        push_msg.status = "failed"
                        db.add(push_msg)
                db.commit()
                return False
