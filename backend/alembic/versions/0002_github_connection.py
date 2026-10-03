"""add GitHub connection and OAuth state tables

Revision ID: 0002_github_connection
Revises: 0001_initial
"""
import sqlalchemy as sa

from alembic import op

revision = "0002_github_connection"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_connections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_user_id", sa.String(length=50), nullable=False),
        sa.Column("github_login", sa.String(length=255), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_github_connections_user_id", "github_connections", ["user_id"])
    op.create_table(
        "github_oauth_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("state_hash"),
    )
    op.create_index("ix_github_oauth_states_user_id", "github_oauth_states", ["user_id"])
    op.create_index("ix_github_oauth_states_state_hash", "github_oauth_states", ["state_hash"])
    op.create_index("ix_github_oauth_states_expires_at", "github_oauth_states", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_github_oauth_states_expires_at", table_name="github_oauth_states")
    op.drop_index("ix_github_oauth_states_state_hash", table_name="github_oauth_states")
    op.drop_index("ix_github_oauth_states_user_id", table_name="github_oauth_states")
    op.drop_table("github_oauth_states")
    op.drop_index("ix_github_connections_user_id", table_name="github_connections")
    op.drop_table("github_connections")
