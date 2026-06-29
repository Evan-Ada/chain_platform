from datetime import date, datetime, timezone
from typing import Any

from pydantic import EmailStr
from sqlalchemy import DateTime, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str = Field(min_length=3, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserRegister(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    username: str | None = Field(default=None, min_length=3, max_length=255)  # type: ignore[assignment]
    email: str | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserUpdateMe(SQLModel):
    username: str | None = Field(default=None, min_length=3, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: int
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: int = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: int
    owner_id: int
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


class HealthStatus(SQLModel):
    status: str
    pg: bool
    mongo: bool
    redis: bool
    version: str


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ──────────────────────────────────────────────
# 内容订阅系统模型
# ──────────────────────────────────────────────


# --- Subscription ---
class SubscriptionBase(SQLModel):
    name: str = Field(max_length=255)
    keywords: list[str] = Field(default=[], sa_column=Column(JSONB, nullable=False, server_default="[]"))
    sources: list[str] = Field(default=["rss"], sa_column=Column(JSONB, nullable=False, server_default='["rss"]'))
    schedule_type: str = Field(default="daily", max_length=20)  # hourly | daily | weekly
    schedule_cron: str = Field(default="0 8 * * *", max_length=100)
    enabled: bool = True


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SQLModel):
    name: str | None = None
    keywords: list[str] | None = None
    sources: list[str] | None = None
    schedule_type: str | None = None
    schedule_cron: str | None = None
    enabled: bool | None = None


class Subscription(SubscriptionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    last_run_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    contents: list["ContentRecord"] = Relationship(back_populates="subscription", cascade_delete=True)


class SubscriptionPublic(SubscriptionBase):
    id: int
    user_id: int
    last_run_at: datetime | None = None
    created_at: datetime | None = None


class SubscriptionsPublic(SQLModel):
    data: list[SubscriptionPublic]
    count: int


# --- ContentRecord ---
class ContentRecordBase(SQLModel):
    title: str = Field(max_length=500)
    content: str | None = Field(default=None)
    source_url: str = Field(max_length=1000)
    source_name: str = Field(max_length=100)  # 平台名称
    url_hash: str = Field(max_length=64, unique=True)  # SHA256 去重
    keywords_matched: list[str] = Field(default=[], sa_column=Column(JSONB, nullable=False, server_default="[]"))
    is_read: bool = False
    # --- LLM 打标字段 ---
    llm_status: str = "pending"  # pending | processing | done | failed
    llm_tags: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False, server_default="{}"))
    llm_error: str | None = Field(default=None)


class ContentRecord(ContentRecordBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id", nullable=False, ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    subscription: Subscription | None = Relationship(back_populates="contents")


class ContentRecordPublic(ContentRecordBase):
    id: int
    subscription_id: int
    created_at: datetime | None = None


class ContentRecordsPublic(SQLModel):
    data: list[ContentRecordPublic]
    count: int


# --- LLMConfig ---
class LLMConfigBase(SQLModel):
    name: str = Field(max_length=100)
    provider: str = Field(default="openai", max_length=50)  # openai / deepseek / etc
    api_key: str = Field(max_length=500)
    base_url: str = Field(default="https://api.openai.com/v1", max_length=500)
    model: str = Field(default="gpt-4o-mini", max_length=100)
    enabled: bool = True
    is_default: bool = False
    extra: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False, server_default="{}"))
    # 软删除与连通测试字段
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_test_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_test_status: str | None = Field(default=None, max_length=20)  # success / failed / unknown
    last_test_message: str | None = Field(default=None, max_length=500)


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=100)
    enabled: bool | None = None
    is_default: bool | None = None
    extra: dict[str, Any] | None = None
    deleted_at: datetime | None = None
    last_test_at: datetime | None = None
    last_test_status: str | None = None
    last_test_message: str | None = None


class LLMConfig(LLMConfigBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class LLMConfigPublic(LLMConfigBase):
    """对外返回时隐藏 api_key。"""
    id: int
    created_at: datetime | None = None

    model_config = {"json_schema_extra": {"exclude": {"api_key"}}}


class LLMConfigPublicMasked(LLMConfigBase):
    """对外返回时 api_key 仅显示后四位，并包含软删除与测试字段。"""
    id: int
    created_at: datetime | None = None
    masked_api_key: str = ""
    # 覆盖继承的 api_key，Public 中不暴露
    model_config = {"json_schema_extra": {"exclude": {"api_key"}}}


class LLMConfigsPublic(SQLModel):
    data: list[LLMConfigPublicMasked]
    count: int


# --- DataSourceConfig ---
class DataSourceConfigBase(SQLModel):
    name: str = Field(max_length=100)
    source_type: str = Field(max_length=50)  # rss / api / crawler
    enabled: bool = True
    config: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False, server_default="{}"))


class DataSourceConfigCreate(DataSourceConfigBase):
    pass


class DataSourceConfigUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    source_type: str | None = Field(default=None, max_length=50)
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class DataSourceConfig(DataSourceConfigBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class DataSourceConfigPublic(DataSourceConfigBase):
    id: int
    created_at: datetime | None = None


class DataSourceConfigsPublic(SQLModel):
    data: list[DataSourceConfigPublic]
    count: int


# ──────────────────────────────────────────────
# Tag / TagSynonym（标签字典 + 同义词）
# ──────────────────────────────────────────────


class TagBase(SQLModel):
    name: str = Field(max_length=100, unique=True)
    display_name: str = Field(max_length=255)
    category: str | None = Field(default=None, max_length=50)  # topic | industry | sentiment
    usage_count: int = 0


class Tag(TagBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    synonyms: list["TagSynonym"] = Relationship(back_populates="tag", cascade_delete=True)


class TagPublic(TagBase):
    id: int
    created_at: datetime | None = None


# --- TagSynonym ---
class TagSynonymBase(SQLModel):
    synonym: str = Field(max_length=255, unique=True)
    source: str = Field(max_length=20)  # seed | llm | user


class TagSynonym(TagSynonymBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", nullable=False, ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    tag: Tag | None = Relationship(back_populates="synonyms")


class TagSynonymPublic(TagSynonymBase):
    id: int
    tag_id: int
    created_at: datetime | None = None


# ──────────────────────────────────────────────
# ScheduledTask（全局调度任务）
# ──────────────────────────────────────────────


class ScheduledTaskBase(SQLModel):
    name: str = Field(max_length=255)
    biz_type: str = Field(max_length=50)  # subscription | custom
    biz_id: int | None = Field(default=None)
    cron_expr: str = Field(max_length=100)
    enabled: bool = True


class ScheduledTask(ScheduledTaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    last_run_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    next_run_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    owner_user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class ScheduledTaskPublic(ScheduledTaskBase):
    id: int
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    owner_user_id: int
    created_at: datetime | None = None


# ──────────────────────────────────────────────
# PushPreference / PushMessage / UserDevice
# ──────────────────────────────────────────────


class PushPreferenceBase(SQLModel):
    channels: dict[str, bool] = Field(
        default={"email": True, "app": True},
        sa_column=Column(JSONB, nullable=False, server_default='{"email":true,"app":true}'),
    )
    push_time: str = Field(default="08:00:00", max_length=20)
    timezone: str = Field(default="Asia/Shanghai", max_length=50)
    daily_digest: bool = True
    importance_filter: list[str] = Field(
        default=["high", "medium"],
        sa_column=Column(JSONB, nullable=False, server_default='["high","medium"]'),
    )


class PushPreference(PushPreferenceBase, table=True):
    id: int = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class PushPreferencePublic(PushPreferenceBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


# --- PushMessage ---
class PushMessageBase(SQLModel):
    subscription_id: int | None = Field(default=None)
    content_record_id: int | None = Field(default=None)
    title: str = Field(max_length=500)
    summary: str = Field(max_length=2000)
    tags: list[str] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    importance: str = Field(max_length=20)  # high | medium | low
    channel: str = Field(max_length=20)  # email | app
    status: str = Field(max_length=20)  # pending | sent | failed | read
    sent_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    read_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    push_date: date | None = None


class PushMessage(PushMessageBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class PushMessagePublic(PushMessageBase):
    id: int
    user_id: int
    created_at: datetime | None = None


# --- UserDevice ---
class UserDeviceBase(SQLModel):
    platform: str = Field(max_length=20)  # h5 | app | mp-weixin | mp-alipay
    device_id: str = Field(max_length=255)
    push_token: str | None = Field(default=None, max_length=500)


class UserDevice(UserDeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    last_active_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class UserDevicePublic(UserDeviceBase):
    id: int
    user_id: int
    last_active_at: datetime | None = None
    created_at: datetime | None = None
