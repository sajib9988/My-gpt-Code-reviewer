"""add repository scan and indexed file tables

Revision ID: 0003_repository_scan
Revises: 0002_github_connection
"""
import sqlalchemy as sa

from alembic import op

revision = "0003_repository_scan"
down_revision = "0002_github_connection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repository_scans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("branch", sa.String(length=255), nullable=False),
        sa.Column("commit_sha", sa.String(length=100)),
        sa.Column("framework", sa.String(length=100)),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("files_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_repository_scans_project_id", "repository_scans", ["project_id"])
    op.create_table(
        "project_files",
        sa.Column("id", sa.String(length=1100), primary_key=True),
        sa.Column(
            "scan_id",
            sa.String(length=36),
            sa.ForeignKey("repository_scans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("file_type", sa.String(length=30), nullable=False, server_default="file"),
        sa.Column("language", sa.String(length=50)),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha", sa.String(length=100)),
    )
    op.create_index("ix_project_files_scan_id", "project_files", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_project_files_scan_id", table_name="project_files")
    op.drop_table("project_files")
    op.drop_index("ix_repository_scans_project_id", table_name="repository_scans")
    op.drop_table("repository_scans")
