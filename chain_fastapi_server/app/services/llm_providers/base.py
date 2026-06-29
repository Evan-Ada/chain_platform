"""LLM Provider 抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """LLM Provider 抽象基类。"""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """发起 chat 对话，返回回复文本。"""
        raise NotImplementedError

    @abstractmethod
    async def tag(self, title: str, content: str) -> dict[str, Any]:
        """对文章进行标签分类。"""
        raise NotImplementedError
