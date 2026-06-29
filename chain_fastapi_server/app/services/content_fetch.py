"""内容抓取服务。

提供三种适配器：RSS、热点新闻 API、RSSHub，统一由 ContentFetchService 调度。
三数据源并发抓取（asyncio.gather），入库去重统一处理。
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from loguru import logger
from sqlmodel import Session, select

from app.models import ContentRecord, DataSourceConfig, Subscription


def _url_hash(url: str) -> str:
    """计算 URL 的 SHA256 哈希，用于去重。"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    """检查文本中包含哪些关键词。"""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


# === 数据源适配器 ===


class SourceAdapter:
    """数据源适配器基类。"""
    name: str = ""

    async def fetch(self, keywords: list[str]) -> list[dict[str, Any]]:
        raise NotImplementedError


class RssAdapter(SourceAdapter):
    """标准 RSS/Atom 源抓取。"""
    name = "rss"

    RSS_MAP = {
        "weibo": "https://rsshub.app/weibo/hot",
        "zhihu": "https://rsshub.app/zhihu/hot",
        "36kr": "https://rsshub.app/36kr/news",
    }

    async def fetch(self, keywords: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for platform, url in self.RSS_MAP.items():
                try:
                    resp = await client.get(url)
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:20]:
                        title = entry.get("title", "")
                        content = entry.get("summary", entry.get("description", ""))
                        matched = _match_keywords(f"{title} {content}", keywords)
                        if keywords and not matched:
                            continue
                        results.append({
                            "title": title,
                            "content": content,
                            "source_url": entry.get("link", ""),
                            "source_name": platform,
                            "keywords_matched": matched,
                        })
                except Exception as e:
                    logger.warning(f"RSS 源 {platform} 抓取失败: {e}")
        return results


class HotNewsAdapter(SourceAdapter):
    """热点新闻 API 适配器。"""
    name = "api"

    async def fetch(self, keywords: list[str], ds_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not ds_config or not ds_config.get("endpoint"):
            return []
        results: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if ds_config.get("api_key"):
                    headers["Authorization"] = f"Bearer {ds_config['api_key']}"
                resp = await client.get(ds_config["endpoint"], headers=headers)
                data = resp.json()
                raw_list = data.get("data", data) if isinstance(data, dict) else data
                if not isinstance(raw_list, list):
                    raw_list = []
                for item in raw_list:
                    title = item.get("title", "")
                    content = item.get("desc", item.get("summary", ""))
                    matched = _match_keywords(f"{title} {content}", keywords)
                    if keywords and not matched:
                        continue
                    results.append({
                        "title": title,
                        "content": content,
                        "source_url": item.get("url", item.get("link", "")),
                        "source_name": item.get("source", "热点API"),
                        "keywords_matched": matched,
                    })
        except Exception as e:
            logger.warning(f"热点 API 抓取失败: {e}")
        return results


class RssHubAdapter(SourceAdapter):
    """RSSHub 自定义实例适配器。"""
    name = "rsshub"

    async def fetch(self, keywords: list[str], rsshub_url: str = "") -> list[dict[str, Any]]:
        if not rsshub_url:
            return []
        results: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(rsshub_url)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:20]:
                    title = entry.get("title", "")
                    content = entry.get("summary", entry.get("description", ""))
                    matched = _match_keywords(f"{title} {content}", keywords)
                    if keywords and not matched:
                        continue
                    results.append({
                        "title": title,
                        "content": content,
                        "source_url": entry.get("link", ""),
                        "source_name": "RSSHub",
                        "keywords_matched": matched,
                    })
        except Exception as e:
            logger.warning(f"RSSHub 抓取失败: {e}")
        return results


class Kr36SsrAdapter(SourceAdapter):
    """36氪 SSR 列表页抓取（多 URL + Tag 词典匹配）。"""
    name = "ssr"

    async def fetch(
        self,
        keywords: list[str],
        *,
        db: Session | None = None,
        ds_config: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from app.services.kr36_parser import parse_kr36_page
        from app.services.tag_service import TagService

        config = ds_config or {}
        list_urls: list[str] = config.get("list_urls") or [config.get("list_url", "")]
        list_urls = [u for u in list_urls if u]
        if not list_urls:
            return []

        search_terms = list(keywords)
        if db is not None:
            categories = config.get("tag_categories")
            search_terms = TagService.get_search_terms(db, categories=categories)
        if not search_terms:
            search_terms = keywords

        max_items = int(config.get("max_items_per_url", 20))
        timeout = float(config.get("timeout_seconds", 25))
        retry_times = int(config.get("retry_times", 2))
        headers = {
            "User-Agent": config.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

        results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for list_url in list_urls:
                html = ""
                for attempt in range(retry_times + 1):
                    try:
                        resp = await client.get(list_url, headers=headers)
                        resp.raise_for_status()
                        html = resp.text
                        break
                    except Exception as e:
                        if attempt >= retry_times:
                            logger.warning(f"36kr SSR 抓取失败 {list_url}: {e}")
                        else:
                            await asyncio.sleep(1)

                if not html:
                    continue

                items = parse_kr36_page(html)[:max_items]
                for item in items:
                    source_url = item.get("source_url", "")
                    if not source_url or source_url in seen_urls:
                        continue
                    title = item.get("title", "")
                    content = item.get("content", "")
                    matched = _match_keywords(f"{title} {content}", search_terms)
                    if search_terms and not matched:
                        continue
                    seen_urls.add(source_url)
                    results.append({
                        "title": title,
                        "content": content,
                        "source_url": source_url,
                        "source_name": "36kr",
                        "keywords_matched": matched,
                    })

        logger.info(f"36kr SSR 匹配 {len(results)} 条（词表 {len(search_terms)} 个）")
        return results


# 适配器映射
_ADAPTERS: dict[str, type[SourceAdapter]] = {
    "rss": RssAdapter,
    "api": HotNewsAdapter,
    "rsshub": RssHubAdapter,
    "ssr": Kr36SsrAdapter,
}


class ContentFetchService:
    """内容抓取与入库服务。"""

    def _load_source_config(self, db: Session, source_type: str) -> dict[str, Any]:
        """从 DataSourceConfig 表加载配置。"""
        config = db.exec(
            select(DataSourceConfig).where(
                DataSourceConfig.source_type == source_type,
                DataSourceConfig.enabled == True,
            )
        ).first()
        return config.config if config else {}

    async def fetch_and_save(self, subscription: Subscription, db: Session) -> int:
        """并行抓取所有数据源，统一去重入库，返回新增条数。"""
        # 并发启动所有适配器的 fetch 任务
        tasks = []
        for source in subscription.sources:
            adapter_cls = _ADAPTERS.get(source)
            if not adapter_cls:
                continue
            adapter = adapter_cls()
            if source == "api":
                extra = self._load_source_config(db, "api")
                tasks.append(adapter.fetch(subscription.keywords, extra))
            elif source == "rsshub":
                extra = self._load_source_config(db, "rsshub")
                rsshub_url = extra.get("rsshub_url", "")
                tasks.append(adapter.fetch(subscription.keywords, rsshub_url))
            elif source == "ssr":
                extra = self._load_source_config(db, "ssr")
                tasks.append(adapter.fetch(subscription.keywords, db=db, ds_config=extra))
            else:
                tasks.append(adapter.fetch(subscription.keywords))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并所有结果
        all_items: list[dict[str, Any]] = []
        for result in results_list:
            if isinstance(result, Exception):
                logger.error(f"适配器异常: {result}")
                continue
            all_items.extend(result)

        # 统一去重入库
        new_count = 0
        new_record_ids: list[int] = []
        for item in all_items:
            source_url = item.get("source_url", "")
            if not source_url:
                continue
            url_hash = _url_hash(source_url)
            existing = db.exec(
                select(ContentRecord).where(ContentRecord.url_hash == url_hash)
            ).first()
            if existing:
                continue

            record = ContentRecord(
                subscription_id=subscription.id,
                title=item.get("title", "")[:500],
                content=item.get("content"),
                source_url=source_url,
                source_name=item.get("source_name", ""),
                url_hash=url_hash,
                keywords_matched=item.get("keywords_matched", []),
                llm_status="pending",
            )
            db.add(record)
            db.flush()
            if record.id is not None:
                new_record_ids.append(record.id)
            new_count += 1

        if new_count > 0:
            db.commit()

        # 更新订阅最后执行时间
        subscription.last_run_at = datetime.now(timezone.utc)
        db.add(subscription)
        db.commit()

        if new_record_ids:
            from app.services.push_service import PushService

            await PushService.push_immediate_for_records(
                subscription.user_id,
                subscription.id,
                new_record_ids,
                db=db,
            )

        logger.info(f"抓取完成 subscription_id={subscription.id}, 新增 {new_count} 条")
        return new_count

    async def fetch_multiple(self, subscriptions: list[Subscription], db: Session) -> dict[str, int]:
        """并行抓取多个订阅。"""
        tasks = [self.fetch_and_save(sub, db) for sub in subscriptions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        summary: dict[str, int] = {}
        for sub, result in zip(subscriptions, results):
            if isinstance(result, Exception):
                logger.error(f"抓取异常 subscription_id={sub.id}, error={result}")
                summary[str(sub.id)] = 0
            else:
                summary[str(sub.id)] = result
        return summary
