"""integrity constraints: one live answer per step, one worker link per user

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Duplicates left by double taps: keep the earliest live answer and soft-delete the rest,
    # so admin comments attached to them are not lost.
    op.execute(
        """
        UPDATE object_answers SET is_deleted = true, deleted_at = now()
        WHERE is_deleted = false
          AND id NOT IN (
            SELECT min(id) FROM object_answers WHERE is_deleted = false GROUP BY object_id, step_id
          )
        """
    )
    op.create_index(
        "uq_object_answers_object_step_active",
        "object_answers",
        ["object_id", "step_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
        sqlite_where=sa.text("is_deleted = 0"),
    )

    # A worker link carries no data of its own, so the extra copies can simply go.
    op.execute(
        """
        DELETE FROM object_workers
        WHERE id NOT IN (SELECT min(id) FROM object_workers GROUP BY object_id, user_id)
        """
    )
    op.create_unique_constraint("uq_object_workers_object_user", "object_workers", ["object_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_object_workers_object_user", "object_workers", type_="unique")
    op.drop_index("uq_object_answers_object_step_active", table_name="object_answers")
