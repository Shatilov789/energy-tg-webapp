"""drop the legacy questionnaire section; notifications point at process objects

The old «Обʼєкти» section (scenarios, steps, text answers, locks, admin comments,
step threads, status notes, worker links) is gone. Its data is dropped without
transfer: there was none in production (decision in #29).

Notifications now reference a deal and, optionally, a stage visit. Their type
becomes a plain string so new kinds need no enum migration.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-17 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_NOTIFICATION_TYPES = (
    "REMINDER",
    "ADMIN_COMMENT",
    "OBJECT_SHARED",
    "STEP_UNLOCKED",
    "STEP_COMMENT",
    "WORKER_ASSIGNED",
    "WORKER_REMOVED",
    "OBJECT_COMPLETED",
)


def upgrade() -> None:
    # Every existing notification points at the legacy section (decision 2 in #29).
    op.execute("DELETE FROM notifications")
    op.drop_constraint("notifications_object_id_fkey", "notifications", type_="foreignkey")
    op.drop_column("notifications", "object_id")
    op.drop_column("notifications", "step_number")
    op.add_column("notifications", sa.Column("deal_id", sa.Integer(), nullable=True))
    op.add_column("notifications", sa.Column("progress_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "notifications_deal_id_fkey", "notifications", "deals", ["deal_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "notifications_progress_id_fkey",
        "notifications",
        "deal_stage_progress",
        ["progress_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column(
        "notifications",
        "type",
        type_=sa.String(length=50),
        existing_nullable=False,
        postgresql_using="type::text",
    )
    op.execute("DROP TYPE IF EXISTS notificationtype")

    op.drop_index(op.f("ix_audit_logs_object_id"), table_name="audit_logs")
    op.drop_constraint("audit_logs_object_id_fkey", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "object_id")

    # Children first, so foreign keys never point at a dropped table.
    for table in (
        "admin_comments",
        "step_status_notes",
        "step_comments",
        "object_answers",
        "object_workers",
        "objects",
        "scenario_steps",
        "scenarios",
    ):
        op.drop_table(table)
    op.execute("DROP TYPE IF EXISTS objectstatus")
    op.execute("DROP TYPE IF EXISTS objectcriticality")


def downgrade() -> None:
    # The tables come back empty: the legacy data was dropped on upgrade.
    _create_legacy_tables()

    op.add_column("audit_logs", sa.Column("object_id", sa.Integer(), nullable=True))
    op.create_foreign_key("audit_logs_object_id_fkey", "audit_logs", "objects", ["object_id"], ["id"])
    op.create_index(op.f("ix_audit_logs_object_id"), "audit_logs", ["object_id"], unique=False)

    # Rows of kinds the old enum does not know cannot survive the type change.
    kinds = ", ".join(f"'{kind}'" for kind in LEGACY_NOTIFICATION_TYPES)
    op.execute(f"DELETE FROM notifications WHERE type NOT IN ({kinds})")
    notification_type = sa.Enum(*LEGACY_NOTIFICATION_TYPES, name="notificationtype")
    notification_type.create(op.get_bind())
    op.alter_column(
        "notifications",
        "type",
        type_=notification_type,
        existing_nullable=False,
        postgresql_using="type::notificationtype",
    )
    op.drop_constraint("notifications_progress_id_fkey", "notifications", type_="foreignkey")
    op.drop_constraint("notifications_deal_id_fkey", "notifications", type_="foreignkey")
    op.drop_column("notifications", "progress_id")
    op.drop_column("notifications", "deal_id")
    op.add_column("notifications", sa.Column("object_id", sa.Integer(), nullable=True))
    op.add_column("notifications", sa.Column("step_number", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "notifications_object_id_fkey", "notifications", "objects", ["object_id"], ["id"], ondelete="SET NULL"
    )


def _create_legacy_tables() -> None:
    """Recreate the legacy tables exactly as revisions 0001 and 0002 left them."""
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenarios_is_deleted"), "scenarios", ["is_deleted"], unique=False)
    op.create_table(
        "objects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("IN_PROGRESS", "COMPLETED", name="objectstatus"), nullable=False),
        sa.Column("criticality", sa.Enum("NORMAL", "HIGH", "CRITICAL", name="objectcriticality"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_objects_created_by_id"), "objects", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_objects_is_deleted"), "objects", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_objects_scenario_id"), "objects", ["scenario_id"], unique=False)
    op.create_table(
        "scenario_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenario_steps_scenario_id"), "scenario_steps", ["scenario_id"], unique=False)
    op.create_table(
        "object_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("answered_by_id", sa.Integer(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["answered_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["scenario_steps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_object_answers_answered_by_id"), "object_answers", ["answered_by_id"], unique=False)
    op.create_index(op.f("ix_object_answers_is_deleted"), "object_answers", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_object_answers_object_id"), "object_answers", ["object_id"], unique=False)
    op.create_index(op.f("ix_object_answers_step_id"), "object_answers", ["step_id"], unique=False)
    op.create_index(
        "uq_object_answers_object_step_active",
        "object_answers",
        ["object_id", "step_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_table(
        "object_workers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_id", "user_id", name="uq_object_workers_object_user"),
    )
    op.create_index(op.f("ix_object_workers_object_id"), "object_workers", ["object_id"], unique=False)
    op.create_index(op.f("ix_object_workers_user_id"), "object_workers", ["user_id"], unique=False)
    op.create_table(
        "step_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("recipient_id", sa.Integer(), nullable=True),
        sa.Column("reply_to_id", sa.Integer(), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("is_system_event", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reply_to_id"], ["step_comments.id"]),
        sa.ForeignKeyConstraint(["step_id"], ["scenario_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_step_comments_author_id"), "step_comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_step_comments_object_id"), "step_comments", ["object_id"], unique=False)
    op.create_index(op.f("ix_step_comments_recipient_id"), "step_comments", ["recipient_id"], unique=False)
    op.create_index(op.f("ix_step_comments_step_id"), "step_comments", ["step_id"], unique=False)
    op.create_table(
        "step_status_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["scenario_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_step_status_notes_author_id"), "step_status_notes", ["author_id"], unique=False)
    op.create_index(op.f("ix_step_status_notes_object_id"), "step_status_notes", ["object_id"], unique=False)
    op.create_index(op.f("ix_step_status_notes_step_id"), "step_status_notes", ["step_id"], unique=False)
    op.create_table(
        "admin_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["answer_id"], ["object_answers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_comments_admin_id"), "admin_comments", ["admin_id"], unique=False)
    op.create_index(op.f("ix_admin_comments_answer_id"), "admin_comments", ["answer_id"], unique=False)
