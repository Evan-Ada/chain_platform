"""LLM 配置管理路由。"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.models import LLMConfig
from app.services.llm_config_service import test_connectivity, update_last_test_result

router = APIRouter(prefix="/LLMConfig", tags=["LLMConfig"])


# ── 请求模型 ──


class AddLLMConfigM(BaseModel):
    name: str
    provider: str = "openai"
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    enabled: bool = True
    is_default: bool = False
    extra: dict[str, Any] = {}


class UpdateLLMConfigM(BaseModel):
    id: int
    name: str | None = None
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    extra: dict[str, Any] | None = None


class SetDefaultLLMConfigM(BaseModel):
    id: int


class TestLLMConfigM(BaseModel):
    id: int | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    provider: str | None = None


# ── 路由 ──


def _active_configs_stmt():
    """返回过滤 deleted_at IS NULL 的 LLMConfig select 语句。"""
    return select(LLMConfig).where(LLMConfig.deleted_at.is_(None))


@router.post("/add")
async def addLLMConfig(pm: AddLLMConfigM, db: SessionDep, current_user: CurrentUser):
    """新增 LLM 配置。

    若当前无任何有效默认配置，新配置自动 is_default=True。
    """
    # 检查是否存在有效默认配置
    has_active_default = db.exec(
        select(LLMConfig).where(
            LLMConfig.deleted_at.is_(None),
            LLMConfig.is_default == True,
            LLMConfig.enabled == True,
        )
    ).first()

    config = LLMConfig.model_validate(pm.model_dump())
    # 无有效默认时自动升为默认
    if not has_active_default:
        config.is_default = True
    elif config.is_default:
        _unset_all_defaults(db)

    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "添加成功", _to_masked_dict(config))


@router.post("/list")
async def listLLMConfigs(db: SessionDep, current_user: CurrentUser):
    """查询所有 LLM 配置（api_key 已脱敏，仅返回未删除）。"""
    configs = db.exec(_active_configs_stmt().order_by(LLMConfig.created_at.desc())).all()
    data = [_to_masked_dict(c) for c in configs]
    return resp_200(200, "查询成功", {"total": len(data), "res": data})


@router.post("/update")
async def updateLLMConfig(pm: UpdateLLMConfigM, db: SessionDep, current_user: CurrentUser):
    """更新 LLM 配置（仅限未删除配置）。"""
    config = db.get(LLMConfig, pm.id)
    if not config or config.deleted_at is not None:
        return resp_400(400, "配置不存在")
    update_data = pm.model_dump(exclude_unset=True, exclude={"id"})
    for k, v in update_data.items():
        setattr(config, k, v)
    if update_data.get("is_default"):
        _unset_all_defaults(db, exclude_id=config.id)
    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "更新成功", _to_masked_dict(config))


@router.post("/delete")
async def deleteLLMConfig(pm: SetDefaultLLMConfigM, db: SessionDep, current_user: CurrentUser):
    """删除 LLM 配置（软删除）。若被删的是默认，自动切换到最早的剩余有效配置。"""
    config = db.get(LLMConfig, pm.id)
    if not config or config.deleted_at is not None:
        return resp_400(400, "配置不存在")

    was_default = config.is_default
    # 软删除
    config.deleted_at = datetime.now(timezone.utc)
    config.is_default = False
    db.add(config)

    # 若被删的是默认，尝试切换
    if was_default:
        next_default = db.exec(
            select(LLMConfig).where(
                LLMConfig.deleted_at.is_(None),
                LLMConfig.enabled == True,
                LLMConfig.id != config.id,
            ).order_by(LLMConfig.created_at.asc())
        ).first()
        if next_default:
            next_default.is_default = True
            db.add(next_default)

    db.commit()
    return resp_200(200, "删除成功")


@router.post("/setDefault")
async def setDefaultLLMConfig(pm: SetDefaultLLMConfigM, db: SessionDep, current_user: CurrentUser):
    """设为默认 LLM 配置（目标配置必须未删除）。"""
    config = db.get(LLMConfig, pm.id)
    if not config or config.deleted_at is not None:
        return resp_400(400, "配置不存在")
    if not config.enabled:
        logger.warning(f"setDefault: 配置 {pm.id} enabled=False，仍设为默认")
    _unset_all_defaults(db, exclude_id=config.id)
    config.is_default = True
    db.add(config)
    db.commit()
    db.refresh(config)
    return resp_200(200, "设置成功", _to_masked_dict(config))


@router.post("/test")
async def testLLMConfig(pm: TestLLMConfigM, db: SessionDep, current_user: CurrentUser):
    """测试 LLM 配置连通性，走 llm_config_service 全 9 种 Provider 均支持。"""
    if pm.id:
        config = db.get(LLMConfig, pm.id)
        if not config or config.deleted_at is not None:
            return resp_400(400, "配置不存在")
    else:
        if not pm.api_key:
            return resp_400(400, "请提供 api_key 或配置 id")
        # 构造临时 config 用于测试（不使用 db）
        config = LLMConfig(
            name="temp",
            provider=pm.provider or "openai",
            api_key=pm.api_key,
            base_url=pm.base_url or "https://api.openai.com/v1",
            model=pm.model or "gpt-4o-mini",
            enabled=True,
            is_default=False,
            extra={},
        )

    try:
        reply, latency_ms = await test_connectivity(config)
        if pm.id:
            update_last_test_result(config, db, "success", reply)
        return resp_200(200, "连通性测试成功", {"reply": reply, "latency_ms": latency_ms})
    except Exception as e:
        err_msg = str(e)[:500]
        if pm.id:
            update_last_test_result(config, db, "failed", err_msg)
        return resp_400(400, f"连通性测试失败: {e}")


def _list_providers() -> list[dict[str, str]]:
    """返回已知 provider 列表。"""
    return [
        {"id": "openai", "name": "OpenAI"},
        {"id": "deepseek", "name": "DeepSeek"},
        {"id": "zhipu", "name": "智谱 GLM"},
        {"id": "moonshot", "name": "Moonshot (Kimi)"},
        {"id": "ollama", "name": "Ollama (本地)"},
        {"id": "azure", "name": "Azure OpenAI"},
        {"id": "anthropic", "name": "Anthropic Claude"},
        {"id": "gemini", "name": "Google Gemini"},
        {"id": "minimax", "name": "MiniMax"},
    ]


@router.post("/listProviders")
async def listProviders(db: SessionDep, current_user: CurrentUser):
    """返回支持的 LLM Provider 列表。"""
    return resp_200(200, "查询成功", _list_providers())


# ── 私有方法 ──


def _unset_all_defaults(db: SessionDep, exclude_id: int | None = None) -> None:
    """取消所有未删除配置的默认状态。"""
    stmt = _active_configs_stmt().where(LLMConfig.is_default == True)
    if exclude_id:
        stmt = stmt.where(LLMConfig.id != exclude_id)
    for config in db.exec(stmt).all():
        config.is_default = False
        db.add(config)


def _mask_api_key(api_key: str) -> str:
    """脱敏 api_key，只显示后四位。"""
    if not api_key or len(api_key) <= 4:
        return "****"
    return "****" + api_key[-4:]


def _to_masked_dict(config: LLMConfig) -> dict[str, Any]:
    """将 LLMConfig 转为脱敏字典（含 last_test_* 字段）。"""
    data = config.model_dump()
    data["masked_api_key"] = _mask_api_key(config.api_key)
    del data["api_key"]
    return data
