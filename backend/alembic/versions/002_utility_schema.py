"""Utility schema: journal_notes table.

Creates the journal_notes table for storing user-authored notes and photo
references attached to confirmed visits. Each visit may have at most one
journal note.

Revision ID: 002
Revises: 001
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create journal_notes table with FK constraints and indexes."""

    op.create_table(
        "journal_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "visit_id",
            sa.Integer(),
            sa.ForeignKey("visits.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("text", sa.String(1000), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Composite index for efficient lookups by user and visit
    op.create_index(
        "ix_journal_notes_user_id_visit_id",
        "journal_notes",
        ["user_id", "visit_id"],
    )


def downgrade() -> None:
    """Drop journal_notes table."""

    op.drop_index("ix_journal_notes_user_id_visit_id", table_name="journal_notes")
    op.drop_table("journal_notes")
