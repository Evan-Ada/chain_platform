"""scheduler_v2：全局调度 + rehydrate。

从数据库恢复所有 enabled 的 ScheduledTask 到 APScheduler，
并提供 Subscription 生命周期与调度器的同步接口。
"""

from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlmodel import Session, select

from app.core.db import engine
from app.core.scheduler import scheduler
from app.models import ScheduledTask, Subscription
from app.services.content_fetch import ContentFetchService


def _parse_cron(cron_expr: str) -> CronTrigger | None:
    """将 5 段 cron 表达式解析为 CronTrigger。"""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None
    return CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone="Asia/Shanghai",
    )


async def _run_job(task_id: int) -> None:
    """APScheduler 回调：根据 biz_type 分发任务。"""
    with Session(engine) as db:
        task = db.get(ScheduledTask, task_id)
        if not task or not task.enabled:
            logger.info(f"任务已禁用或不存在: id={task_id}")
            return

        logger.info(f"触发任务: {task.name} (id={task_id})")

        if task.biz_type == "subscription" and task.biz_id:
            sub = db.get(Subscription, task.biz_id)
            if sub and sub.enabled:
                service = ContentFetchService()
                await service.fetch_and_save(sub, db)
                # 更新 last_run_at / next_run_at
                task.last_run_at = datetime.now()
                next_runs = scheduler.get_job(f"task_{task.id}").next_run_time if scheduler.get_job(f"task_{task.id}") else None
                task.next_run_at = next_runs
                db.add(task)
                db.commit()
        else:
            logger.warning(f"未知 biz_type: {task.biz_type}，任务跳过")


class ScheduledTaskService:
    """调度任务服务。"""

    @staticmethod
    def rehydrate() -> None:
        """从数据库加载所有 enabled 的 ScheduledTask 到调度器。"""
        with Session(engine) as db:
            tasks = db.exec(select(ScheduledTask).where(ScheduledTask.enabled == True)).all()
            for task in tasks:
                trigger = _parse_cron(task.cron_expr)
                if not trigger:
                    logger.warning(f"无效 cron 表达式: {task.cron_expr}，跳过任务 {task.id}")
                    continue
                job_id = f"task_{task.id}"
                try:
                    scheduler.remove_job(job_id)
                except Exception:
                    pass
                scheduler.add_job(
                    _run_job,
                    trigger=trigger,
                    id=job_id,
                    args=[task.id],
                    replace_existing=True,
                )
                logger.info(f"已恢复调度任务: {task.name} (id={task.id})")

    @staticmethod
    def upsert_from_subscription(sub: Subscription) -> None:
        """根据 Subscription 插入或更新 ScheduledTask。"""
        with Session(engine) as db:
            existing = db.exec(
                select(ScheduledTask).where(
                    ScheduledTask.biz_type == "subscription",
                    ScheduledTask.biz_id == sub.id,
                )
            ).first()

            if existing:
                existing.name = f"sub::{sub.id}"
                existing.cron_expr = sub.schedule_cron
                existing.enabled = sub.enabled
                db.add(existing)
                task = existing
            else:
                task = ScheduledTask(
                    name=f"sub::{sub.id}",
                    biz_type="subscription",
                    biz_id=sub.id,
                    cron_expr=sub.schedule_cron,
                    enabled=sub.enabled,
                    owner_user_id=sub.user_id,
                )
                db.add(task)
                db.flush()

            db.commit()
            db.refresh(task)

            # 同步到调度器
            if task.enabled:
                trigger = _parse_cron(task.cron_expr)
                if trigger:
                    job_id = f"task_{task.id}"
                    try:
                        scheduler.remove_job(job_id)
                    except Exception:
                        pass
                    scheduler.add_job(
                        _run_job,
                        trigger=trigger,
                        id=job_id,
                        args=[task.id],
                        replace_existing=True,
                    )
            else:
                try:
                    scheduler.remove_job(f"task_{task.id}")
                except Exception:
                    pass

    @staticmethod
    def remove_for_subscription(sub_id: int) -> None:
        """删除 Subscription 对应的调度任务。"""
        with Session(engine) as db:
            task = db.exec(
                select(ScheduledTask).where(
                    ScheduledTask.biz_type == "subscription",
                    ScheduledTask.biz_id == sub_id,
                )
            ).first()

            if task:
                try:
                    scheduler.remove_job(f"task_{task.id}")
                except Exception:
                    pass
                db.delete(task)
                db.commit()
