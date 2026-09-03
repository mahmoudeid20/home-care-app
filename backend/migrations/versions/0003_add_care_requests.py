"""add care_requests and related tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

care_request_status_enum = postgresql.ENUM(
    "OPEN", "MATCHED", "CLOSED", "EXPIRED", "CANCELLED", name="care_request_status"
)
mobility_status_enum = postgresql.ENUM(
    "INDEPENDENT", "NEEDS_ASSISTANCE", "WHEELCHAIR", "BEDRIDDEN", name="mobility_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    care_request_status_enum.create(bind, checkfirst=True)
    mobility_status_enum.create(bind, checkfirst=True)
    # nurse_gender, shift_type, and price_unit enums already exist from
    # migration 0002 and are reused here (create_type=False below).

    op.create_table(
        "care_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN", "MATCHED", "CLOSED", "EXPIRED", "CANCELLED",
                name="care_request_status", create_type=False,
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("patient_name", sa.String(150), nullable=False),
        sa.Column("patient_age", sa.Integer(), nullable=False),
        sa.Column(
            "patient_gender",
            postgresql.ENUM("MALE", "FEMALE", name="nurse_gender", create_type=False),
            nullable=False,
        ),
        sa.Column("medical_condition", sa.Text(), nullable=False),
        sa.Column(
            "mobility_status",
            postgresql.ENUM(
                "INDEPENDENT", "NEEDS_ASSISTANCE", "WHEELCHAIR", "BEDRIDDEN",
                name="mobility_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("special_requirements", sa.Text(), nullable=True),
        sa.Column(
            "preferred_nurse_gender",
            postgresql.ENUM("MALE", "FEMALE", name="nurse_gender", create_type=False),
            nullable=True,
        ),
        sa.Column("min_experience_years", sa.Integer(), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("verified_nurses_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "preferred_shift",
            postgresql.ENUM(
                "MORNING", "EVENING", "NIGHT", "HOURS_24", "CUSTOM",
                name="shift_type", create_type=False,
            ),
            nullable=False,
            server_default="CUSTOM",
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("hours_per_day", sa.Numeric(4, 1), nullable=True),
        sa.Column("number_of_days", sa.Integer(), nullable=True),
        sa.Column("custom_schedule_note", sa.Text(), nullable=True),
        sa.Column(
            "payment_frequency",
            postgresql.ENUM(
                "HOURLY", "DAILY", "WEEKLY", "MONTHLY", name="price_unit", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_care_requests_patient_id", "care_requests", ["patient_id"])
    op.create_index("ix_care_requests_status", "care_requests", ["status"])

    op.create_table(
        "care_request_services",
        sa.Column(
            "care_request_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_requests.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "service_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("services.id", ondelete="CASCADE"), primary_key=True,
        ),
    )

    op.create_table(
        "care_request_specialties",
        sa.Column(
            "care_request_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_requests.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "specialty_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True,
        ),
    )

    op.create_table(
        "care_request_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "care_request_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_care_request_requirements_care_request_id",
        "care_request_requirements",
        ["care_request_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_care_request_requirements_care_request_id", table_name="care_request_requirements"
    )
    op.drop_table("care_request_requirements")
    op.drop_table("care_request_specialties")
    op.drop_table("care_request_services")
    op.drop_index("ix_care_requests_status", table_name="care_requests")
    op.drop_index("ix_care_requests_patient_id", table_name="care_requests")
    op.drop_table("care_requests")

    bind = op.get_bind()
    mobility_status_enum.drop(bind, checkfirst=True)
    care_request_status_enum.drop(bind, checkfirst=True)
