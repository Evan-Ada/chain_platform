"""36kr SSR 解析与适配器单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.content_fetch import Kr36SsrAdapter, _match_keywords
from app.services.kr36_parser import parse_html_fallback, parse_initial_state, parse_kr36_page


SAMPLE_INITIAL_STATE_HTML = """
<html><body><script>
window.__INITIAL_STATE__ = {
  "information": {
    "itemList": [
      {"title": "OpenAI 发布新模型，人工智能再升温", "url": "/p/123456", "summary": "AI 赛道"},
      {"title": "无关新闻标题", "url": "/p/999", "summary": "普通内容"}
    ]
  }
};
</script></body></html>
"""

SAMPLE_LINK_HTML = """
<html><body>
  <a href="/p/888888">半导体产业链最新动态分析报道</a>
</body></html>
"""


class TestKr36Parser:
    def test_parse_initial_state(self) -> None:
        items = parse_initial_state(SAMPLE_INITIAL_STATE_HTML)
        assert len(items) >= 1
        assert any("人工智能" in i["title"] for i in items)
        assert items[0]["source_url"].startswith("https://36kr.com")

    def test_parse_html_fallback(self) -> None:
        items = parse_html_fallback(SAMPLE_LINK_HTML)
        assert len(items) == 1
        assert "半导体" in items[0]["title"]

    def test_parse_kr36_page_prefers_state(self) -> None:
        items = parse_kr36_page(SAMPLE_INITIAL_STATE_HTML)
        assert any("人工智能" in i["title"] for i in items)


class TestKr36SsrAdapter:
    @pytest.mark.asyncio
    async def test_fetch_matches_tag_keywords(self) -> None:
        adapter = Kr36SsrAdapter()
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INITIAL_STATE_HTML
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.content_fetch.httpx.AsyncClient", return_value=mock_client):
            results = await adapter.fetch(
                [],
                ds_config={
                    "list_urls": ["https://36kr.com/information/web_news/latest"],
                    "max_items_per_url": 10,
                    "tag_categories": ["topic"],
                },
                db=None,
            )

        # db=None 时用空 keywords，不过滤
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_fetch_filters_by_keywords(self) -> None:
        adapter = Kr36SsrAdapter()
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INITIAL_STATE_HTML
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.content_fetch.httpx.AsyncClient", return_value=mock_client):
            results = await adapter.fetch(
                ["人工智能"],
                ds_config={"list_urls": ["https://36kr.com/test"]},
            )

        assert len(results) == 1
        assert "人工智能" in results[0]["keywords_matched"]


class TestMatchKeywords:
    def test_match_chinese(self) -> None:
        matched = _match_keywords("半导体供应链紧张", ["半导体", "人工智能"])
        assert "半导体" in matched
        assert "人工智能" not in matched
