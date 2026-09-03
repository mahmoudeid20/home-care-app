"""add admin_actions, platform_settings, payments, complaints tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

payment_status_enum = postgresql.ENUM(
    "PENDING", "PAID", "FAILED", "REFUNDED", "CANCELLED", name="payment_status"
)
complaint_status_enum = postgresql.ENUM(
    "OPEN", "IN_REVIEW", "RESOLVED", "CLOSED", name="complaint_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    payment_status_enum.create(bind, checkfirst=True)
    complaint_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "admin_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_admin_actions_admin_id", "admin_actions", ["admin_id"])
    op.create_index("ix_admin_actions_action_type", "admin_actions", ["action_type"])
    op.create_index("ix_admin_actions_target_id", "admin_actions", ["target_id"])

    op.create_table(
        "platform_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("commission_percentage", sa.Numeric(4, 3), nullable=False, server_default="0.10"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EGP"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "PAID", "FAILED", "REFUNDED", "CANCELLED",
                name="payment_status", create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("transaction_id", sa.String(200), nullable=True),
        sa.Column("platform_commission", sa.Numeric(10, 2), nullable=False),
        sa.Column("nurse_earnings", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_payments_status", "payments", ["status"])

    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "booking_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN", "IN_REVIEW", "RESOLVED", "CLOSED", name="complaint_status", create_type=False
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_complaints_user_id", "complaints", ["user_id"])
    op.create_index("ix_complaints_status", "complaints", ["status"])


def downgrade() -> None:
    op.drop_index("ix_complaints_status", table_name="complaints")
    op.drop_index("ix_complaints_user_id", table_name="complaints")
    op.drop_table("complaints")

    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_table("payments")

    op.drop_table("platform_settings")

    op.drop_index("ix_admin_actions_target_id", table_name="admin_actions")
    op.drop_index("ix_admin_actions_action_type", table_name="admin_actions")
    op.drop_index("ix_admin_actions_admin_id", table_name="admin_actions")
    op.drop_table("admin_actions")

    bind = op.get_bind()
    complaint_status_enum.drop(bind, checkfirst=True)
    payment_status_enum.drop(bind, checkfirst=True)
