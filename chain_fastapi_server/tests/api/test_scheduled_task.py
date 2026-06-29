"""ScheduledTask 调度任务测试。"""

import uuid

import pytest
from sqlmodel import Session, delete, select

from app.core.db import engine
from app.models import ScheduledTask, User
from app.services.scheduler_v2 import ScheduledTaskService


class TestScheduledTaskService:
    """测试 ScheduledTaskService 的增删改查与调度器集成。"""

    def setup_method(self) -> None:
        """每个测试前清空 scheduledtask 表。"""
        with Session(engine) as db:
            db.exec(delete(ScheduledTask))
            db.commit()

    def test_add_and_rehydrate(self) -> None:
        """add 后 rehydrate 能看到任务。"""
        with Session(engine) as db:
            # 获取一个测试用户
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            task = ScheduledTask(
                name="test task",
                biz_type="subscription",
                biz_id=uuid.uuid4(),
                cron_expr="0 8 * * *",
                enabled=True,
                owner_user_id=user.id,
            )
            db.add(task)
            db.commit()
            task_id = task.id

        # rehydrate
        ScheduledTaskService.rehydrate()

        from app.core.scheduler import scheduler

        job = scheduler.get_job(f"task_{task_id}")
        assert job is not None

        # 清理
        from app.core.scheduler import scheduler

        try:
            scheduler.remove_job(f"task_{task_id}")
        except Exception:
            pass

    def test_toggle_task(self) -> None:
        """toggle 启用/禁用任务。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            task = ScheduledTask(
                name="toggle test",
                biz_type="custom",
                cron_expr="0 9 * * *",
                enabled=True,
                owner_user_id=user.id,
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            task.enabled = False
            db.add(task)
            db.commit()

            # 禁用后 rehydrate，调度器应无此 job
            ScheduledTaskService.rehydrate()

            from app.core.scheduler import scheduler

            job = scheduler.get_job(f"task_{task.id}")
            assert job is None

    def test_delete_task(self) -> None:
        """delete 后任务从调度器移除。"""
        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            task = ScheduledTask(
                name="delete test",
                biz_type="custom",
                cron_expr="0 10 * * *",
                enabled=True,
                owner_user_id=user.id,
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            task_id = task.id

        # 先注册
        ScheduledTaskService.rehydrate()

        from app.core.scheduler import scheduler

        job = scheduler.get_job(f"task_{task_id}")
        assert job is not None

        # 删除
        ScheduledTaskService.remove_for_subscription(task_id)

        job2 = scheduler.get_job(f"task_{task_id}")
        assert job2 is None

    def test_upsert_from_subscription(self) -> None:
        """upsert_from_subscription 正确创建/更新调度任务。"""
        from app.models import Subscription

        with Session(engine) as db:
            user = db.exec(select(User).limit(1)).first()
            if not user:
                pytest.skip("No user in DB")

            sub = Subscription(
                name="test sub",
                user_id=user.id,
                keywords=[],
                sources=["rss"],
                schedule_cron="0 7 * * *",
                enabled=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)

            ScheduledTaskService.upsert_from_subscription(sub)

            # 验证调度任务存在
            from app.core.scheduler import scheduler

            job = scheduler.get_job(f"task_{sub.id}")
            assert job is not None

            # 清理
            try:
                scheduler.remove_job(f"task_{sub.id}")
            except Exception:
                pass
