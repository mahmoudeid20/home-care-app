"""add reviews and notifications tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

notification_type_enum = postgresql.ENUM(
    "NEW_REQUEST",
    "REQUEST_ACCEPTED",
    "REQUEST_REJECTED",
    "BOOKING_CONFIRMED",
    "BOOKING_CANCELLED",
    "NEW_MESSAGE",
    "BOOKING_REMINDER",
    "DOCUMENT_VERIFICATION_RESULT",
    "NEW_REVIEW",
    name="notification_type",
)


def upgrade() -> None:
    bind = op.get_bind()
    notification_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column(
            "patient_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "nurse_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("professionalism", sa.Integer(), nullable=False),
        sa.Column("communication", sa.Integer(), nullable=False),
        sa.Column("care_quality", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "overall_rating BETWEEN 1 AND 5 AND professionalism BETWEEN 1 AND 5 "
            "AND communication BETWEEN 1 AND 5 AND care_quality BETWEEN 1 AND 5",
            name="ck_review_ratings_1_to_5",
        ),
    )
    op.create_index("ix_reviews_patient_id", "reviews", ["patient_id"])
    op.create_index("ix_reviews_nurse_id", "reviews", ["nurse_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "type",
            postgresql.ENUM(
                "NEW_REQUEST", "REQUEST_ACCEPTED", "REQUEST_REJECTED", "BOOKING_CONFIRMED",
                "BOOKING_CANCELLED", "NEW_MESSAGE", "BOOKING_REMINDER",
                "DOCUMENT_VERIFICATION_RESULT", "NEW_REVIEW",
                name="notification_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])


def downgrade() -> None:
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_reviews_nurse_id", table_name="reviews")
    op.drop_index("ix_reviews_patient_id", table_name="reviews")
    op.drop_table("reviews")

    bind = op.get_bind()
    notification_type_enum.drop(bind, checkfirst=True)
