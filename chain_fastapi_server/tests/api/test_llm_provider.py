"""LLM Provider 测试（纯单元测试，不依赖真实 DB）。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models import LLMConfig


class TestOpenAICompatProvider:
    """测试 OpenAI 兼容 Provider。"""

    async def test_chat_success(self) -> None:
        """成功调用并返回内容。"""
        from app.services.llm_providers.openai_compat import OpenAICompatProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )
        provider = OpenAICompatProvider(config)

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="ok"))]

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            result = await provider.chat(
                messages=[{"role": "user", "content": "Say 'ok'"}],
                max_tokens=10,
            )
            assert result == "ok"

    async def test_chat_failure_retries(self) -> None:
        """调用失败后重试。"""
        from app.services.llm_providers.openai_compat import OpenAICompatProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )
        provider = OpenAICompatProvider(config)

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.return_value.chat.completions.create = AsyncMock(
                side_effect=Exception("rate limit")
            )
            with pytest.raises(Exception) as exc_info:
                await provider.chat(
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=10,
                )
            assert "rate limit" in str(exc_info.value)

    async def test_tag_returns_correct_format(self) -> None:
        """tag 方法返回正确 JSON 格式。"""
        from app.services.llm_providers.openai_compat import OpenAICompatProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )
        provider = OpenAICompatProvider(config)

        mock_response = AsyncMock()
        mock_response.choices = [
            AsyncMock(
                message=AsyncMock(
                    content='{"category":"tech","importance":"high","tags":["AI"],"sentiment":"neutral","one_sentence_summary":"AI news"}'
                )
            )
        ]

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            result = await provider.tag(title="AI News", content="AI update")
            assert result["category"] == "tech"
            assert result["importance"] == "high"
            assert "AI" in result["tags"]


class TestAnthropicProvider:
    """测试 Anthropic Provider。"""

    async def test_chat_success(self) -> None:
        """Anthropic HTTP 调用成功。"""
        from app.services.llm_providers.anthropic import AnthropicProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="anthropic",
            api_key="sk-ant-test",
            base_url="",
            model="claude-3-5-sonnet",
        )
        provider = AnthropicProvider(config)

        mock_response = AsyncMock()
        mock_response.json = lambda: {"content": [{"text": "hello"}]}
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await provider.chat(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            assert result == "hello"


class TestGeminiProvider:
    """测试 Gemini Provider。"""

    async def test_chat_success(self) -> None:
        """Gemini API 调用成功。"""
        from app.services.llm_providers.gemini import GeminiProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="gemini",
            api_key="gemini-test-key",
            base_url="",
            model="gemini-1.5-flash",
        )
        provider = GeminiProvider(config)

        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "candidates": [{"content": {"parts": [{"text": "gemini response"}]}}]
        }
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await provider.chat(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            assert result == "gemini response"


class TestMiniMaxProvider:
    """测试 MiniMax Provider。"""

    async def test_chat_success(self) -> None:
        """MiniMax API 调用成功。"""
        from app.services.llm_providers.minimax import MiniMaxProvider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="minimax",
            api_key="minimax-test-key",
            base_url="",
            model="abab6-chat",
        )
        provider = MiniMaxProvider(config)

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="minimax ok"))]

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            result = await provider.chat(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            assert result == "minimax ok"


class TestProviderRegistry:
    """测试 Provider 注册表。"""

    def test_get_provider_returns_correct_type(self) -> None:
        """Registry 根据 provider 字段返回正确类型。"""
        from app.services.llm_providers.openai_compat import OpenAICompatProvider
        from app.services.llm_providers.registry import get_provider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="deepseek",
            api_key="sk-test",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        )
        provider = get_provider(config)
        assert isinstance(provider, OpenAICompatProvider)

        config.provider = "azure"
        from app.services.llm_providers.azure_openai import AzureOpenAIProvider
        provider2 = get_provider(config)
        assert isinstance(provider2, AzureOpenAIProvider)

        config.provider = "anthropic"
        from app.services.llm_providers.anthropic import AnthropicProvider
        provider3 = get_provider(config)
        assert isinstance(provider3, AnthropicProvider)

        config.provider = "gemini"
        from app.services.llm_providers.gemini import GeminiProvider
        provider4 = get_provider(config)
        assert isinstance(provider4, GeminiProvider)

        config.provider = "minimax"
        from app.services.llm_providers.minimax import MiniMaxProvider
        provider5 = get_provider(config)
        assert isinstance(provider5, MiniMaxProvider)

    def test_unknown_provider_defaults_to_openai(self) -> None:
        """未知 provider 默认为 OpenAI 兼容。"""
        from app.services.llm_providers.openai_compat import OpenAICompatProvider
        from app.services.llm_providers.registry import get_provider

        config = LLMConfig(
            id=uuid.uuid4(),
            name="test",
            provider="unknown_provider",
            api_key="sk-test",
            base_url="https://unknown.com/v1",
            model="unknown-model",
        )
        provider = get_provider(config)
        assert isinstance(provider, OpenAICompatProvider)
