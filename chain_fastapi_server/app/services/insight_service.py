"""InsightService：洞见异步 LLM 解读服务。"""

import asyncio

from loguru import logger
from sqlmodel import Session, select

from app.core.db import engine
from app.models import InsightEntry, LLMConfig
from app.services.llm_providers.registry import get_provider
from app.services.tag_service import TagService


def _get_default_llm_config() -> LLMConfig | None:
    with Session(engine) as db:
        return db.exec(
            select(LLMConfig).where(
                LLMConfig.deleted_at.is_(None),
                LLMConfig.is_default == True,
                LLMConfig.enabled == True,
            )
        ).first()


class InsightService:
    @staticmethod
    async def interpret(insight_id: int) -> bool:
        """异步 LLM 解读任务。"""
        with Session(engine) as db:
            insight = db.get(InsightEntry, insight_id)
            if not insight:
                logger.warning(f"洞见 {insight_id} 不存在")
                return False

            llm_config = _get_default_llm_config()
            if not llm_config:
                logger.warning("没有可用的 LLM 配置")
                insight.status = "failed"
                insight.error_message = "没有可用的 LLM 配置"
                db.add(insight)
                db.commit()
                return False

            insight.status = "processing"
            db.add(insight)
            db.commit()

            try:
                provider = get_provider(llm_config)
                result = await provider.interpret(raw_text=insight.raw_text)

                # 复用 TagService.normalize() 归一化标签
                normalized = TagService.normalize(result)
                tags = normalized.get("tags", [])

                insight.ai_interpretation = result
                insight.tags = tags
                insight.status = "done"
                insight.error_message = None
                db.add(insight)
                db.commit()
                logger.info(f"洞见解读成功 insight_id={insight_id}")
                return True
            except Exception as e:
                insight.status = "failed"
                insight.error_message = str(e)[:500]
                db.add(insight)
                db.commit()
                logger.error(f"洞见解读失败 insight_id={insight_id}, error={e}")
                return False

    @staticmethod
    async def interpret_pending(batch_size: int = 5) -> dict[str, int]:
        """批量处理 pending 洞见。"""
        with Session(engine) as db:
            pending = list(
                db.exec(
                    select(InsightEntry)
                    .where(
                        InsightEntry.status == "pending",
                        InsightEntry.deleted_at.is_(None),
                    )
                    .limit(batch_size)
                ).all()
            )

        success = 0
        failed = 0
        for insight in pending:
            ok = await InsightService.interpret(insight.id)
            if ok:
                success += 1
            else:
                failed += 1

        logger.info(
            f"批量解读完成: 总计 {len(pending)}, 成功 {success}, 失败 {failed}"
        )
        return {"total": len(pending), "success": success, "failed": failed}
