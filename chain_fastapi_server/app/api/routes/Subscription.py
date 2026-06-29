"""内容订阅管理路由。"""

from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.db import engine
from app.core.response import resp_200, resp_400
from app.core.scheduler import scheduler
from app.models import ContentRecord, Subscription
from app.services.content_fetch import ContentFetchService
from app.services.llm_tag import LLMTagService
from app.services.scheduler_v2 import ScheduledTaskService

router = APIRouter(prefix="/Subscription", tags=["Subscription"])


# ── 请求模型 ──


class AddSubscriptionM(BaseModel):
    name: str
    keywords: list[str] = []
    sources: list[str] = ["rss"]
    schedule_type: str = "daily"
    schedule_cron: str = "0 8 * * *"
    enabled: bool = True


class UpdateSubscriptionM(BaseModel):
    id: int
    name: str | None = None
    keywords: list[str] | None = None
    sources: list[str] | None = None
    schedule_type: str | None = None
    schedule_cron: str | None = None
    enabled: bool | None = None


class ToggleSubscriptionM(BaseModel):
    id: int
    enabled: bool


class SearchContentsM(BaseModel):
    subscription_id: int | None = None
    category: str | None = None
    importance: str | None = None
    llm_status: str | None = None
    keyword: str | None = None
    page_num: int = 1
    page_size: int = 20


class RunNowM(BaseModel):
    id: int


class RetryTagM(BaseModel):
    id: int  # content record id


# ── 定时任务函数 ──


async def _run_subscription_fetch(subscription_id: int) -> None:
    """APScheduler 回调：抓取单个订阅内容。"""
    with Session(engine) as db:
        sub = db.get(Subscription, subscription_id)
        if not sub or not sub.enabled:
            return
        service = ContentFetchService()
        await service.fetch_and_save(sub, db)


def _job_id(sub_id: int) -> str:
    return f"sub_{sub_id}"


def _register_job(sub: Subscription) -> None:
    """注册 APScheduler 定时任务。"""
    parts = sub.schedule_cron.strip().split()
    if len(parts) != 5:
        return
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone="Asia/Shanghai",
    )
    job_id = _job_id(sub.id)
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    scheduler.add_job(
        _run_subscription_fetch,
        trigger=trigger,
        id=job_id,
        args=[sub.id],
        replace_existing=True,
    )


# ── 路由 ──


@router.post("/add")
async def addSubscription(pm: AddSubscriptionM, db: SessionDep, current_user: CurrentUser):
    """新增订阅。"""
    sub = Subscription(
        **pm.model_dump(),
        user_id=current_user.id,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    ScheduledTaskService.upsert_from_subscription(sub)
    return resp_200(200, "添加成功", _sub_to_dict(sub))


@router.post("/list")
async def listSubscriptions(db: SessionDep, current_user: CurrentUser):
    """查询当前用户的订阅列表。"""
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subs = list(db.exec(stmt).all())
    data = [_sub_to_dict(s) for s in subs]
    return resp_200(200, "查询成功", {"total": len(data), "res": data})


@router.post("/update")
async def updateSubscription(pm: UpdateSubscriptionM, db: SessionDep, current_user: CurrentUser):
    """更新订阅。"""
    sub = db.get(Subscription, pm.id)
    if not sub or sub.user_id != current_user.id:
        return resp_400(400, "订阅不存在")
    update_data = pm.model_dump(exclude_unset=True, exclude={"id"})
    for k, v in update_data.items():
        setattr(sub, k, v)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    ScheduledTaskService.upsert_from_subscription(sub)
    return resp_200(200, "更新成功", _sub_to_dict(sub))


@router.post("/delete")
async def deleteSubscription(pm: RunNowM, db: SessionDep, current_user: CurrentUser):
    """删除订阅。"""
    sub = db.get(Subscription, pm.id)
    if not sub or sub.user_id != current_user.id:
        return resp_400(400, "订阅不存在")
    ScheduledTaskService.remove_for_subscription(sub.id)
    db.delete(sub)
    db.commit()
    return resp_200(200, "删除成功")


@router.post("/toggle")
async def toggleSubscription(pm: ToggleSubscriptionM, db: SessionDep, current_user: CurrentUser):
    """启用/禁用订阅。"""
    sub = db.get(Subscription, pm.id)
    if not sub or sub.user_id != current_user.id:
        return resp_400(400, "订阅不存在")
    sub.enabled = pm.enabled
    db.add(sub)
    db.commit()
    db.refresh(sub)
    ScheduledTaskService.upsert_from_subscription(sub)
    return resp_200(200, "操作成功", _sub_to_dict(sub))


@router.post("/contents")
async def listContents(pm: SearchContentsM, db: SessionDep, current_user: CurrentUser):
    """查询订阅内容列表（分页 + 多维过滤）。"""
    stmt = select(ContentRecord)
    count_stmt = select(func.count()).select_from(ContentRecord)

    if pm.subscription_id:
        sub = db.get(Subscription, pm.subscription_id)
        if not sub or sub.user_id != current_user.id:
            return resp_400(400, "订阅不存在")
        stmt = stmt.where(ContentRecord.subscription_id == pm.subscription_id)
        count_stmt = count_stmt.where(ContentRecord.subscription_id == pm.subscription_id)
    else:
        user_sub_ids = select(Subscription.id).where(Subscription.user_id == current_user.id)
        stmt = stmt.where(ContentRecord.subscription_id.in_(user_sub_ids))
        count_stmt = count_stmt.where(ContentRecord.subscription_id.in_(user_sub_ids))

    if pm.llm_status:
        stmt = stmt.where(ContentRecord.llm_status == pm.llm_status)
        count_stmt = count_stmt.where(ContentRecord.llm_status == pm.llm_status)

    if pm.keyword:
        stmt = stmt.where(ContentRecord.title.ilike(f"%{pm.keyword}%"))
        count_stmt = count_stmt.where(ContentRecord.title.ilike(f"%{pm.keyword}%"))

    if pm.category:
        stmt = stmt.where(ContentRecord.llm_tags["category"].astext == pm.category)
        count_stmt = count_stmt.where(ContentRecord.llm_tags["category"].astext == pm.category)

    if pm.importance:
        stmt = stmt.where(ContentRecord.llm_tags["importance"].astext == pm.importance)
        count_stmt = count_stmt.where(ContentRecord.llm_tags["importance"].astext == pm.importance)

    total = db.exec(count_stmt).one()

    offset = (pm.page_num - 1) * pm.page_size
    stmt = stmt.order_by(ContentRecord.created_at.desc()).offset(offset).limit(pm.page_size)
    records = list(db.exec(stmt).all())
    data = [r.model_dump() for r in records]
    for d in data:
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
    return resp_200(200, "查询成功", {"total": total, "res": data})


@router.post("/runNow")
async def runNow(pm: RunNowM, db: SessionDep, current_user: CurrentUser):
    """手动触发抓取。"""
    sub = db.get(Subscription, pm.id)
    if not sub or sub.user_id != current_user.id:
        return resp_400(400, "订阅不存在")
    service = ContentFetchService()
    new_count = await service.fetch_and_save(sub, db)
    return resp_200(200, f"抓取完成，新增 {new_count} 条", {"new_count": new_count})


@router.post("/retryTag")
async def retryTag(pm: RetryTagM, db: SessionDep, current_user: CurrentUser):
    """重试单条内容的 LLM 打标。"""
    record = db.get(ContentRecord, pm.id)
    if not record:
        return resp_400(400, "内容不存在")
    sub = db.get(Subscription, record.subscription_id)
    if not sub or sub.user_id != current_user.id:
        return resp_400(400, "内容不存在")
    service = LLMTagService()
    ok = await service.tag_single(record, db)
    if ok:
        return resp_200(200, "打标成功")
    else:
        return resp_400(400, "打标失败，请检查 LLM 配置")


# ── 私有方法 ──


def _sub_to_dict(sub: Subscription) -> dict:
    """Subscription 转字典。"""
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "name": sub.name,
        "keywords": sub.keywords,
        "sources": sub.sources,
        "schedule_type": sub.schedule_type,
        "schedule_cron": sub.schedule_cron,
        "enabled": sub.enabled,
        "last_run_at": sub.last_run_at.isoformat() if sub.last_run_at else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }
