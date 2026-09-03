"""
Configurable weights for the rule-based matching engine (Section 21):
"Make the weights configurable. Do not hard-code them throughout the
application."

Implemented as a single-row config table rather than scattering percentages
through the codebase. `get_active()` in the repository creates the Section-21
defaults on first use if no row exists yet, so the engine works out of the
box without requiring a manual admin step first.
"""
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MatchingWeights(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "matching_weights"

    # All weights are fractions that should sum to 1.0 (validated at the
    # API layer on update). Defaults mirror Section 21 exactly.
    skills_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.30, nullable=False)
    experience_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.20, nullable=False)
    location_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.15, nullable=False)
    availability_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.15, nullable=False)
    price_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.10, nullable=False)
    rating_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.05, nullable=False)
    verification_weight: Mapped[float] = mapped_column(Numeric(4, 3), default=0.05, nullable=False)
