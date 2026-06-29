"""36氪 SSR 页面解析工具。"""

from __future__ import annotations

import json
import re
from typing import Any

from selectolax.parser import HTMLParser

_INITIAL_STATE_RE = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*(?:</script>|window\.)",
    re.DOTALL,
)


def normalize_kr36_url(url: str, base: str = "https://36kr.com") -> str:
    """补全相对链接。"""
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return f"{base.rstrip('/')}{url}"
    return f"{base.rstrip('/')}/{url}"


def _walk_state(obj: Any, found: list[dict[str, str]]) -> None:
    """递归扫描 __INITIAL_STATE__ 中的文章形字段。"""
    if isinstance(obj, dict):
        title = obj.get("title") or obj.get("widgetTitle") or obj.get("name")
        url = obj.get("url") or obj.get("itemUrl") or obj.get("route") or obj.get("link")
        summary = obj.get("summary") or obj.get("description") or obj.get("content") or ""
        if (
            isinstance(title, str)
            and title.strip()
            and isinstance(url, str)
            and url.strip()
            and len(title) >= 4
        ):
            found.append(
                {
                    "title": title.strip(),
                    "content": str(summary).strip() if summary else "",
                    "source_url": normalize_kr36_url(url.strip()),
                }
            )
        for value in obj.values():
            _walk_state(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _walk_state(item, found)


def parse_initial_state(html: str) -> list[dict[str, str]]:
    """从 HTML 中提取 window.__INITIAL_STATE__ 文章列表。"""
    match = _INITIAL_STATE_RE.search(html)
    if not match:
        # 兜底：找 script 内任意 __INITIAL_STATE__=
        alt = re.search(r"__INITIAL_STATE__\s*=\s*(\{.*\})\s*;", html, re.DOTALL)
        if not alt:
            return []
        raw = alt.group(1)
    else:
        raw = match.group(1)

    try:
        state = json.loads(raw)
    except json.JSONDecodeError:
        return []

    found: list[dict[str, str]] = []
    _walk_state(state, found)

    # 按 URL 去重，保留首次出现
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in found:
        url = item.get("source_url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(item)
    return unique


def parse_html_fallback(html: str, base: str = "https://36kr.com") -> list[dict[str, str]]:
    """CSS 兜底：解析列表页上的标题链接。"""
    tree = HTMLParser(html)
    found: list[dict[str, str]] = []
    seen: set[str] = set()

    for node in tree.css("a"):
        href = node.attributes.get("href", "")
        title = node.text(strip=True)
        if not href or not title or len(title) < 6:
            continue
        if "/p/" not in href and "/newsflashes/" not in href:
            continue
        url = normalize_kr36_url(href, base)
        if url in seen:
            continue
        seen.add(url)
        found.append({"title": title, "content": "", "source_url": url})

    return found


def parse_kr36_page(html: str) -> list[dict[str, str]]:
    """优先 INITIAL_STATE，失败则 CSS 兜底。"""
    items = parse_initial_state(html)
    if items:
        return items
    return parse_html_fallback(html)
