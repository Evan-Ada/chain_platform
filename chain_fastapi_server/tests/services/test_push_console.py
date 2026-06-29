"""即时终端推送单元测试。"""

import uuid

import pytest
from sqlmodel import Session, select

from app.core.db import engine
from app.models import ContentRecord, PushMessage, PushPreference, Subscription, User
from app.services.push_service import PushService


class TestPushConsole:
    @pytest.fixture(autouse=True)
    def cleanup(self) -> None:
        self._created_sub_ids: list[int] = []
        self._created_record_ids: list[int] = []
        self._created_msg_ids: list[int] = []
        yield
        with Session(engine) as db:
            for mid in self._created_msg_ids:
                m = db.get(PushMessage, mid)
                if m:
                    db.delete(m)
            for rid in self._created_record_ids:
                r = db.get(ContentRecord, rid)
                if r:
                    db.delete(r)
            for sid in self._created_sub_ids:
                s = db.get(Subscription, sid)
                if s:
                    db.delete(s)
            db.commit()

    @pytest.mark.asyncio
    async def test_push_immediate_writes_messages(self) -> None:
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="push test",
                user_id=user.id,
                keywords=[],
                sources=["ssr"],
                schedule_cron="0 8 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
            self._created_sub_ids.append(sub.id)

            uid = uuid.uuid4().hex[:12]
            record = ContentRecord(
                subscription_id=sub.id,
                title="测试人工智能新闻",
                content="内容摘要",
                source_url=f"https://example.com/push-{uid}",
                source_name="36kr",
                url_hash=f"hash_{uid}",
                keywords_matched=["人工智能"],
                llm_status="pending",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            self._created_record_ids.append(record.id)

            count = await PushService.push_immediate_for_records(
                user.id,
                sub.id,
                [record.id],
                db=db,
                console=False,
            )
            assert count == 1

            msgs = list(
                db.exec(
                    select(PushMessage).where(PushMessage.user_id == user.id)
                ).all()
            )
            assert len(msgs) == 1
            self._created_msg_ids.extend(m.id for m in msgs if m.id)
            assert msgs[0].channel == "app"
            assert msgs[0].status == "sent"
            assert "人工智能" in msgs[0].tags
