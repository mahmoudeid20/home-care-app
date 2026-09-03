import uuid

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.nurse import (
    DocumentStatus,
    Gender,
    Nurse,
    NurseAvailability,
    NurseDocument,
    NurseService,
    NurseSpecialty,
    PriceUnit,
    ShiftType,
)


def _nurse_load_options():
    return (
        selectinload(Nurse.location),
        selectinload(Nurse.specialties).selectinload(NurseSpecialty.specialty),
        selectinload(Nurse.services).selectinload(NurseService.service),
        selectinload(Nurse.availability_slots),
    )


class NurseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Nurse | None:
        result = await self.db.execute(
            select(Nurse).options(*_nurse_load_options()).where(Nurse.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, nurse_id: uuid.UUID) -> Nurse | None:
        result = await self.db.execute(
            select(Nurse).options(*_nurse_load_options()).where(Nurse.id == nurse_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, **fields) -> Nurse:
        nurse = Nurse(user_id=user_id, **fields)
        self.db.add(nurse)
        await self.db.flush()
        # Only refresh server-generated columns (created_at/updated_at).
        # A full refresh() would expire relationship attributes too, and a
        # brand-new object's relationships haven't been touched yet, so any
        # later access (e.g. iterating nurse.specialties) would attempt an
        # implicit lazy load — which raises MissingGreenlet in async
        # SQLAlchemy. Scoping the refresh avoids that entirely.
        await self.db.refresh(nurse, attribute_names=["created_at", "updated_at"])
        return nurse

    async def replace_specialties(self, nurse: Nurse, specialty_ids: list[uuid.UUID]) -> None:
        # Delete via an explicit statement rather than iterating
        # nurse.specialties, which would trigger an implicit (sync) lazy
        # load if the relationship hasn't been eagerly loaded on this
        # instance yet — see the note in create() above.
        await self.db.execute(delete(NurseSpecialty).where(NurseSpecialty.nurse_id == nurse.id))
        await self.db.flush()
        for specialty_id in specialty_ids:
            self.db.add(NurseSpecialty(nurse_id=nurse.id, specialty_id=specialty_id))
        await self.db.flush()

    async def replace_services(self, nurse: Nurse, services: list[dict]) -> None:
        await self.db.execute(delete(NurseService).where(NurseService.nurse_id == nurse.id))
        await self.db.flush()
        for svc in services:
            self.db.add(
                NurseService(
                    nurse_id=nurse.id,
                    service_id=svc["service_id"],
                    price=svc["price"],
                    price_unit=svc["price_unit"],
                )
            )
        await self.db.flush()

    async def replace_availability(self, nurse: Nurse, slots: list[dict]) -> None:
        await self.db.execute(
            delete(NurseAvailability).where(NurseAvailability.nurse_id == nurse.id)
        )
        await self.db.flush()
        for slot in slots:
            self.db.add(NurseAvailability(nurse_id=nurse.id, **slot))
        await self.db.flush()

    async def add_document(
        self, nurse_id: uuid.UUID, document_type, file_url: str
    ) -> NurseDocument:
        doc = NurseDocument(nurse_id=nurse_id, document_type=document_type, file_url=file_url)
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def list_documents(self, nurse_id: uuid.UUID) -> list[NurseDocument]:
        result = await self.db.execute(
            select(NurseDocument).where(NurseDocument.nurse_id == nurse_id)
        )
        return list(result.scalars().all())

    async def get_document_by_id(self, document_id: uuid.UUID) -> NurseDocument | None:
        return await self.db.get(NurseDocument, document_id)

    async def set_document_status(
        self,
        document: NurseDocument,
        status: DocumentStatus,
        reviewed_by: uuid.UUID,
        rejection_reason: str | None = None,
    ) -> None:
        document.status = status
        document.reviewed_by = reviewed_by
        document.rejection_reason = rejection_reason
        await self.db.flush()

    async def set_approval(self, nurse: Nurse, is_approved: bool) -> None:
        nurse.is_approved = is_approved
        await self.db.flush()

    async def set_suspended(self, nurse: Nurse, is_suspended: bool) -> None:
        nurse.is_suspended = is_suspended
        await self.db.flush()

    async def list_all_admin(
        self,
        is_approved: bool | None = None,
        pending_verification: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Nurse]:
        """
        Unlike `search()` (marketplace-facing, only approved/non-suspended
        nurses), this includes every nurse regardless of approval state -
        admins need to see pending/rejected ones too (Section 26/28).
        """
        stmt = select(Nurse).options(*_nurse_load_options())
        if is_approved is not None:
            stmt = stmt.where(Nurse.is_approved.is_(is_approved))
        if pending_verification:
            stmt = stmt.where(
                (Nurse.identity_verified.is_(False))
                | (Nurse.qualification_verified.is_(False))
                | (Nurse.experience_verified.is_(False))
            )
        stmt = stmt.order_by(Nurse.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        gender: Gender | None = None,
        min_experience_years: int | None = None,
        specialty_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        payment_frequency: PriceUnit | None = None,
        shift_type: ShiftType | None = None,
        verified_only: bool = False,
        governorate: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Nurse]:
        """
        DB-level filtering for the nurse marketplace (Section 15):
        "Filters must be implemented efficiently at the database/API level.
        Do not retrieve thousands of nurses and filter them only on the
        mobile device."

        Only approved, non-suspended nurses are ever returned — an
        unapproved nurse is not yet "fully active" (Section 17).
        """
        stmt = select(Nurse).options(*_nurse_load_options()).where(
            Nurse.is_approved.is_(True), Nurse.is_suspended.is_(False)
        )

        if gender is not None:
            stmt = stmt.where(Nurse.gender == gender)
        if min_experience_years is not None:
            stmt = stmt.where(Nurse.experience_years >= min_experience_years)
        if min_rating is not None:
            stmt = stmt.where(Nurse.average_rating >= min_rating)
        if verified_only:
            stmt = stmt.where(
                Nurse.identity_verified.is_(True),
                Nurse.qualification_verified.is_(True),
                Nurse.experience_verified.is_(True),
            )

        if specialty_id is not None:
            stmt = stmt.join(NurseSpecialty, NurseSpecialty.nurse_id == Nurse.id).where(
                NurseSpecialty.specialty_id == specialty_id
            )

        if price_min is not None or price_max is not None or payment_frequency is not None:
            price_conditions = []
            if price_min is not None:
                price_conditions.append(NurseService.price >= price_min)
            if price_max is not None:
                price_conditions.append(NurseService.price <= price_max)
            if payment_frequency is not None:
                price_conditions.append(NurseService.price_unit == payment_frequency)
            stmt = stmt.join(NurseService, NurseService.nurse_id == Nurse.id).where(
                and_(*price_conditions)
            )

        if shift_type is not None:
            stmt = stmt.join(
                NurseAvailability, NurseAvailability.nurse_id == Nurse.id
            ).where(NurseAvailability.shift_type == shift_type)

        if governorate is not None:
            from app.models.location import Location  # local import avoids a cycle

            stmt = stmt.join(Location, Location.id == Nurse.location_id).where(
                Location.governorate == governorate
            )

        stmt = stmt.distinct().order_by(Nurse.average_rating.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_approved_candidates(self) -> list[Nurse]:
        """
        All approved, non-suspended nurses — the candidate pool for the
        matching engine (Section 21). Filtering by request-specific
        criteria (specialty overlap, shift, etc.) happens in the scoring
        step itself so partial matches can still be ranked and returned,
        rather than being excluded outright by a DB WHERE clause.
        """
        stmt = (
            select(Nurse)
            .options(*_nurse_load_options())
            .where(Nurse.is_approved.is_(True), Nurse.is_suspended.is_(False))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
