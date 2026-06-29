"""add deleted_at and last_test fields to llmconfig

Revision ID: ae290dce401b
Revises: a7f0c1b9d2e3
Create Date: 2026-06-29 10:36:07.214688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae290dce401b'
down_revision = 'a7f0c1b9d2e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### LLMConfig 软删除与连通测试字段 ###
    op.add_column('llmconfig', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('llmconfig', sa.Column('last_test_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('llmconfig', sa.Column('last_test_status', sa.String(length=20), nullable=True))
    op.add_column('llmconfig', sa.Column('last_test_message', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('llmconfig', 'last_test_message')
    op.drop_column('llmconfig', 'last_test_status')
    op.drop_column('llmconfig', 'last_test_at')
    op.drop_column('llmconfig', 'deleted_at')
