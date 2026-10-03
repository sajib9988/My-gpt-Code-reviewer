"""add code change approval records

Revision ID: 0005_code_changes
Revises: 0004_agent_workspace
"""
import sqlalchemy as sa

from alembic import op

revision = "0005_code_changes"
down_revision = "0004_agent_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "code_changes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("agent_runs.id", ondelete="SET NULL")),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("old_content", sa.Text()),
        sa.Column("new_content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("branch", sa.String(length=255)),
        sa.Column("commit_sha", sa.String(length=100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_code_changes_project_id", "code_changes", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_code_changes_project_id", table_name="code_changes")
    op.drop_table("code_changes")
