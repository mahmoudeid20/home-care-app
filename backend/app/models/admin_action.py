"""
Audit log of administrative actions (Section 28: "Maintain an audit log of
administrative actions"). Every mutating admin action - document review,
nurse approval/suspension, user activation, complaint resolution, catalog
edits - writes one row here via AdminActionRepository.record(), so nothing
an admin does is silently unaccountable.
"""
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AdminAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "admin_actions"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    admin = relationship("User", foreign_keys=[admin_id])
