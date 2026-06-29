"""init int pk schema

Revision ID: a7f0c1b9d2e3
Revises: fe56fa70289e
Create Date: 2026-06-09 00:00:00.000000

本迁移把内容订阅/标签/推送系统的所有 UUID 主键与外键统一替换为
PostgreSQL 自增 Integer。User/Item 表保持现状（已在 d98dd8ec85a3
历史迁移里转换过）。云端 DB 36.213.33.96:5432 已经把 user 表的 id
列换成 integer，因此本次迁移按"现状已经是 int 形态"的目标 schema
来做。

由于本迁移依赖 .env 提供的云端 DB 凭据，**不**在本次自动化中
执行 `alembic upgrade head`，由主 Agent 在确认云端状态后手动执行。
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a7f0c1b9d2e3"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tag
    op.create_table(
        "tag",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tag_name", "tag", ["name"], unique=True)

    # tagsynonym
    op.create_table(
        "tagsynonym",
        sa.Column("synonym", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("synonym"),
    )
    op.create_index("ix_tagsynonym_synonym", "tagsynonym", ["synonym"], unique=True)

    # scheduledtask
    op.create_table(
        "scheduledtask",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("biz_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("biz_id", sa.Integer(), nullable=True),
        sa.Column("cron_expr", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduledtask_biz_type", "scheduledtask", ["biz_type"], unique=False)
    op.create_index("ix_scheduledtask_enabled", "scheduledtask", ["enabled"], unique=False)

    # pushpreference
    op.create_table(
        "pushpreference",
        sa.Column(
            "channels",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{"email":true,"app":true}',
            nullable=False,
        ),
        sa.Column(
            "push_time",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="08:00:00",
        ),
        sa.Column(
            "timezone",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
            server_default="Asia/Shanghai",
        ),
        sa.Column("daily_digest", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "importance_filter",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='["high","medium"]',
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # userdevice
    op.create_table(
        "userdevice",
        sa.Column("platform", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("device_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("push_token", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "platform", "device_id", name="uq_userdevice_user_platform_device"),
    )
    op.create_index("ix_userdevice_user_id", "userdevice", ["user_id"], unique=False)

    # datasourceconfig
    op.create_table(
        "datasourceconfig",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("source_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # llmconfig
    op.create_table(
        "llmconfig",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("api_key", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("base_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # subscription
    op.create_table(
        "subscription",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), server_default='["rss"]', nullable=False),
        sa.Column("schedule_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("schedule_cron", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # contentrecord
    op.create_table(
        "contentrecord",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("source_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("url_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column(
            "keywords_matched",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("llm_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("llm_tags", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("llm_error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscription.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url_hash"),
    )

    # pushmessage（依赖 subscription / contentrecord）
    op.create_table(
        "pushmessage",
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("content_record_id", sa.Integer(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("importance", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("channel", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("push_date", sa.Date(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscription.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["content_record_id"], ["contentrecord.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pushmessage_user_id", "pushmessage", ["user_id"], unique=False)
    op.create_index("ix_pushmessage_status", "pushmessage", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("contentrecord")
    op.drop_table("subscription")
    op.drop_table("llmconfig")
    op.drop_table("datasourceconfig")
    op.drop_table("userdevice")
    op.drop_table("pushmessage")
    op.drop_table("pushpreference")
    op.drop_table("scheduledtask")
    op.drop_table("tagsynonym")
    op.drop_table("tag")
