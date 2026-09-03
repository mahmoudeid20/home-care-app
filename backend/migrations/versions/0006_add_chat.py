"""add conversations and messages tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

message_type_enum = postgresql.ENUM("TEXT", "IMAGE", "FILE", name="message_type")


def upgrade() -> None:
    bind = op.get_bind()
    message_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "nurse_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "booking_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("patient_id", "nurse_id", name="uq_conversation_patient_nurse"),
    )
    op.create_index("ix_conversations_patient_id", "conversations", ["patient_id"])
    op.create_index("ix_conversations_nurse_id", "conversations", ["nurse_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "sender_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "message_type",
            postgresql.ENUM("TEXT", "IMAGE", "FILE", name="message_type", create_type=False),
            nullable=False,
            server_default="TEXT",
        ),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("attachment_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_nurse_id", table_name="conversations")
    op.drop_index("ix_conversations_patient_id", table_name="conversations")
    op.drop_table("conversations")

    bind = op.get_bind()
    message_type_enum.drop(bind, checkfirst=True)
