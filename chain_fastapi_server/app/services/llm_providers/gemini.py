"""Google Gemini Provider。"""

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


class GeminiProvider(LLMProvider):
    """Google Gemini Provider（generativelanguage.googleapis.com）。"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._api_key = config.api_key

    def _get_base_url(self) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.config.model}:generateContent"
        )

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
                prompt_text = "\n".join(
                    f"{m['role']}: {m['content']}" for m in messages
                )
                async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT) as client:
                    response = await client.post(
                        self._get_base_url(),
                        params={"key": self._api_key},
                        json={
                            "contents": [{"parts": [{"text": prompt_text}]}],
                            "generationConfig": {
                                "temperature": temperature,
                                "maxOutputTokens": max_tokens,
                            },
                        },
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                last_error = e
                if attempt < retry_times:
                    await self._backoff(attempt)

        raise last_error or RuntimeError("Gemini chat failed")

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
