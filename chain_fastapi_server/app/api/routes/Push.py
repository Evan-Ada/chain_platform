"""Push 推送管理路由。"""

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.models import PushMessage, PushPreference

router = APIRouter(prefix="/Push", tags=["Push"])


# ── 请求模型 ──


class UpdatePreferenceM(BaseModel):
    channels: dict[str, bool] | None = None
    push_time: str | None = None
    timezone: str | None = None
    daily_digest: bool | None = None
    importance_filter: list[str] | None = None


class ListMessagesM(BaseModel):
    push_date: str | None = None
    importance: str | None = None
    is_read: bool | None = None
    page_num: int = 1
    page_size: int = 20


class MarkAsReadM(BaseModel):
    id_list: list[int]


class ResendM(BaseModel):
    id: int


# ── 路由 ──


@router.post("/getPreference")
async def getPreference(db: SessionDep, current_user: CurrentUser):
    """获取当前用户的推送偏好。"""
    pref = db.get(PushPreference, current_user.id)
    if not pref:
        # 返回默认值
        default_pref = {
            "id": current_user.id,
            "channels": {"email": True, "app": True},
            "push_time": "08:00:00",
            "timezone": "Asia/Shanghai",
            "daily_digest": True,
            "importance_filter": ["high", "medium"],
            "created_at": None,
            "updated_at": None,
        }
        return resp_200(200, "查询成功", default_pref)
    return resp_200(200, "查询成功", _pref_to_dict(pref))


@router.post("/updatePreference")
async def updatePreference(pm: UpdatePreferenceM, db: SessionDep, current_user: CurrentUser):
    """更新推送偏好（upsert）。"""
    pref = db.get(PushPreference, current_user.id)
    if not pref:
        pref = PushPreference(id=current_user.id)
        db.add(pref)

    update_data = pm.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(pref, k, v)

    db.add(pref)
    db.commit()
    db.refresh(pref)
    return resp_200(200, "更新成功", _pref_to_dict(pref))


@router.post("/listMessages")
async def listMessages(pm: ListMessagesM, db: SessionDep, current_user: CurrentUser):
    """分页查询推送消息列表。"""
    stmt = select(PushMessage).where(PushMessage.user_id == current_user.id)
    count_stmt = select(PushMessage).where(PushMessage.user_id == current_user.id)

    if pm.push_date:
        try:
            pd = date.fromisoformat(pm.push_date)
            stmt = stmt.where(PushMessage.push_date == pd)
            count_stmt = count_stmt.where(PushMessage.push_date == pd)
        except ValueError:
            pass

    if pm.importance:
        stmt = stmt.where(PushMessage.importance == pm.importance)
        count_stmt = count_stmt.where(PushMessage.importance == pm.importance)

    if pm.is_read is not None:
        if pm.is_read:
            stmt = stmt.where(PushMessage.status == "read")
            count_stmt = count_stmt.where(PushMessage.status == "read")
        else:
            stmt = stmt.where(PushMessage.status != "read")
            count_stmt = count_stmt.where(PushMessage.status != "read")

    total = len(list(db.exec(count_stmt).all()))
    offset = (pm.page_num - 1) * pm.page_size
    stmt = stmt.order_by(PushMessage.created_at.desc()).offset(offset).limit(pm.page_size)
    msgs = list(db.exec(stmt).all())

    data = [_msg_to_dict(m) for m in msgs]
    return resp_200(200, "查询成功", {"total": total, "res": data})


@router.post("/markAsRead")
async def markAsRead(pm: MarkAsReadM, db: SessionDep, current_user: CurrentUser):
    """批量标记消息为已读。"""
    count = 0
    for mid in pm.id_list:
        msg = db.get(PushMessage, mid)
        if msg and msg.user_id == current_user.id:
            msg.status = "read"
            from datetime import datetime, timezone

            msg.read_at = datetime.now(timezone.utc)
            db.add(msg)
            count += 1
    db.commit()
    return resp_200(200, f"已标记 {count} 条消息为已读")


@router.post("/unreadCount")
async def unreadCount(db: SessionDep, current_user: CurrentUser):
    """返回未读消息数量。"""
    count = len(
        db.exec(
            select(PushMessage).where(
                PushMessage.user_id == current_user.id,
                PushMessage.status != "read",
            )
        ).all()
    )
    return resp_200(200, "查询成功", {"unread_count": count})


@router.post("/resend")
async def resend(pm: ResendM, db: SessionDep, current_user: CurrentUser):
    """重发邮件消息。"""
    from app.services.push_service import PushService

    msg = db.get(PushMessage, pm.id)
    if not msg or msg.user_id != current_user.id:
        return resp_400(400, "消息不存在")

    if msg.channel != "email":
        return resp_400(400, "仅支持重发邮件消息")

    msg.status = "pending"
    db.add(msg)
    db.commit()

    ok = PushService.send_email(current_user.id, [msg.id])
    if ok:
        msg.status = "sent"
    else:
        msg.status = "failed"
    db.add(msg)
    db.commit()

    return resp_200(200, "重发成功" if ok else "重发失败")


# ── 私有方法 ──


def _pref_to_dict(pref: PushPreference) -> dict:
    return {
        "id": pref.id,
        "channels": pref.channels,
        "push_time": pref.push_time,
        "timezone": pref.timezone,
        "daily_digest": pref.daily_digest,
        "importance_filter": pref.importance_filter,
        "created_at": pref.created_at.isoformat() if pref.created_at else None,
        "updated_at": pref.updated_at.isoformat() if pref.updated_at else None,
    }


def _msg_to_dict(msg: PushMessage) -> dict:
    return {
        "id": msg.id,
        "user_id": msg.user_id,
        "subscription_id": msg.subscription_id if msg.subscription_id else None,
        "content_record_id": msg.content_record_id if msg.content_record_id else None,
        "title": msg.title,
        "summary": msg.summary,
        "tags": msg.tags,
        "importance": msg.importance,
        "channel": msg.channel,
        "status": msg.status,
        "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
        "push_date": msg.push_date.isoformat() if msg.push_date else None,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
