import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _full_booking_setup(client, seed_lookup, db_session, suffix):
    patient_token = await register_and_get_token(client, f"bookpatient{suffix}@example.com", "PATIENT")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    await client.post("/api/v1/patients/me", headers=patient_headers, json={"full_name": "FM"})

    cr_payload = {
        "patient_name": "Someone",
        "patient_age": 65,
        "patient_gender": "MALE",
        "medical_condition": "Needs daily nursing care.",
        "mobility_status": "NEEDS_ASSISTANCE",
        "service_ids": [str(seed_lookup["service_general"])],
        "location": {"governorate": "Cairo", "city": "Maadi"},
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "hours_per_day": 8,
        "payment_frequency": "MONTHLY",
    }
    cr_resp = await client.post("/api/v1/care-requests", headers=patient_headers, json=cr_payload)
    cr_id = cr_resp.json()["id"]

    nurse_token = await register_and_get_token(client, f"booknurse{suffix}@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers,
        json={"full_name": "Nurse", "gender": "FEMALE", "experience_years": 5},
    )
    nurse_id = nurse_resp.json()["id"]

    import uuid as uuid_module
    from app.models.nurse import Nurse

    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    app_resp = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    app_id = app_resp.json()["id"]

    accept_resp = await client.post(f"/api/v1/applications/{app_id}/accept", headers=nurse_headers)
    booking_id = accept_resp.json()["id"]

    return patient_headers, nurse_headers, booking_id, cr_id


async def test_booking_starts_accepted(client, seed_lookup, db_session):
    _p, _n, booking_id, _cr = await _full_booking_setup(client, seed_lookup, db_session, "1")
    assert booking_id is not None


async def test_full_happy_path_lifecycle(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, cr_id = await _full_booking_setup(
        client, seed_lookup, db_session, "2"
    )

    confirm_resp = await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    start_resp = await client.post(f"/api/v1/bookings/{booking_id}/start", headers=nurse_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "ACTIVE"

    complete_resp = await client.post(f"/api/v1/bookings/{booking_id}/complete", headers=nurse_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"


async def test_nurse_cannot_confirm_booking(client, seed_lookup, db_session):
    _p, nurse_headers, booking_id, _cr = await _full_booking_setup(client, seed_lookup, db_session, "3")
    resp = await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=nurse_headers)
    assert resp.status_code == 403


async def test_patient_cannot_start_booking(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, _cr = await _full_booking_setup(
        client, seed_lookup, db_session, "4"
    )
    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    resp = await client.post(f"/api/v1/bookings/{booking_id}/start", headers=patient_headers)
    assert resp.status_code == 403


async def test_cannot_start_before_confirm(client, seed_lookup, db_session):
    _p, nurse_headers, booking_id, _cr = await _full_booking_setup(client, seed_lookup, db_session, "5")
    resp = await client.post(f"/api/v1/bookings/{booking_id}/start", headers=nurse_headers)
    assert resp.status_code == 422


async def test_cannot_complete_before_active(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, _cr = await _full_booking_setup(
        client, seed_lookup, db_session, "6"
    )
    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    resp = await client.post(f"/api/v1/bookings/{booking_id}/complete", headers=nurse_headers)
    assert resp.status_code == 422


async def test_cancel_reopens_care_request(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, cr_id = await _full_booking_setup(
        client, seed_lookup, db_session, "7"
    )

    cr_before = await client.get(f"/api/v1/care-requests/{cr_id}", headers=patient_headers)
    assert cr_before.json()["status"] == "MATCHED"

    cancel_resp = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=patient_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    cr_after = await client.get(f"/api/v1/care-requests/{cr_id}", headers=patient_headers)
    assert cr_after.json()["status"] == "OPEN"


async def test_cannot_cancel_active_booking(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, _cr = await _full_booking_setup(
        client, seed_lookup, db_session, "8"
    )
    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    await client.post(f"/api/v1/bookings/{booking_id}/start", headers=nurse_headers)

    resp = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=patient_headers)
    assert resp.status_code == 422


async def test_nurse_can_also_cancel(client, seed_lookup, db_session):
    _p, nurse_headers, booking_id, _cr = await _full_booking_setup(client, seed_lookup, db_session, "9")
    resp = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=nurse_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


async def test_get_booking_forbidden_for_third_party(client, seed_lookup, db_session):
    _p, _n, booking_id, _cr = await _full_booking_setup(client, seed_lookup, db_session, "10")
    intruder_token = await register_and_get_token(client, "bookintruder@example.com", "PATIENT")
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=intruder_headers)
    assert resp.status_code == 403


async def test_list_my_bookings_patient_and_nurse(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id, _cr = await _full_booking_setup(
        client, seed_lookup, db_session, "11"
    )
    patient_list = await client.get("/api/v1/bookings", headers=patient_headers)
    assert patient_list.status_code == 200
    assert len(patient_list.json()) == 1

    nurse_list = await client.get("/api/v1/bookings", headers=nurse_headers)
    assert nurse_list.status_code == 200
    assert len(nurse_list.json()) == 1
