"""add applications and bookings tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

application_status_enum = postgresql.ENUM(
    "PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN", name="application_status"
)
booking_status_enum = postgresql.ENUM(
    "ACCEPTED", "CONFIRMED", "ACTIVE", "COMPLETED", "REVIEWED", "CANCELLED", "EXPIRED",
    name="booking_status",
)


def upgrade() -> None:
    bind = op.get_bind()
    application_status_enum.create(bind, checkfirst=True)
    booking_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "care_request_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "nurse_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "patient_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN",
                name="application_status", create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_applications_care_request_id", "applications", ["care_request_id"])
    op.create_index("ix_applications_nurse_id", "applications", ["nurse_id"])
    op.create_index("ix_applications_patient_id", "applications", ["patient_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "care_request_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "application_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column(
            "patient_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "nurse_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ACCEPTED", "CONFIRMED", "ACTIVE", "COMPLETED", "REVIEWED", "CANCELLED", "EXPIRED",
                name="booking_status", create_type=False,
            ),
            nullable=False,
            server_default="ACCEPTED",
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("hours_per_day", sa.Numeric(4, 1), nullable=True),
        sa.Column(
            "payment_frequency",
            postgresql.ENUM(
                "HOURLY", "DAILY", "WEEKLY", "MONTHLY", name="price_unit", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("agreed_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_bookings_care_request_id", "bookings", ["care_request_id"])
    op.create_index("ix_bookings_patient_id", "bookings", ["patient_id"])
    op.create_index("ix_bookings_nurse_id", "bookings", ["nurse_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])


def downgrade() -> None:
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_nurse_id", table_name="bookings")
    op.drop_index("ix_bookings_patient_id", table_name="bookings")
    op.drop_index("ix_bookings_care_request_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_patient_id", table_name="applications")
    op.drop_index("ix_applications_nurse_id", table_name="applications")
    op.drop_index("ix_applications_care_request_id", table_name="applications")
    op.drop_table("applications")

    bind = op.get_bind()
    booking_status_enum.drop(bind, checkfirst=True)
    application_status_enum.drop(bind, checkfirst=True)
