"""数据源配置管理路由。"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.models import DataSourceConfig

router = APIRouter(prefix="/DataSourceConfig", tags=["DataSourceConfig"])


# ── 请求模型 ──


class AddDataSourceConfigM(BaseModel):
    name: str
    source_type: str
    enabled: bool = True
    config: dict[str, Any] = {}


class UpdateDataSourceConfigM(BaseModel):
    id: int
    name: str | None = None
    source_type: str | None = None
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class ToggleDataSourceConfigM(BaseModel):
    id: int
    enabled: bool


# ── 路由 ──


@router.post("/add")
async def addDataSourceConfig(pm: AddDataSourceConfigM, db: SessionDep, current_user: CurrentUser):
    """新增数据源配置。"""
    config = DataSourceConfig.model_validate(pm.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "添加成功", _to_dict(config))


@router.post("/list")
async def listDataSourceConfigs(db: SessionDep, current_user: CurrentUser):
    """查询所有数据源配置。"""
    configs = list(db.exec(select(DataSourceConfig).order_by(DataSourceConfig.created_at.desc())).all())
    data = [_to_dict(c) for c in configs]
    return resp_200(200, "查询成功", {"total": len(data), "res": data})


@router.post("/update")
async def updateDataSourceConfig(pm: UpdateDataSourceConfigM, db: SessionDep, current_user: CurrentUser):
    """更新数据源配置。"""
    config = db.get(DataSourceConfig, pm.id)
    if not config:
        return resp_400(400, "配置不存在")
    update_data = pm.model_dump(exclude_unset=True, exclude={"id"})
    for k, v in update_data.items():
        setattr(config, k, v)
    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "更新成功", _to_dict(config))


@router.post("/delete")
async def deleteDataSourceConfig(pm: UpdateDataSourceConfigM, db: SessionDep, current_user: CurrentUser):
    """删除数据源配置。"""
    config = db.get(DataSourceConfig, pm.id)
    if not config:
        return resp_400(400, "配置不存在")
    db.delete(config)
    db.commit()
    return resp_200(200, "删除成功")


@router.post("/toggle")
async def toggleDataSourceConfig(pm: ToggleDataSourceConfigM, db: SessionDep, current_user: CurrentUser):
    """启用/禁用数据源配置。"""
    config = db.get(DataSourceConfig, pm.id)
    if not config:
        return resp_400(400, "配置不存在")
    config.enabled = pm.enabled
    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "操作成功", _to_dict(config))


# ── 私有方法 ──


def _to_dict(config: DataSourceConfig) -> dict[str, Any]:
    """DataSourceConfig 转字典。"""
    return {
        "id": config.id,
        "name": config.name,
        "source_type": config.source_type,
        "enabled": config.enabled,
        "config": config.config,
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }
