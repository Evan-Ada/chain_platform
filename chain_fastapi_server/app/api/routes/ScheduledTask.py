"""ScheduledTask 调度任务管理路由。"""

from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.core.scheduler import scheduler
from app.models import ScheduledTask

router = APIRouter(prefix="/ScheduledTask", tags=["ScheduledTask"])


# ── 请求模型 ──


class ListScheduledTaskM(BaseModel):
    biz_type: str | None = None
    enabled: bool | None = None
    page_num: int = 1
    page_size: int = 20


class AddScheduledTaskM(BaseModel):
    name: str
    biz_type: str
    biz_id: int | None = None
    cron_expr: str
    enabled: bool = True


class UpdateScheduledTaskM(BaseModel):
    id: int
    name: str | None = None
    cron_expr: str | None = None
    enabled: bool | None = None


class DeleteScheduledTaskM(BaseModel):
    id: int


class ToggleScheduledTaskM(BaseModel):
    id: int
    enabled: bool


class RunNowM(BaseModel):
    id: int


class PreviewCronM(BaseModel):
    cron_expr: str


# ── 路由 ──


@router.post("/list")
async def listScheduledTasks(pm: ListScheduledTaskM, db: SessionDep, current_user: CurrentUser):
    """分页查询调度任务。"""
    stmt = select(ScheduledTask).where(ScheduledTask.owner_user_id == current_user.id)
    count_stmt = select(ScheduledTask).where(ScheduledTask.owner_user_id == current_user.id)

    if pm.biz_type is not None:
        stmt = stmt.where(ScheduledTask.biz_type == pm.biz_type)
        count_stmt = count_stmt.where(ScheduledTask.biz_type == pm.biz_type)

    if pm.enabled is not None:
        stmt = stmt.where(ScheduledTask.enabled == pm.enabled)
        count_stmt = count_stmt.where(ScheduledTask.enabled == pm.enabled)

    total = len(list(db.exec(count_stmt).all()))
    offset = (pm.page_num - 1) * pm.page_size
    stmt = stmt.order_by(ScheduledTask.created_at.desc()).offset(offset).limit(pm.page_size)
    tasks = list(db.exec(stmt).all())

    data = [_task_to_dict(t) for t in tasks]
    return resp_200(200, "查询成功", {"total": total, "res": data})


@router.post("/add")
async def addScheduledTask(pm: AddScheduledTaskM, db: SessionDep, current_user: CurrentUser):
    """新增调度任务。"""
    task = ScheduledTask(
        name=pm.name,
        biz_type=pm.biz_type,
        biz_id=pm.biz_id,
        cron_expr=pm.cron_expr,
        enabled=pm.enabled,
        owner_user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 注册到调度器
    if task.enabled:
        _register_job(task)

    return resp_200(200, "添加成功", _task_to_dict(task))


@router.post("/update")
async def updateScheduledTask(pm: UpdateScheduledTaskM, db: SessionDep, current_user: CurrentUser):
    """更新调度任务。"""
    task = db.get(ScheduledTask, pm.id)
    if not task or task.owner_user_id != current_user.id:
        return resp_400(400, "任务不存在")

    if pm.name is not None:
        task.name = pm.name
    if pm.cron_expr is not None:
        task.cron_expr = pm.cron_expr
    if pm.enabled is not None:
        task.enabled = pm.enabled

    db.add(task)
    db.commit()
    db.refresh(task)

    # 重新注册
    try:
        scheduler.remove_job(f"task_{task.id}")
    except Exception:
        pass
    if task.enabled:
        _register_job(task)

    return resp_200(200, "更新成功", _task_to_dict(task))


@router.post("/delete")
async def deleteScheduledTask(pm: DeleteScheduledTaskM, db: SessionDep, current_user: CurrentUser):
    """删除调度任务。"""
    task = db.get(ScheduledTask, pm.id)
    if not task or task.owner_user_id != current_user.id:
        return resp_400(400, "任务不存在")

    try:
        scheduler.remove_job(f"task_{task.id}")
    except Exception:
        pass

    db.delete(task)
    db.commit()
    return resp_200(200, "删除成功")


@router.post("/toggle")
async def toggleScheduledTask(pm: ToggleScheduledTaskM, db: SessionDep, current_user: CurrentUser):
    """启用/禁用调度任务。"""
    task = db.get(ScheduledTask, pm.id)
    if not task or task.owner_user_id != current_user.id:
        return resp_400(400, "任务不存在")

    task.enabled = pm.enabled
    db.add(task)
    db.commit()
    db.refresh(task)

    if pm.enabled:
        _register_job(task)
    else:
        try:
            scheduler.remove_job(f"task_{task.id}")
        except Exception:
            pass

    return resp_200(200, "操作成功", _task_to_dict(task))


@router.post("/runNow")
async def runNow(pm: RunNowM, db: SessionDep, current_user: CurrentUser):
    """立即触发任务执行（直接调用 ContentFetchService）。"""
    from app.services.content_fetch import ContentFetchService
    from app.models import Subscription

    task = db.get(ScheduledTask, pm.id)
    if not task or task.owner_user_id != current_user.id:
        return resp_400(400, "任务不存在")

    if task.biz_type == "subscription" and task.biz_id:
        sub = db.get(Subscription, task.biz_id)
        if not sub:
            return resp_400(400, "关联订阅不存在")
        service = ContentFetchService()
        new_count = await service.fetch_and_save(sub, db)
        return resp_200(200, f"抓取完成，新增 {new_count} 条", {"new_count": new_count})

    return resp_400(400, "该任务类型不支持手动触发")


@router.post("/previewNext")
async def previewNext(pm: PreviewCronM, db: SessionDep, current_user: CurrentUser):
    """预览 cron 接下来 5 次执行时间。"""
    try:
        cron = croniter(pm.cron_expr, datetime.now())
        next_runs = [cron.get_next(datetime).isoformat() for _ in range(5)]
        return resp_200(200, "查询成功", {"next_runs": next_runs})
    except Exception as e:
        return resp_400(400, f"无效 cron 表达式: {e}")


# ── 私有方法 ──


def _parse_cron(cron_expr: str) -> CronTrigger | None:
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None
    return CronTrigger(
        minute=parts[0], hour=parts[1], day=parts[2],
        month=parts[3], day_of_week=parts[4],
        timezone="Asia/Shanghai",
    )


def _register_job(task: ScheduledTask) -> None:
    trigger = _parse_cron(task.cron_expr)
    if not trigger:
        return
    job_id = f"task_{task.id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    scheduler.add_job(
        _run_task_job,
        trigger=trigger,
        id=job_id,
        args=[task.id],
        replace_existing=True,
    )


async def _run_task_job(task_id: int) -> None:
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.content_fetch import ContentFetchService
    from app.models import Subscription

    with Session(engine) as db:
        task = db.get(ScheduledTask, task_id)
        if not task or not task.enabled:
            return

        if task.biz_type == "subscription" and task.biz_id:
            sub = db.get(Subscription, task.biz_id)
            if sub and sub.enabled:
                service = ContentFetchService()
                await service.fetch_and_save(sub, db)
                task.last_run_at = datetime.now()
                db.add(task)
                db.commit()


def _task_to_dict(task: ScheduledTask) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "biz_type": task.biz_type,
        "biz_id": task.biz_id if task.biz_id else None,
        "cron_expr": task.cron_expr,
        "enabled": task.enabled,
        "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
        "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
        "owner_user_id": task.owner_user_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }
