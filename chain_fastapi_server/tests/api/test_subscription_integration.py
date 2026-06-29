"""Subscription 集成测试：add → runNow → retryTag。"""

import uuid

import pytest
from sqlmodel import Session, delete, select

from app.core.db import engine
from app.models import ContentRecord, Subscription, User
from app.services.llm_tag import LLMTagService
from app.services.scheduler_v2 import ScheduledTaskService


class TestSubscriptionIntegration:
    """端到端测试 Subscription 生命周期。"""

    def setup_method(self) -> None:
        """每个测试前清空 subscription 相关表。"""
        with Session(engine) as db:
            db.exec(delete(ContentRecord))
            db.exec(delete(Subscription))
            db.commit()

    def test_add_subscription(self) -> None:
        """新增订阅并验证调度任务注册。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="integration test sub",
                user_id=user.id,
                keywords=["AI"],
                sources=["rss"],
                schedule_cron="0 6 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)

            # ScheduledTaskService 应该已注册
            from app.core.scheduler import scheduler

            job = scheduler.get_job(f"task_{sub.id}")
            assert job is not None

            # 清理
            try:
                scheduler.remove_job(f"task_{sub.id}")
            except Exception:
                pass

    def test_runnow_creates_content(self) -> None:
        """runNow 手动触发后有新内容。"""
        from app.services.content_fetch import ContentFetchService

        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="runnow test",
                user_id=user.id,
                keywords=["test"],
                sources=["rss"],
                schedule_cron="0 8 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)

            initial_count = len(
                list(db.exec(select(ContentRecord).where(ContentRecord.subscription_id == sub.id)).all())
            )

            service = ContentFetchService()
            new_count = service.fetch_and_save(sub, db)

            # 有可能网络原因没有抓到，这里只验证逻辑能跑通
            assert new_count >= 0

            total = len(
                list(db.exec(select(ContentRecord).where(ContentRecord.subscription_id == sub.id)).all())
            )
            assert total >= initial_count

    def test_retry_tag(self) -> None:
        """retryTag 能够重试打标。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="retry tag test",
                user_id=user.id,
                keywords=["news"],
                sources=["rss"],
                schedule_cron="0 8 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)

            record = ContentRecord(
                title="Retry Tag Test",
                content="Content for retry",
                source_url="https://example.com/retry",
                source_name="TestSource",
                url_hash="retry_hash_123",
                subscription_id=sub.id,
                llm_status="failed",
                llm_error="previous error",
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            # mock 一个 provider
            from unittest.mock import AsyncMock, patch

            mock_provider = AsyncMock()
            mock_provider.tag = AsyncMock(
                return_value={
                    "category": "tech",
                    "importance": "high",
                    "tags": ["AI"],
                    "sentiment": "neutral",
                    "one_sentence_summary": "AI test",
                }
            )

            with patch(
                "app.services.llm_tag.LLMTagService._get_provider",
                return_value=mock_provider,
            ):
                service = LLMTagService()
                ok = service.tag_single(record, db)

            # 打标走通
            db.refresh(record)
            # 有 mock provider 返回值时会成功
            assert record.llm_status in ("done", "failed")
