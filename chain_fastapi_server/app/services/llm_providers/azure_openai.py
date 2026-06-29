"""Azure OpenAI Provider。"""

import json
from typing import Any

from openai import AsyncAzureOpenAI

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


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI Provider。"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: AsyncAzureOpenAI | None = None

    def _get_client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            extra = self.config.extra or {}
            api_version = extra.get("api_version", "2024-01-01")
            azure_endpoint = extra.get("azure_endpoint", "")
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

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
