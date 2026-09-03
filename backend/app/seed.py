"""
Development seed data (Section 40): "10 nurses, 5 patients, multiple
specialties, multiple services, different prices, different locations,
different ratings, different availability states, several care requests,
several bookings. This will allow the application to be tested
immediately."

Idempotent: checks for a marker record (the admin account) before doing
anything, so re-running this against an already-seeded database is a
no-op rather than crashing on unique-constraint violations.

Run with:  python -m app.seed
"""
import asyncio
import random
from datetime import date, time, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.application import Application, ApplicationStatus
from app.models.booking import Booking, BookingStatus
from app.models.care_request import (
    CareRequest,
    CareRequestService,
    CareRequestSpecialty,
    CareRequestStatus,
    MobilityStatus,
)
from app.models.location import Location
from app.models.nurse import (
    Gender,
    Nurse,
    NurseAvailability,
    NurseService,
    NurseSpecialty,
    PriceUnit,
    ShiftType,
)
from app.models.patient import Patient
from app.models.review import Review
from app.models.service import Service
from app.models.specialty import Specialty
from app.models.user import User, UserRole

SPECIALTIES = [
    ("General Nursing", "تمريض عام"),
    ("Elderly Care", "رعاية المسنين"),
    ("Post-operative Care", "رعاية ما بعد الجراحة"),
    ("Wound Care", "رعاية الجروح"),
    ("Chronic Care Support", "رعاية الأمراض المزمنة"),
]

SERVICES = [
    ("General Nursing", "تمريض عام"),
    ("Elderly Care", "رعاية المسنين"),
    ("Post-operative Care", "رعاية ما بعد الجراحة"),
    ("Wound Care", "رعاية الجروح"),
    ("Medication Assistance", "المساعدة في الأدوية"),
    ("Injection Assistance", "المساعدة في الحقن"),
    ("Vital Signs Monitoring", "مراقبة العلامات الحيوية"),
    ("Bedridden Patient Care", "رعاية المرضى طريحي الفراش"),
    ("Chronic Care Support", "رعاية الأمراض المزمنة"),
    ("Other", "أخرى"),
]

LOCATIONS = [
    ("Cairo", "Nasr City", "Zone 1", 30.0561, 31.3429),
    ("Cairo", "Maadi", "Degla", 29.9603, 31.2508),
    ("Cairo", "Heliopolis", "Korba", 30.0906, 31.3244),
    ("Giza", "Dokki", None, 30.0382, 31.2122),
    ("Giza", "6th of October", None, 29.9660, 30.9333),
    ("Alexandria", "Smouha", None, 31.2089, 29.9497),
]

NURSE_NAMES = [
    ("Ahmed Mohamed", Gender.MALE),
    ("Fatma Ali", Gender.FEMALE),
    ("Mahmoud Hassan", Gender.MALE),
    ("Nourhan Ibrahim", Gender.FEMALE),
    ("Youssef Adel", Gender.MALE),
    ("Mariam Sami", Gender.FEMALE),
    ("Omar Khaled", Gender.MALE),
    ("Salma Tarek", Gender.FEMALE),
    ("Karim Fathy", Gender.MALE),
    ("Heba Nabil", Gender.FEMALE),
]

PATIENT_NAMES = [
    "Layla Mostafa",
    "Hassan Ezzat",
    "Dina Farouk",
    "Amr Shawky",
    "Rania Gamal",
]


async def _get_or_create_location(db, session_locations, gov, city, area, lat, lng) -> Location:
    key = (gov, city)
    if key in session_locations:
        return session_locations[key]
    loc = Location(governorate=gov, city=city, area=area, latitude=lat, longitude=lng)
    db.add(loc)
    await db.flush()
    session_locations[key] = loc
    return loc


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing_admin = await db.execute(
            select(User).where(User.email == "admin@homecare.example")
        )
        if existing_admin.scalar_one_or_none():
            print("Seed data already present (admin@homecare.example exists) - skipping.")
            return

        specialty_rows = [Specialty(name_en=en, name_ar=ar) for en, ar in SPECIALTIES]
        service_rows = [Service(name_en=en, name_ar=ar) for en, ar in SERVICES]
        db.add_all(specialty_rows + service_rows)
        await db.flush()

        admin = User(
            email="admin@homecare.example",
            password_hash=hash_password("AdminPass123"),
            role=UserRole.ADMIN,
        )
        db.add(admin)

        session_locations = {}
        for gov, city, area, lat, lng in LOCATIONS:
            await _get_or_create_location(db, session_locations, gov, city, area, lat, lng)
        location_list = list(session_locations.values())

        nurses = []
        for i, (name, gender) in enumerate(NURSE_NAMES):
            user = User(
                email=f"nurse{i+1}@homecare.example",
                password_hash=hash_password("NursePass123"),
                role=UserRole.NURSE,
            )
            db.add(user)
            await db.flush()

            loc = location_list[i % len(location_list)]
            experience_years = 1 + (i * 2) % 15
            is_approved = i < 7
            is_verified = is_approved

            nurse = Nurse(
                user_id=user.id,
                full_name=name,
                professional_title="Registered Nurse",
                bio=f"{name} has {experience_years} years of home-care nursing experience.",
                gender=gender,
                experience_years=experience_years,
                education="Bachelor of Nursing, Cairo University",
                location_id=loc.id,
                identity_verified=is_verified,
                qualification_verified=is_verified,
                experience_verified=is_verified,
                is_approved=is_approved,
                average_rating=0,
                review_count=0,
            )
            db.add(nurse)
            await db.flush()

            chosen_specialties = random.sample(specialty_rows, k=random.randint(1, 3))
            for sp in chosen_specialties:
                db.add(NurseSpecialty(nurse_id=nurse.id, specialty_id=sp.id))

            chosen_services = random.sample(service_rows, k=random.randint(1, 2))
            for svc in chosen_services:
                db.add(
                    NurseService(
                        nurse_id=nurse.id,
                        service_id=svc.id,
                        price=random.choice([6000, 8000, 10000, 12000, 15000, 18000]),
                        price_unit=PriceUnit.MONTHLY,
                    )
                )

            shift = random.choice(list(ShiftType))
            db.add(
                NurseAvailability(
                    nurse_id=nurse.id,
                    shift_type=shift,
                    start_time=time(8, 0) if shift == ShiftType.MORNING else time(20, 0),
                    end_time=time(16, 0) if shift == ShiftType.MORNING else time(4, 0),
                )
            )

            nurses.append(nurse)

        patients = []
        for i, name in enumerate(PATIENT_NAMES):
            user = User(
                email=f"patient{i+1}@homecare.example",
                password_hash=hash_password("PatientPass123"),
                role=UserRole.PATIENT,
            )
            db.add(user)
            await db.flush()

            loc = location_list[i % len(location_list)]
            patient = Patient(
                user_id=user.id,
                full_name=name,
                location_id=loc.id,
                preferred_language="ar" if i % 2 == 0 else "en",
            )
            db.add(patient)
            await db.flush()
            patients.append(patient)

        await db.flush()

        today = date.today()
        care_requests = []
        cr_configs = [
            ("Father", 72, Gender.MALE, MobilityStatus.NEEDS_ASSISTANCE, CareRequestStatus.OPEN),
            ("Mother", 68, Gender.FEMALE, MobilityStatus.INDEPENDENT, CareRequestStatus.OPEN),
            ("Grandfather", 80, Gender.MALE, MobilityStatus.BEDRIDDEN, CareRequestStatus.MATCHED),
            ("Uncle", 55, Gender.MALE, MobilityStatus.WHEELCHAIR, CareRequestStatus.CLOSED),
            ("Aunt", 63, Gender.FEMALE, MobilityStatus.NEEDS_ASSISTANCE, CareRequestStatus.CANCELLED),
        ]
        for i, (rel, age, gender, mobility, status) in enumerate(cr_configs):
            patient = patients[i % len(patients)]
            loc = location_list[i % len(location_list)]
            cr = CareRequest(
                patient_id=patient.id,
                status=status,
                patient_name=f"{rel} of {patient.full_name}",
                patient_age=age,
                patient_gender=gender,
                medical_condition="Requires daily assistance with mobility and personal care.",
                mobility_status=mobility,
                location_id=loc.id,
                start_date=today + timedelta(days=3 + i),
                end_date=today + timedelta(days=33 + i),
                hours_per_day=random.choice([8, 12, 24]),
                payment_frequency=PriceUnit.MONTHLY,
                budget_min=8000,
                budget_max=16000,
                preferred_shift=random.choice(list(ShiftType)),
            )
            db.add(cr)
            await db.flush()
            db.add(CareRequestService(care_request_id=cr.id, service_id=service_rows[0].id))
            db.add(CareRequestSpecialty(care_request_id=cr.id, specialty_id=specialty_rows[1].id))
            care_requests.append(cr)

        await db.flush()

        app1 = Application(
            care_request_id=care_requests[2].id,
            nurse_id=nurses[0].id,
            patient_id=care_requests[2].patient_id,
            status=ApplicationStatus.ACCEPTED,
        )
        db.add(app1)
        await db.flush()
        booking1 = Booking(
            care_request_id=care_requests[2].id,
            application_id=app1.id,
            patient_id=care_requests[2].patient_id,
            nurse_id=nurses[0].id,
            status=BookingStatus.REVIEWED,
            start_date=care_requests[2].start_date,
            end_date=care_requests[2].end_date,
            hours_per_day=12,
            payment_frequency=PriceUnit.MONTHLY,
            agreed_price=12000,
        )
        db.add(booking1)
        await db.flush()
        db.add(
            Review(
                booking_id=booking1.id,
                patient_id=booking1.patient_id,
                nurse_id=booking1.nurse_id,
                overall_rating=5,
                professionalism=5,
                communication=4,
                care_quality=5,
                comment="Excellent care, very professional and punctual.",
            )
        )
        # Keep the nurse's denormalized aggregate honest with the review
        # actually created above (same formula ReviewService uses), rather
        # than an unrelated random number.
        nurses[0].average_rating = 5.0
        nurses[0].review_count = 1

        app2 = Application(
            care_request_id=care_requests[0].id,
            nurse_id=nurses[1].id,
            patient_id=care_requests[0].patient_id,
            status=ApplicationStatus.ACCEPTED,
        )
        db.add(app2)
        await db.flush()
        db.add(
            Booking(
                care_request_id=care_requests[0].id,
                application_id=app2.id,
                patient_id=care_requests[0].patient_id,
                nurse_id=nurses[1].id,
                status=BookingStatus.ACTIVE,
                start_date=care_requests[0].start_date,
                end_date=care_requests[0].end_date,
                hours_per_day=8,
                payment_frequency=PriceUnit.MONTHLY,
                agreed_price=10000,
            )
        )

        app3 = Application(
            care_request_id=care_requests[1].id,
            nurse_id=nurses[2].id,
            patient_id=care_requests[1].patient_id,
            status=ApplicationStatus.ACCEPTED,
        )
        db.add(app3)
        await db.flush()
        db.add(
            Booking(
                care_request_id=care_requests[1].id,
                application_id=app3.id,
                patient_id=care_requests[1].patient_id,
                nurse_id=nurses[2].id,
                status=BookingStatus.CONFIRMED,
                start_date=care_requests[1].start_date,
                end_date=care_requests[1].end_date,
                hours_per_day=8,
                payment_frequency=PriceUnit.MONTHLY,
                agreed_price=9000,
            )
        )

        await db.commit()

        print("Seed complete:")
        print(f"  {len(specialty_rows)} specialties, {len(service_rows)} services")
        print(f"  {len(nurses)} nurses (7 approved+verified, 3 pending)")
        print(f"  {len(patients)} patients")
        print(f"  {len(care_requests)} care requests (OPEN/MATCHED/CLOSED/CANCELLED)")
        print("  3 bookings (REVIEWED with a 5-star review, ACTIVE, CONFIRMED)")
        print("  1 admin: admin@homecare.example / AdminPass123")
        print("  Nurse logins: nurse1..nurse10@homecare.example / NursePass123")
        print("  Patient logins: patient1..patient5@homecare.example / PatientPass123")


if __name__ == "__main__":
    asyncio.run(seed())
