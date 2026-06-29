"""Anthropic Claude Provider。"""

import json
from typing import Any

import httpx

from app.core.config import settings
from app.models import LLMConfig

from .base import LLMProvider

TAG_PROMPT = """你是一个内容分类专家。请对以下文章进行分类打标。

文章标题：{title}
文章摘要：{content}

请返回 JSON 格式，包含以下字段：
- category: 内容分类（如：科技、财经、社会、娱乐、体育、国际、其他）
- importance: 重要程度（high / medium / low）
- tags: 关键词列表（最多 5 个）
- sentiment: 情感倾向（positive / neutral / negative）
- one_sentence_summary: 一句话总结

只返回 JSON，不要其他文字。"""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Provider（通过 HTTP 调用 Messages API）。"""

    BASE_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, config: LLMConfig):
        self.config = config

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        retry_times = settings.LLM_RETRY_TIMES
        last_error: Exception | None = None

        for attempt in range(retry_times + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT) as client:
                    body = {
                        "messages": messages,
                        "model": self.config.model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    response = await client.post(
                        self.BASE_URL,
                        json=body,
                        headers={
                            "x-api-key": self.config.api_key,
                            "anthropic-version": self.ANTHROPIC_VERSION,
                            "Content-Type": "application/json",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["content"][0]["text"]
            except Exception as e:
                last_error = e
                if attempt < retry_times:
                    await self._backoff(attempt)

        raise last_error or RuntimeError("Anthropic chat failed")

    async def tag(self, title: str, content: str) -> dict[str, Any]:
        prompt = TAG_PROMPT.format(title=title, content=content)
        result_text = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        text = result_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        return json.loads(text)

    @staticmethod
    async def _backoff(attempt: int) -> None:
        import asyncio

        wait_times = [1, 3]
        await asyncio.sleep(wait_times[attempt] if attempt < len(wait_times) else 3)
