"""LLM 标签服务。

使用 LLM 对抓取到的内容进行分类打标。
"""

import asyncio

from loguru import logger
from sqlmodel import Session, select

from app.models import ContentRecord, LLMConfig

from app.services.llm_providers.registry import get_provider
from app.services.tag_service import TagService


def _get_default_llm_config(db: Session) -> LLMConfig | None:
    """获取默认 LLM 配置（仅限未删除）。"""
    return db.exec(
        select(LLMConfig).where(
            LLMConfig.deleted_at.is_(None),
            LLMConfig.is_default == True,
            LLMConfig.enabled == True,
        )
    ).first()


class LLMTagService:
    """LLM 标签服务。"""

    def __init__(self, llm_config: LLMConfig | None = None):
        self._config = llm_config

    def _get_provider(self, db: Session):
        """获取 LLM Provider 实例。"""
        config = self._config or _get_default_llm_config(db)
        if not config:
            return None
        return get_provider(config)

    async def tag_single(self, record: ContentRecord, db: Session) -> bool:
        """对单条内容进行 LLM 打标。返回是否成功。"""
        provider = self._get_provider(db)
        if not provider:
            logger.warning("没有可用的 LLM 配置，跳过打标")
            return False

        # 更新状态为处理中
        record.llm_status = "processing"
        db.add(record)
        db.commit()

        try:
            tags = await provider.tag(
                title=record.title or "",
                content=record.content or "",
            )

            # 归一化标签
            tags = TagService.normalize(tags)

            record.llm_tags = tags
            record.llm_status = "done"
            record.llm_error = None
            db.add(record)
            db.commit()
            logger.info(f"打标成功 record_id={record.id}")
            return True
        except Exception as e:
            record.llm_status = "failed"
            record.llm_error = str(e)[:1000]
            db.add(record)
            db.commit()
            logger.error(f"打标失败 record_id={record.id}, error={e}")
            return False

    async def batch_tag_pending(self, db: Session, batch_size: int = 10) -> dict[str, int]:
        """批量处理 pending 状态的内容记录。返回统计信息。"""
        provider = self._get_provider(db)
        if not provider:
            logger.warning("没有可用的 LLM 配置，跳过批量打标")
            return {"total": 0, "success": 0, "failed": 0}

        stmt = (
            select(ContentRecord)
            .where(ContentRecord.llm_status == "pending")
            .limit(batch_size)
        )
        records = list(db.exec(stmt).all())

        success = 0
        failed = 0
        for record in records:
            ok = await _tag_with_retry(record, db, provider)
            if ok:
                success += 1
            else:
                failed += 1

        logger.info(f"批量打标完成: 总计 {len(records)}, 成功 {success}, 失败 {failed}")
        return {"total": len(records), "success": success, "failed": failed}


async def _tag_with_retry(record: ContentRecord, db: Session, provider) -> bool:
    """带指数退避的重试逻辑。"""
    wait_times = [1, 3]
    for attempt in range(len(wait_times) + 1):
        record.llm_status = "processing"
        db.add(record)
        db.commit()

        try:
            tags = await provider.tag(
                title=record.title or "",
                content=record.content or "",
            )
            tags = TagService.normalize(tags)
            record.llm_tags = tags
            record.llm_status = "done"
            record.llm_error = None
            db.add(record)
            db.commit()
            logger.info(f"打标成功 record_id={record.id}")
            return True
        except Exception as e:
            record.llm_status = "failed"
            record.llm_error = str(e)[:1000]
            db.add(record)
            db.commit()
            logger.warning(f"打标失败 record_id={record.id}, attempt={attempt + 1}, error={e}")
            if attempt < len(wait_times):
                await asyncio.sleep(wait_times[attempt])

    return False
