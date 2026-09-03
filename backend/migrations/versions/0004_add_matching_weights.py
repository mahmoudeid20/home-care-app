"""add matching_weights config table

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matching_weights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skills_weight", sa.Numeric(4, 3), nullable=False, server_default="0.30"),
        sa.Column("experience_weight", sa.Numeric(4, 3), nullable=False, server_default="0.20"),
        sa.Column("location_weight", sa.Numeric(4, 3), nullable=False, server_default="0.15"),
        sa.Column("availability_weight", sa.Numeric(4, 3), nullable=False, server_default="0.15"),
        sa.Column("price_weight", sa.Numeric(4, 3), nullable=False, server_default="0.10"),
        sa.Column("rating_weight", sa.Numeric(4, 3), nullable=False, server_default="0.05"),
        sa.Column("verification_weight", sa.Numeric(4, 3), nullable=False, server_default="0.05"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    # No seed row here — MatchingWeightsRepository.get_active() creates the
    # single default row lazily on first use (avoids a dependency on
    # Postgres's pgcrypto/uuid-ossp extensions for gen_random_uuid() in a
    # raw migration INSERT).


def downgrade() -> None:
    op.drop_table("matching_weights")
