"""LLM Provider 注册表。"""

from app.models import LLMConfig

from .anthropic import AnthropicProvider
from .azure_openai import AzureOpenAIProvider
from .base import LLMProvider
from .gemini import GeminiProvider
from .minimax import MiniMaxProvider
from .openai_compat import OpenAICompatProvider

PROVIDERS = {
    "openai": OpenAICompatProvider,
    "deepseek": OpenAICompatProvider,
    "zhipu": OpenAICompatProvider,
    "moonshot": OpenAICompatProvider,
    "ollama": OpenAICompatProvider,
    "azure": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "minimax": MiniMaxProvider,
}


def get_provider(config: LLMConfig) -> LLMProvider:
    """根据 LLMConfig.provider 返回对应的 LLMProvider 实例。"""
    cls = PROVIDERS.get(config.provider, OpenAICompatProvider)
    return cls(config)
