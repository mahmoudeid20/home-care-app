"""add profiles: locations, specialties, services, patients, nurses

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

nurse_gender_enum = postgresql.ENUM("MALE", "FEMALE", name="nurse_gender")
price_unit_enum = postgresql.ENUM("HOURLY", "DAILY", "WEEKLY", "MONTHLY", name="price_unit")
shift_type_enum = postgresql.ENUM(
    "MORNING", "EVENING", "NIGHT", "HOURS_24", "CUSTOM", name="shift_type"
)
document_type_enum = postgresql.ENUM(
    "NATIONAL_ID",
    "NURSING_CERTIFICATE",
    "GRADUATION_CERTIFICATE",
    "EXPERIENCE_CERTIFICATE",
    "OTHER",
    name="document_type",
)
document_status_enum = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", name="document_status")


def upgrade() -> None:
    bind = op.get_bind()
    nurse_gender_enum.create(bind, checkfirst=True)
    price_unit_enum.create(bind, checkfirst=True)
    shift_type_enum.create(bind, checkfirst=True)
    document_type_enum.create(bind, checkfirst=True)
    document_status_enum.create(bind, checkfirst=True)

    # --- locations ---
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("governorate", sa.String(100), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("area", sa.String(150), nullable=True),
        sa.Column("address_line", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_locations_governorate", "locations", ["governorate"])

    # --- specialties ---
    op.create_table(
        "specialties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name_en", sa.String(150), nullable=False, unique=True),
        sa.Column("name_ar", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- services ---
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name_en", sa.String(150), nullable=False, unique=True),
        sa.Column("name_ar", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- patients ---
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="ar"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- nurses ---
    op.create_table(
        "nurses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("professional_title", sa.String(150), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("gender", postgresql.ENUM("MALE", "FEMALE", name="nurse_gender", create_type=False), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("qualification_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("experience_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_nurses_is_approved", "nurses", ["is_approved"])

    # --- nurse_specialties ---
    op.create_table(
        "nurse_specialties",
        sa.Column("nurse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nurses.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("specialty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("nurse_id", "specialty_id", name="uq_nurse_specialty"),
    )

    # --- nurse_services ---
    op.create_table(
        "nurse_services",
        sa.Column("nurse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nurses.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_unit", postgresql.ENUM("HOURLY", "DAILY", "WEEKLY", "MONTHLY", name="price_unit", create_type=False), nullable=False),
        sa.UniqueConstraint("nurse_id", "service_id", name="uq_nurse_service"),
    )

    # --- nurse_availability ---
    op.create_table(
        "nurse_availability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nurse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=True),
        sa.Column("shift_type", postgresql.ENUM("MORNING", "EVENING", "NIGHT", "HOURS_24", "CUSTOM", name="shift_type", create_type=False), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
    )
    op.create_index("ix_nurse_availability_nurse_id", "nurse_availability", ["nurse_id"])

    # --- nurse_documents ---
    op.create_table(
        "nurse_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nurse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", postgresql.ENUM("NATIONAL_ID", "NURSING_CERTIFICATE", "GRADUATION_CERTIFICATE", "EXPERIENCE_CERTIFICATE", "OTHER", name="document_type", create_type=False), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "APPROVED", "REJECTED", name="document_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_nurse_documents_nurse_id", "nurse_documents", ["nurse_id"])
    op.create_index("ix_nurse_documents_status", "nurse_documents", ["status"])


def downgrade() -> None:
    op.drop_table("nurse_documents")
    op.drop_table("nurse_availability")
    op.drop_table("nurse_services")
    op.drop_table("nurse_specialties")
    op.drop_index("ix_nurses_is_approved", table_name="nurses")
    op.drop_table("nurses")
    op.drop_table("patients")
    op.drop_table("services")
    op.drop_table("specialties")
    op.drop_index("ix_locations_governorate", table_name="locations")
    op.drop_table("locations")

    bind = op.get_bind()
    document_status_enum.drop(bind, checkfirst=True)
    document_type_enum.drop(bind, checkfirst=True)
    shift_type_enum.drop(bind, checkfirst=True)
    price_unit_enum.drop(bind, checkfirst=True)
    nurse_gender_enum.drop(bind, checkfirst=True)
