"""
Turns raw (untrusted) LLM output into a validated AIExtractionResult.

Every field from the model is treated as untrusted input: enums are
checked against the real allowed values (never passed through blindly),
numeric fields are range-clamped, and specialty/service keywords are
resolved against the actual catalog rather than trusted as IDs. This
keeps the AI firmly in an assistive role -- it can only ever produce a
pre-fill suggestion built from data that already exists in the system,
never something the matching engine or database hasn't already validated
through their normal paths.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.care_request import MobilityStatus
from app.models.nurse import ShiftType
from app.repositories.lookup_repository import LookupRepository
from app.schemas.ai_extraction import AIExtractionResult
from app.services.llm_client import LLMClient, get_llm_client

_VALID_MOBILITY = {m.value for m in MobilityStatus}
_VALID_SHIFT = {s.value for s in ShiftType}
_VALID_GENDER = {"MALE", "FEMALE"}


def _clean_int(value, min_val: int, max_val: int) -> int | None:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if min_val <= n <= max_val else None


def _clean_float(value, min_val: float, max_val: float) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if min_val <= n <= max_val else None


def _clean_enum(value, allowed: set[str]) -> str | None:
    if isinstance(value, str) and value.upper() in allowed:
        return value.upper()
    return None


def _clean_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()][:10]


class AIExtractionService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient | None = None):
        self.db = db
        self.lookup = LookupRepository(db)
        self.llm_client = llm_client if llm_client is not None else get_llm_client()

    async def extract(self, text: str) -> AIExtractionResult:
        if self.llm_client is None:
            raise ValidationAppError(
                "AI requirement extraction is not configured on this server "
                "(no LLM_API_KEY set). Use the manual multi-step form instead.",
                error_code="AI_NOT_CONFIGURED",
            )

        raw = await self.llm_client.extract_requirements(text)
        if not isinstance(raw, dict):
            raw = {}

        specialty_keywords = _clean_str_list(raw.get("required_specialty_keywords"))
        service_keywords = _clean_str_list(raw.get("required_service_keywords"))

        matched_specialty_ids, unmatched_specialties = await self._resolve_specialties(
            specialty_keywords
        )
        matched_service_ids, unmatched_services = await self._resolve_services(service_keywords)

        return AIExtractionResult(
            age=_clean_int(raw.get("age"), 0, 130),
            gender=_clean_enum(raw.get("gender"), _VALID_GENDER),
            patient_type=raw.get("patient_type") if isinstance(raw.get("patient_type"), str) else None,
            duration_days=_clean_int(raw.get("duration_days"), 1, 3650),
            hours_per_day=_clean_float(raw.get("hours_per_day"), 0.5, 24),
            preferred_shift=_clean_enum(raw.get("preferred_shift"), _VALID_SHIFT),
            languages=_clean_str_list(raw.get("languages")),
            mobility_status=_clean_enum(raw.get("mobility_status"), _VALID_MOBILITY),
            matched_specialty_ids=matched_specialty_ids,
            unmatched_specialty_keywords=unmatched_specialties,
            matched_service_ids=matched_service_ids,
            unmatched_service_keywords=unmatched_services,
        )

    async def _resolve_specialties(self, keywords: list[str]) -> tuple[list, list[str]]:
        if not keywords:
            return [], []
        catalog = await self.lookup.list_specialties(active_only=True)
        matched_ids = []
        unmatched = []
        for kw in keywords:
            hit = self._best_match(kw, catalog)
            if hit:
                if hit.id not in matched_ids:
                    matched_ids.append(hit.id)
            else:
                unmatched.append(kw)
        return matched_ids, unmatched

    async def _resolve_services(self, keywords: list[str]) -> tuple[list, list[str]]:
        if not keywords:
            return [], []
        catalog = await self.lookup.list_services(active_only=True)
        matched_ids = []
        unmatched = []
        for kw in keywords:
            hit = self._best_match(kw, catalog)
            if hit:
                if hit.id not in matched_ids:
                    matched_ids.append(hit.id)
            else:
                unmatched.append(kw)
        return matched_ids, unmatched

    @staticmethod
    def _best_match(keyword: str, catalog: list):
        """Simple bidirectional substring match -- good enough for short
        catalog lists (tens of entries, not thousands) and keeps the
        matching logic transparent/auditable rather than a black box."""
        kw_lower = keyword.lower().strip()
        if not kw_lower:
            return None
        for item in catalog:
            name_lower = item.name_en.lower()
            if kw_lower in name_lower or name_lower in kw_lower:
                return item
        return None
