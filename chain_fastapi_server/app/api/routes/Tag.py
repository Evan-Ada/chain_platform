"""Tag 标签管理路由。"""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.response import resp_200, resp_400
from app.models import Tag, TagSynonym

router = APIRouter(prefix="/Tag", tags=["Tag"])


# ── 请求模型 ──


class ListTagM(BaseModel):
    keyword: str | None = None
    category: str | None = None
    page_num: int = 1
    page_size: int = 20


class MergeTagM(BaseModel):
    source_tag_ids: list[int]
    target_tag_id: int


class RenameTagM(BaseModel):
    tag_id: int
    new_name: str


class AddSynonymM(BaseModel):
    tag_id: int
    synonym: str


class RemoveSynonymM(BaseModel):
    synonym_id: int


# ── 路由 ──


from app.models import Tag  # noqa: F401 (re-export for response_model)

TagListResponse = dict  # openapi-schema placeholder


@router.post("/list")
async def listTags(pm: ListTagM, db: SessionDep, current_user: CurrentUser) -> TagListResponse:
    """分页查询标签列表。"""
    stmt = select(Tag)
    count_stmt = select(0)

    if pm.keyword:
        stmt = stmt.where(Tag.display_name.ilike(f"%{pm.keyword}%"))
        count_stmt = select(Tag).where(Tag.display_name.ilike(f"%{pm.keyword}%"))

    if pm.category:
        stmt = stmt.where(Tag.category == pm.category)
        count_stmt = select(Tag).where(Tag.category == pm.category)

    total = len(list(db.exec(count_stmt).all()))
    offset = (pm.page_num - 1) * pm.page_size
    stmt = stmt.order_by(Tag.usage_count.desc()).offset(offset).limit(pm.page_size)
    tags = list(db.exec(stmt).all())

    data = [_tag_to_dict(t) for t in tags]
    return resp_200(200, "查询成功", {"total": total, "res": data})


@router.post("/merge")
async def mergeTags(pm: MergeTagM, db: SessionDep, current_user: CurrentUser):
    """合并标签（admin）：将 source_tag_ids 合并到 target_tag_id。"""
    from app.services.tag_service import TagService

    try:
        TagService.merge_tags(pm.source_tag_ids, pm.target_tag_id)
        return resp_200(200, "合并成功")
    except Exception as e:
        return resp_400(400, f"合并失败: {e}")


@router.post("/rename")
async def renameTag(pm: RenameTagM, db: SessionDep, current_user: CurrentUser):
    """修改标签 display_name（admin）。"""
    tag = db.get(Tag, pm.tag_id)
    if not tag:
        return resp_400(400, "标签不存在")
    tag.display_name = pm.new_name
    db.add(tag)
    db.commit()
    return resp_200(200, "更新成功", _tag_to_dict(tag))


@router.post("/addSynonym")
async def addSynonym(pm: AddSynonymM, db: SessionDep, current_user: CurrentUser):
    """为标签添加同义词。"""
    tag = db.get(Tag, pm.tag_id)
    if not tag:
        return resp_400(400, "标签不存在")

    existing = db.exec(
        select(TagSynonym).where(
            TagSynonym.tag_id == pm.tag_id,
            TagSynonym.synonym == pm.synonym,
        )
    ).first()
    if existing:
        return resp_400(400, "同义词已存在")

    ts = TagSynonym(tag_id=pm.tag_id, synonym=pm.synonym, source="user")
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return resp_200(200, "添加成功", _synonym_to_dict(ts))


@router.post("/removeSynonym")
async def removeSynonym(pm: RemoveSynonymM, db: SessionDep, current_user: CurrentUser):
    """删除同义词。"""
    ts = db.get(TagSynonym, pm.synonym_id)
    if not ts:
        return resp_400(400, "同义词不存在")
    db.delete(ts)
    db.commit()
    return resp_200(200, "删除成功")


@router.post("/stats")
async def tagStats(db: SessionDep, current_user: CurrentUser):
    """返回标签统计（含同义词数量）。"""
    tags = db.exec(select(Tag).order_by(Tag.usage_count.desc())).all()
    stats = []
    for t in tags:
        synonyms_count = len(t.synonyms) if t.synonyms else 0
        stats.append({
            "name": t.name,
            "display_name": t.display_name,
            "category": t.category,
            "usage_count": t.usage_count,
            "synonyms_count": synonyms_count,
        })
    return resp_200(200, "查询成功", stats)


# ── 私有方法 ──


def _tag_to_dict(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "display_name": tag.display_name,
        "category": tag.category,
        "usage_count": tag.usage_count,
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
    }


def _synonym_to_dict(syn: TagSynonym) -> dict:
    return {
        "id": syn.id,
        "tag_id": syn.tag_id,
        "synonym": syn.synonym,
        "source": syn.source,
        "created_at": syn.created_at.isoformat() if syn.created_at else None,
    }
