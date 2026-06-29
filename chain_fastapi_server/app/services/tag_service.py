"""TagService：标签字典 + 语义合并服务。"""

import difflib
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from app.core.db import engine
from app.models import Tag, TagSynonym

# ── 种子词典 ──────────────────────────────────────────────

SEED_TAGS = [
    # 科技
    {"name": "tech", "display_name": "科技", "category": "topic"},
    {"name": "ai", "display_name": "人工智能", "category": "topic"},
    {"name": "semiconductor", "display_name": "半导体", "category": "industry"},
    {"name": "internet", "display_name": "互联网", "category": "industry"},
    {"name": "mobile", "display_name": "移动端", "category": "topic"},
    {"name": "software", "display_name": "软件", "category": "topic"},
    {"name": "hardware", "display_name": "硬件", "category": "topic"},
    {"name": "cyber_security", "display_name": "网络安全", "category": "topic"},
    {"name": "blockchain", "display_name": "区块链", "category": "topic"},
    # 财经
    {"name": "finance", "display_name": "财经", "category": "topic"},
    {"name": "stock", "display_name": "股票", "category": "industry"},
    {"name": "fund", "display_name": "基金", "category": "industry"},
    {"name": "bond", "display_name": "债券", "category": "industry"},
    {"name": "forex", "display_name": "外汇", "category": "industry"},
    {"name": "crypto", "display_name": "加密货币", "category": "industry"},
    {"name": "economy", "display_name": "宏观经济", "category": "topic"},
    {"name": "banking", "display_name": "银行", "category": "industry"},
    {"name": "insurance", "display_name": "保险", "category": "industry"},
    # 社会
    {"name": "society", "display_name": "社会", "category": "topic"},
    {"name": "politics", "display_name": "政治", "category": "topic"},
    {"name": "law", "display_name": "法律", "category": "topic"},
    {"name": "education", "display_name": "教育", "category": "topic"},
    {"name": "healthcare", "display_name": "医疗健康", "category": "topic"},
    {"name": "environment", "display_name": "环境", "category": "topic"},
    # 娱乐
    {"name": "entertainment", "display_name": "娱乐", "category": "topic"},
    {"name": "celebrity", "display_name": "明星", "category": "topic"},
    {"name": "movie", "display_name": "电影", "category": "industry"},
    {"name": "gaming", "display_name": "游戏", "category": "industry"},
    {"name": "sports", "display_name": "体育", "category": "topic"},
    {"name": "football", "display_name": "足球", "category": "topic"},
    {"name": "basketball", "display_name": "篮球", "category": "topic"},
    # 国际
    {"name": "world", "display_name": "国际", "category": "topic"},
    {"name": "us", "display_name": "美国", "category": "topic"},
    {"name": "china", "display_name": "中国", "category": "topic"},
    {"name": "europe", "display_name": "欧洲", "category": "topic"},
    {"name": "asia", "display_name": "亚洲", "category": "topic"},
    # 其他
    {"name": "other", "display_name": "其他", "category": "topic"},
]

SIMILARITY_THRESHOLD = 0.85


class TagService:
    """标签服务：提供标签归一化、同义词管理、合并等功能。"""

    @staticmethod
    def get_search_terms(
        db: Session,
        *,
        categories: list[str] | None = None,
        parent_id: int | None = None,
    ) -> list[str]:
        """从 tag + tagsynonym 汇总去重后的匹配词（display_name、name、synonym）。

        Args:
            parent_id: 若指定，则只返回该父标签的子标签；为 None 则返回所有标签。
        """
        stmt = select(Tag)
        if categories:
            stmt = stmt.where(Tag.category.in_(categories))
        if parent_id is not None:
            stmt = stmt.where(Tag.parent_id == parent_id)
        elif parent_id is None:
            # 不加 parent_id 过滤时保持原有行为：查所有标签
            pass
        tags = list(db.exec(stmt).all())

        terms: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            for candidate in (tag.display_name, tag.name):
                key = candidate.strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    terms.append(candidate.strip())
            if tag.synonyms:
                for syn in tag.synonyms:
                    key = syn.synonym.strip().lower()
                    if key and key not in seen:
                        seen.add(key)
                        terms.append(syn.synonym.strip())
        return terms

    @staticmethod
    def seed_default_tags(db: Session) -> None:
        """初始化种子标签（仅在 tag 表为空时插入）。"""
        existing = db.exec(select(Tag)).first()
        if existing is not None:
            logger.info("Tag 表已有数据，跳过种子初始化")
            return

        for seed in SEED_TAGS:
            tag = Tag(
                name=seed["name"],
                display_name=seed["display_name"],
                category=seed["category"],
                usage_count=0,
            )
            db.add(tag)
        db.commit()
        logger.info(f"已初始化 {len(SEED_TAGS)} 条种子标签")

    @staticmethod
    def normalize(raw_tags: dict[str, Any]) -> dict[str, Any]:
        """对 LLM 返回的标签进行归一化处理。

        流程：
        1. 取 raw_tags["tags"] 列表，逐项 strip
        2. 查 TagSynonym 命中则归并到主 tag
        3. difflib.SequenceMatcher 相似度 ≥ 0.85 归并
        4. 归并后写入 TagSynonym(source='llm')
        5. usage_count += 1
        6. 返回 {**raw_tags, "tags": [主名们], "tag_ids": [int ids]}
        """
        with Session(engine) as db:
            tag_list: list[str] = raw_tags.get("tags", [])
            if not tag_list:
                return {**raw_tags, "tags": [], "tag_ids": [], "parent_names": []}

            # Step 1: strip
            cleaned = [t.strip() for t in tag_list if t.strip()]
            if not cleaned:
                return {**raw_tags, "tags": [], "tag_ids": [], "parent_names": []}

            # 获取所有主 tag
            all_tags: list[Tag] = list(db.exec(select(Tag)).all())

            # 建立 name→Tag 映射
            name_to_tag: dict[str, Tag] = {t.name: t for t in all_tags}

            # 建立 synonym→Tag 映射
            synonym_to_tag: dict[str, Tag] = {}
            for tag in all_tags:
                if tag.synonyms:
                    for syn in tag.synonyms:
                        synonym_to_tag[syn.synonym.lower()] = tag

            merged_names: list[str] = []
            merged_ids: list[int] = []
            new_synonyms: list[tuple[str, Tag]] = []

            for raw in cleaned:
                raw_lower = raw.lower()
                matched_tag: Tag | None = None

                # Step 2: 查同义词表
                if raw_lower in synonym_to_tag:
                    matched_tag = synonym_to_tag[raw_lower]

                # Step 3: 相似度匹配
                if matched_tag is None:
                    best_ratio = 0.0
                    best_name = ""
                    for tag_name in name_to_tag:
                        ratio = difflib.SequenceMatcher(None, raw_lower, tag_name).ratio()
                        if ratio >= SIMILARITY_THRESHOLD and ratio > best_ratio:
                            best_ratio = ratio
                            best_name = tag_name
                    if best_name:
                        matched_tag = name_to_tag[best_name]

                if matched_tag:
                    if matched_tag.name not in merged_names:
                        merged_names.append(matched_tag.name)
                        merged_ids.append(matched_tag.id)
                    if raw_lower != matched_tag.name.lower():
                        new_synonyms.append((raw, matched_tag))
                else:
                    # 未匹配，创建新 tag
                    safe_name = raw_lower.replace(" ", "_")[:100]
                    new_tag = Tag(
                        name=safe_name,
                        display_name=raw,
                        category="topic",
                        usage_count=1,
                    )
                    db.add(new_tag)
                    db.flush()
                    merged_names.append(new_tag.name)
                    merged_ids.append(new_tag.id)

            # Step 4: 写入新发现的同义词
            for synonym, tag in new_synonyms:
                existing = db.exec(
                    select(TagSynonym).where(TagSynonym.synonym == synonym)
                ).first()
                if not existing:
                    ts = TagSynonym(
                        tag_id=tag.id,
                        synonym=synonym,
                        source="llm",
                    )
                    db.add(ts)

            # Step 5: usage_count += 1
            for tag_id in merged_ids:
                tag = db.get(Tag, tag_id)
                if tag:
                    tag.usage_count += 1
                    db.add(tag)

            db.commit()

        # 收集归一化后标签对应的 parent_name（用于前端树展示）
        parent_names: list[str | None] = []
        for tag_id in merged_ids:
            tag = db.get(Tag, tag_id)
            if tag and tag.parent_id:
                parent = db.get(Tag, tag.parent_id)
                parent_names.append(parent.name if parent else None)
            else:
                parent_names.append(None)

        return {
            **raw_tags,
            "tags": merged_names,
            "tag_ids": merged_ids,
            "parent_names": parent_names,
        }

    @staticmethod
    def get_or_create_tag(name: str, category: str | None = None) -> Tag:
        """根据 name 查找或创建标签。"""
        with Session(engine) as db:
            tag = db.exec(select(Tag).where(Tag.name == name)).first()
            if not tag:
                tag = Tag(name=name, display_name=name, category=category or "topic")
                db.add(tag)
                db.commit()
                db.refresh(tag)
            return tag

    @staticmethod
    def add_synonym(tag_id: int, synonym: str, source: str = "user") -> TagSynonym:
        """为标签添加同义词。"""
        with Session(engine) as db:
            ts = TagSynonym(tag_id=tag_id, synonym=synonym.strip(), source=source)
            db.add(ts)
            db.commit()
            db.refresh(ts)
            return ts

    @staticmethod
    def merge_tags(source_ids: list[int], target_id: int) -> None:
        """将多个源标签合并到目标标签。"""
        with Session(engine) as db:
            target = db.get(Tag, target_id)
            if not target:
                return

            for sid in source_ids:
                if sid == target_id:
                    continue
                source = db.get(Tag, sid)
                if not source:
                    continue
                # 合并 usage_count
                target.usage_count += source.usage_count
                # 将源标签的同义词迁移到目标标签
                synonyms = db.exec(select(TagSynonym).where(TagSynonym.tag_id == sid)).all()
                for syn in synonyms:
                    existing = db.exec(
                        select(TagSynonym).where(
                            TagSynonym.synonym == syn.synonym,
                            TagSynonym.tag_id == target_id,
                        )
                    ).first()
                    if not existing:
                        syn.tag_id = target_id
                        db.add(syn)
                db.delete(source)

            db.add(target)
            db.commit()
