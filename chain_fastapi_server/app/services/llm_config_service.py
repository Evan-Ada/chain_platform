"""LLM 配置服务。

提供 LLM 配置的连通性测试等业务逻辑。
"""

import time
from datetime import datetime, timezone

from loguru import logger

from app.models import LLMConfig


async def test_connectivity(config: LLMConfig) -> tuple[str, int]:
    """测试 LLM 配置连通性。

    调用 `get_provider(config).chat()` 并测量延迟。

    Args:
        config: LLMConfig 实例

    Returns:
        (reply_text, latency_ms)

    Raises:
        Exception: 连通测试失败时抛出异常
    """
    from app.services.llm_providers.registry import get_provider

    provider = get_provider(config)
    start = time.monotonic()
    reply = await provider.chat(
        messages=[{"role": "user", "content": "Say 'ok'"}],
        temperature=0,
        max_tokens=10,
    )
    latency_ms = int((time.monotonic() - start) * 1000)
    return reply.strip(), latency_ms


def update_last_test_result(
    config: LLMConfig,
    db,
    status: str,
    message: str,
) -> None:
    """更新配置的最近一次测试结果。

    Args:
        config: LLMConfig 实例
        db: 数据库 session
        status: "success" | "failed"
        message: 回复文本或错误信息（最多截取 500 字符）
    """
    config.last_test_at = datetime.now(timezone.utc)
    config.last_test_status = status
    config.last_test_message = message[:500] if message else None
    db.add(config)
    db.commit()
