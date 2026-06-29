"""Insight 洞见管理路由。"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.models import InsightEntry

router = APIRouter(prefix="/Insight", tags=["Insight"])


# ── 请求模型 ──────────────────────────────────────────────


class AddInsightM(BaseModel):
    raw_text: str
    tags: list[str] = []
    source_type: str = "manual_text"


class ListInsightM(BaseModel):
    tag: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    page_num: int = 1
    page_size: int = 20


class GetInsightM(BaseModel):
    id: int


class FollowUpM(BaseModel):
    parent_id: int
    raw_text: str


class UpdateTagsM(BaseModel):
    id: int
    tags: list[str]


class LinkDigestM(BaseModel):
    id: int
    linked_digest_id: int


class DeleteInsightM(BaseModel):
    id: int


# ── 路由 ──────────────────────────────────────────────


@router.post("/add")
async def addInsight(
    pm: AddInsightM,
    db: SessionDep,
    current_user: CurrentUser,
    bt: BackgroundTasks,
):
    """提交文本洞见，触发异步 LLM 解读。"""
    insight = InsightEntry(
        user_id=current_user.id,
        raw_text=pm.raw_text,
        tags=pm.tags,
        source_type=pm.source_type,
        status="pending",
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # 触发异步解读
    asyncio.create_task(_interpret_insight(insight.id))
    return resp_200(200, "添加成功", _insight_to_dict(insight))


@router.post("/list")
async def listInsights(
    pm: ListInsightM,
    db: SessionDep,
    current_user: CurrentUser,
):
    """分页列表，支持 tag / 日期筛选。"""
    stmt = select(InsightEntry).where(
        InsightEntry.user_id == current_user.id,
        InsightEntry.deleted_at.is_(None),
    )
    if pm.tag:
        stmt = stmt.where(InsightEntry.tags.contains([pm.tag]))
    if pm.status:
        stmt = stmt.where(InsightEntry.status == pm.status)
    if pm.start_date:
        stmt = stmt.where(InsightEntry.created_at >= pm.start_date)
    if pm.end_date:
        stmt = stmt.where(InsightEntry.created_at <= pm.end_date)

    count_stmt = select(0)
    total = len(list(db.exec(count_stmt).all()))
    offset = (pm.page_num - 1) * pm.page_size
    stmt = (
        stmt.order_by(InsightEntry.created_at.desc())
        .offset(offset)
        .limit(pm.page_size)
    )
    insights = list(db.exec(stmt).all())
    return resp_200(
        200,
        "查询成功",
        {"total": total, "res": [_insight_to_dict(i) for i in insights]},
    )


@router.post("/get")
async def getInsight(
    pm: GetInsightM,
    db: SessionDep,
    current_user: CurrentUser,
):
    """单条详情，含追问历史树。"""
    insight = db.get(InsightEntry, pm.id)
    if not insight or insight.user_id != current_user.id:
        return resp_400(400, "洞见不存在")
    follow_ups = _get_follow_ups(pm.id, db)
    data = _insight_to_dict(insight)
    data["follow_ups"] = [_insight_to_dict(f) for f in follow_ups]
    return resp_200(200, "查询成功", data)


@router.post("/followUp")
async def followUp(
    pm: FollowUpM,
    db: SessionDep,
    current_user: CurrentUser,
    bt: BackgroundTasks,
):
    """追问。"""
    parent = db.get(InsightEntry, pm.parent_id)
    if not parent or parent.user_id != current_user.id:
        return resp_400(400, "父洞见不存在")

    child = InsightEntry(
        user_id=current_user.id,
        raw_text=pm.raw_text,
        parent_id=pm.parent_id,
        source_type="manual_text",
        status="pending",
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    asyncio.create_task(_interpret_insight(child.id))
    return resp_200(200, "追问成功", _insight_to_dict(child))


@router.post("/updateTags")
async def updateTags(
    pm: UpdateTagsM,
    db: SessionDep,
    current_user: CurrentUser,
):
    """手动更新标签。"""
    insight = db.get(InsightEntry, pm.id)
    if not insight or insight.user_id != current_user.id:
        return resp_400(400, "洞见不存在")
    insight.tags = pm.tags
    db.add(insight)
    db.commit()
    return resp_200(200, "更新成功", _insight_to_dict(insight))


@router.post("/delete")
async def deleteInsight(
    pm: DeleteInsightM,
    db: SessionDep,
    current_user: CurrentUser,
):
    """软删除。"""
    insight = db.get(InsightEntry, pm.id)
    if not insight or insight.user_id != current_user.id:
        return resp_400(400, "洞见不存在")
    insight.deleted_at = datetime.now(timezone.utc)
    db.add(insight)
    db.commit()
    return resp_200(200, "删除成功")


# ── 私有方法 ──────────────────────────────────────────────


async def _interpret_insight(insight_id: int) -> None:
    """异步 LLM 解读任务（内部调用）。"""
    from app.services.insight_service import InsightService

    await InsightService.interpret(insight_id)


def _insight_to_dict(i: InsightEntry) -> dict[str, Any]:
    return {
        "id": i.id,
        "user_id": i.user_id,
        "source_type": i.source_type,
        "raw_text": i.raw_text,
        "ai_interpretation": i.ai_interpretation,
        "tags": i.tags,
        "status": i.status,
        "error_message": i.error_message,
        "parent_id": i.parent_id,
        "linked_digest_id": i.linked_digest_id,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "updated_at": i.updated_at.isoformat() if i.updated_at else None,
    }


def _get_follow_ups(insight_id: int, db: Session) -> list[InsightEntry]:
    return list(
        db.exec(
            select(InsightEntry)
            .where(
                InsightEntry.parent_id == insight_id,
                InsightEntry.deleted_at.is_(None),
            )
            .order_by(InsightEntry.created_at.asc())
        ).all()
    )
