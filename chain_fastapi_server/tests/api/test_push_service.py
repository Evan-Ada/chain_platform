"""PushService 测试。"""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, delete, select

from app.core.db import engine
from app.models import ContentRecord, PushMessage, PushPreference, Subscription, User
from app.services.push_service import PushService


class TestPushService:
    """测试 PushService 的 dispatch / run_pending / send_email。"""

    def setup_method(self) -> None:
        """每个测试前清空 push 相关表。"""
        with Session(engine) as db:
            db.exec(delete(PushMessage))
            db.exec(delete(PushPreference))
            db.commit()

    def test_dispatch_daily_creates_messages(self) -> None:
        """dispatch_daily 为用户生成推送消息。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="test push sub",
                user_id=user.id,
                keywords=["news"],
                sources=["rss"],
                schedule_cron="0 8 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)

            # 插入一条 content record
            record = ContentRecord(
                title="Test News Article",
                content="This is test content",
                source_url="https://example.com/test",
                source_name="TestSource",
                url_hash="abc123",
                subscription_id=sub.id,
                llm_tags={
                    "importance": "high",
                    "tags": ["tech"],
                    "category": "tech",
                },
            )
            db.add(record)
            db.commit()

            count = PushService.dispatch_daily(user.id, date.today())

            assert count >= 1
            msgs = db.exec(select(PushMessage).where(PushMessage.user_id == user.id)).all()
            assert len(msgs) >= 1

    def test_run_pending_marks_sent(self) -> None:
        """run_pending 将 pending 消息标记为 sent/failed。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            # 插入一条 pending app 消息
            msg = PushMessage(
                user_id=user.id,
                title="Test Push",
                summary="Test summary",
                tags=["tech"],
                importance="medium",
                channel="app",
                status="pending",
                push_date=date.today(),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            msg_id = msg.id

        # app channel 不需要真实发邮件，直接标记 sent
        import asyncio

        asyncio.run(PushService.run_pending())

        with Session(engine) as db:
            updated = db.get(PushMessage, msg_id)
            assert updated.status == "sent"

    def test_send_email_disabled(self) -> None:
        """ENABLE_EMAIL_PUSH=False 时邮件发送返回 False。"""
        from app.core import config

        old_val = config.settings.ENABLE_EMAIL_PUSH
        config.settings.ENABLE_EMAIL_PUSH = False

        try:
            with Session(engine) as db:
                user = db.exec(select(User).limit(1)).first()
                if not user:
                    pytest.skip("No user in DB")

                msg = PushMessage(
                    user_id=user.id,
                    title="Email Test",
                    summary="Test",
                    tags=[],
                    importance="high",
                    channel="email",
                    status="pending",
                    push_date=date.today(),
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                ok = PushService.send_email(user.id, [msg.id])
                assert ok is False

                db.refresh(msg)
                assert msg.status == "failed"
        finally:
            config.settings.ENABLE_EMAIL_PUSH = old_val
