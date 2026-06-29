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

    async def interpret(self, raw_text: str) -> dict[str, Any]:
        """解读洞见文本。"""
        import re

        system_prompt = """你是一个洞见解读助手。用户会输入一段文字（想法、灵感、反思等）。
请分析这段文字，输出一段结构化 JSON（不含 markdown 格式）：
{
  "core_viewpoint": "核心观点（一句话）",
  "emotional_tone": "情绪基调（如：平静、焦虑、乐观、反思等）",
  "motivation": "可能的动机或背景（1-2句话）",
  "actionable_suggestions": ["可执行的建议1", "可执行的建议2"],
  "related_insights": ["相关的历史洞见描述（无则留空数组）"],
  "tags": ["标签1", "标签2（如：tech, finance, life, career, health等）"],
  "reflection_questions": ["自我追问问题1", "自我追问问题2"]
}
请直接输出 JSON，不要添加任何解释。"""

        result_text = await self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if match:
            result_text = match.group()
        import json

        return json.loads(result_text)
