"""TagService 测试（单元测试）。"""

import uuid
from functools import wraps
from unittest.mock import patch

import pytest
from sqlmodel import Session, delete, select

from app.core.db import engine
from app.models import Tag, TagSynonym
from app.services.tag_service import TagService


def setup_tag_table() -> None:
    """清空 tag 相关表。"""
    try:
        with Session(engine) as db:
            db.exec(delete(TagSynonym))
            db.exec(delete(Tag))
            db.commit()
    except Exception:
        pass


class TestTagService:
    """测试 TagService 的各项功能。"""

    def test_seed_default_tags(self) -> None:
        """seed_default_tags 初始化 30+ 条标签。"""
        setup_tag_table()
        try:
            with Session(engine) as db:
                TagService.seed_default_tags(db)
                count = len(list(db.exec(select(Tag)).all()))
                assert count >= 30
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise

    def test_seed_skip_when_not_empty(self) -> None:
        """tag 表非空时跳过 seed。"""
        setup_tag_table()
        try:
            with Session(engine) as db:
                db.add(Tag(name="existing", display_name="已有", category="topic"))
                db.commit()
                TagService.seed_default_tags(db)
                count = len(list(db.exec(select(Tag)).all()))
                assert count == 1
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise

    def test_normalize_exact_match(self) -> None:
        """完全匹配的标签直接归并。"""
        setup_tag_table()
        try:
            with Session(engine) as db:
                TagService.seed_default_tags(db)
                raw = {"tags": ["tech", "finance"], "category": "news"}
                result = TagService.normalize(raw)
                assert "tech" in result["tags"]
                assert "finance" in result["tags"]
                assert "tag_ids" in result
                assert len(result["tag_ids"]) == 2
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise

    def test_normalize_similarity_match(self) -> None:
        """相似度 ≥ 0.85 归并。"""
        setup_tag_table()
        try:
            with Session(engine) as db:
                TagService.seed_default_tags(db)
                raw = {"tags": ["semiticonductor"], "category": "news"}
                result = TagService.normalize(raw)
                assert "semiconductor" in result["tags"]
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise

    def test_get_or_create_tag(self) -> None:
        """get_or_create_tag 查找或创建标签。"""
        setup_tag_table()
        try:
            tag1 = TagService.get_or_create_tag("new_tag", "topic")
            assert tag1.name == "new_tag"
            tag2 = TagService.get_or_create_tag("new_tag", "topic")
            assert tag2.id == tag1.id
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise

    def test_merge_tags(self) -> None:
        """merge_tags 将多个标签合并到目标。"""
        setup_tag_table()
        try:
            with Session(engine) as db:
                TagService.seed_default_tags(db)
                source1 = Tag(name="source1", display_name="源1", category="topic", usage_count=5)
                source2 = Tag(name="source2", display_name="源2", category="topic", usage_count=3)
                target = db.exec(select(Tag).where(Tag.name == "tech")).first()
                db.add(source1)
                db.add(source2)
                db.commit()
                db.refresh(source1)
                db.refresh(source2)

                original_usage = target.usage_count
                TagService.merge_tags([source1.id, source2.id], target.id)

                db.expire_all()
                refreshed_target = db.get(Tag, target.id)
                assert refreshed_target is not None
                assert refreshed_target.usage_count == original_usage + 5 + 3
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"DB unavailable: {e}")
            raise
