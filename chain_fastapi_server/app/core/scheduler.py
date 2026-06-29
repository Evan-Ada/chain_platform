"""APScheduler 调度器模块。

提供全局 AsyncIOScheduler 实例，供路由注册定时任务。
"""

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobEvent, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger


def _job_listener(event: JobEvent) -> None:
    """任务执行事件监听器。"""
    if isinstance(event, JobExecutionEvent):
        if event.exception:
            logger.error(f"定时任务异常 job_id={event.job_id}, exception={event.exception}")
        else:
            logger.info(f"定时任务完成 job_id={event.job_id}")


scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
