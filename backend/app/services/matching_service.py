"""
Rule-based nurse matching engine (Section 21).

Scoring factors and default weights (all admin-configurable via
matching_weights, never hard-coded — see MatchingWeightsRepository):
  - Skills match (specialties + requested services overlap): 30%
  - Experience:                                                20%
  - Location / distance:                                       15%
  - Availability (preferred shift):                            15%
  - Price compatibility with budget:                            10%
  - Rating:                                                      5%
  - Verification status:                                         5%

Hard filters (excluded from results entirely, not just downweighted):
  - Nurse must be approved and not suspended (Section 17)
  - If the request requires verified_nurses_only, unverified nurses are excluded
  - If a preferred_nurse_gender is specified, non-matching nurses are excluded
    (treated as a firm requirement per Section 10, not a soft preference —
    gender preference for hands-on personal care is a legitimate hard need)

This engine only ranks candidates by fit — it never evaluates or comments
on the patient's medical condition (Section 2's healthcare-safety boundary).
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.care_request import CareRequest
from app.models.nurse import Nurse
from app.repositories.care_request_repository import CareRequestRepository
from app.repositories.matching_weight_repository import MatchingWeightsRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.matching import NurseMatchResult
from app.utils.geo import haversine_km

MAX_MATCH_DISTANCE_KM = 50.0


def _skills_score(nurse: Nurse, cr: CareRequest) -> tuple[float, bool]:
    nurse_specialty_ids = {ns.specialty_id for ns in nurse.specialties}
    nurse_service_ids = {ns.service_id for ns in nurse.services}

    required_specialty_ids = {rs.specialty_id for rs in cr.required_specialties}
    required_service_ids = {rs.service_id for rs in cr.required_services}

    scores = []
    if required_specialty_ids:
        scores.append(
            len(nurse_specialty_ids & required_specialty_ids) / len(required_specialty_ids)
        )
    if required_service_ids:
        scores.append(len(nurse_service_ids & required_service_ids) / len(required_service_ids))

    if not scores:
        return 1.0, False
    score = sum(scores) / len(scores)
    return score, score >= 0.5


def _experience_score(nurse: Nurse, cr: CareRequest) -> tuple[float, bool]:
    if not cr.min_experience_years:
        return 1.0, False
    if nurse.experience_years >= cr.min_experience_years:
        return 1.0, True
    return max(0.0, nurse.experience_years / cr.min_experience_years), False


def _location_score(nurse: Nurse, cr: CareRequest) -> tuple[float, float | None]:
    """Returns (score, distance_km). distance_km is None when coordinates
    aren't available for one or both sides, in which case we fall back to
    a coarse governorate/city comparison."""
    n_loc, r_loc = nurse.location, cr.location
    if n_loc and r_loc and n_loc.latitude is not None and n_loc.longitude is not None \
            and r_loc.latitude is not None and r_loc.longitude is not None:
        distance = haversine_km(n_loc.latitude, n_loc.longitude, r_loc.latitude, r_loc.longitude)
        score = max(0.0, 1.0 - (distance / MAX_MATCH_DISTANCE_KM))
        return score, round(distance, 1)

    if n_loc and r_loc:
        if n_loc.city == r_loc.city and n_loc.governorate == r_loc.governorate:
            return 0.8, None
        if n_loc.governorate == r_loc.governorate:
            return 0.5, None
    return 0.2, None


def _availability_score(nurse: Nurse, cr: CareRequest) -> tuple[float, bool]:
    from app.models.nurse import ShiftType

    if cr.preferred_shift == ShiftType.CUSTOM:
        return 1.0, False
    matches = any(slot.shift_type == cr.preferred_shift for slot in nurse.availability_slots)
    return (1.0, True) if matches else (0.4, False)


def _price_score(nurse: Nurse, cr: CareRequest) -> tuple[float, float | None]:
    """Returns (score, estimated_price) using the nurse's price for a
    requested service in the same payment frequency as the request, if any."""
    candidates = [
        ns for ns in nurse.services
        if ns.service_id in {rs.service_id for rs in cr.required_services}
        and ns.price_unit == cr.payment_frequency
    ]
    if not candidates:
        return 0.5, None

    price = float(min(c.price for c in candidates))
    budget_min = float(cr.budget_min) if cr.budget_min is not None else None
    budget_max = float(cr.budget_max) if cr.budget_max is not None else None

    if budget_min is None and budget_max is None:
        return 0.5, price
    if budget_max is not None and price > budget_max:
        overage_ratio = (price - budget_max) / budget_max
        return max(0.0, 1.0 - overage_ratio), price
    if budget_min is not None and price < budget_min:
        return 1.0, price  # cheaper than expected is still good for the patient
    return 1.0, price


def _rating_score(nurse: Nurse) -> float:
    return float(nurse.average_rating) / 5.0


def _verification_score(nurse: Nurse) -> float:
    flags = [nurse.identity_verified, nurse.qualification_verified, nurse.experience_verified]
    return sum(flags) / len(flags)


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.care_requests = CareRequestRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.weights_repo = MatchingWeightsRepository(db)

    async def get_matches(
        self, user_id: uuid.UUID, care_request_id: uuid.UUID, limit: int = 20
    ) -> list[NurseMatchResult]:
        cr = await self.care_requests.get_by_id(care_request_id)
        if not cr:
            raise NotFoundError("Care request not found")

        patient = await self.patients.get_by_user_id(user_id)
        if not patient or cr.patient_id != patient.id:
            raise ForbiddenError("You do not have access to this care request")

        weights = await self.weights_repo.get_active()
        candidates = await self.nurses.list_approved_candidates()

        results: list[NurseMatchResult] = []
        for nurse in candidates:
            if cr.verified_nurses_only and not nurse.is_fully_verified:
                continue
            if cr.preferred_nurse_gender and nurse.gender != cr.preferred_nurse_gender:
                continue

            skills, skills_hit = _skills_score(nurse, cr)
            experience, experience_hit = _experience_score(nurse, cr)
            location, distance_km = _location_score(nurse, cr)
            availability, availability_hit = _availability_score(nurse, cr)
            price, estimated_price = _price_score(nurse, cr)
            rating = _rating_score(nurse)
            verification = _verification_score(nurse)

            total = (
                skills * float(weights.skills_weight)
                + experience * float(weights.experience_weight)
                + location * float(weights.location_weight)
                + availability * float(weights.availability_weight)
                + price * float(weights.price_weight)
                + rating * float(weights.rating_weight)
                + verification * float(weights.verification_weight)
            )
            match_score = round(total * 100, 1)

            reasons = []
            if skills_hit:
                reasons.append("Matches required specialties/services")
            if experience_hit:
                reasons.append("Meets minimum experience requirement")
            if distance_km is not None and distance_km <= MAX_MATCH_DISTANCE_KM:
                reasons.append(f"Within {round(distance_km)} km of requested location")
            elif location >= 0.8:
                reasons.append("Within preferred location")
            if availability_hit:
                reasons.append("Available during requested shift")
            if price >= 0.9 and estimated_price is not None:
                reasons.append("Budget compatible")
            if nurse.is_fully_verified:
                reasons.append("Fully verified nurse")

            results.append(
                NurseMatchResult(
                    nurse_id=nurse.id,
                    full_name=nurse.full_name,
                    professional_title=nurse.professional_title,
                    is_verified=nurse.is_fully_verified,
                    experience_years=nurse.experience_years,
                    specialties=[ns.specialty.name_en for ns in nurse.specialties],
                    average_rating=float(nurse.average_rating),
                    review_count=nurse.review_count,
                    governorate=nurse.location.governorate if nurse.location else None,
                    city=nurse.location.city if nurse.location else None,
                    match_score=match_score,
                    distance_km=distance_km,
                    estimated_price=estimated_price,
                    payment_frequency=cr.payment_frequency.value if estimated_price else None,
                    matching_reasons=reasons,
                )
            )

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:limit]
