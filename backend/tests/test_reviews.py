import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _completed_booking_setup(client, seed_lookup, db_session, suffix):
    patient_token = await register_and_get_token(client, f"revpatient{suffix}@example.com", "PATIENT")
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
        "payment_frequency": "MONTHLY",
    }
    cr_resp = await client.post("/api/v1/care-requests", headers=patient_headers, json=cr_payload)
    cr_id = cr_resp.json()["id"]

    nurse_token = await register_and_get_token(client, f"revnurse{suffix}@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers,
        json={"full_name": "Review Nurse", "gender": "FEMALE", "experience_years": 5},
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

    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    await client.post(f"/api/v1/bookings/{booking_id}/start", headers=nurse_headers)
    await client.post(f"/api/v1/bookings/{booking_id}/complete", headers=nurse_headers)

    return patient_headers, nurse_headers, booking_id, nurse_id


async def test_create_review_success(client, seed_lookup, db_session):
    patient_headers, _nurse_headers, booking_id, nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "1"
    )

    resp = await client.post(
        "/api/v1/reviews",
        headers=patient_headers,
        json={
            "booking_id": booking_id,
            "overall_rating": 5,
            "professionalism": 5,
            "communication": 4,
            "care_quality": 5,
            "comment": "Excellent care, very professional.",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["overall_rating"] == 5
    assert data["nurse_id"] == nurse_id

    booking_resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=patient_headers)
    assert booking_resp.json()["status"] == "REVIEWED"

    nurse_resp = await client.get(f"/api/v1/nurses/{nurse_id}", headers=patient_headers)
    assert nurse_resp.json()["average_rating"] == 5.0
    assert nurse_resp.json()["review_count"] == 1


async def test_duplicate_review_rejected(client, seed_lookup, db_session):
    patient_headers, _nurse_headers, booking_id, _nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "2"
    )
    payload = {
        "booking_id": booking_id,
        "overall_rating": 4,
        "professionalism": 4,
        "communication": 4,
        "care_quality": 4,
    }
    first = await client.post("/api/v1/reviews", headers=patient_headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/reviews", headers=patient_headers, json=payload)
    assert second.status_code == 409


async def test_cannot_review_non_completed_booking(client, seed_lookup, db_session):
    patient_token = await register_and_get_token(client, "revincomplete@example.com", "PATIENT")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    await client.post("/api/v1/patients/me", headers=patient_headers, json={"full_name": "FM"})
    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 50, "patient_gender": "FEMALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]

    nurse_token = await register_and_get_token(client, "revincompletenurse@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers,
        json={"full_name": "Incomplete Nurse", "gender": "MALE"},
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
    accept_resp = await client.post(
        f"/api/v1/applications/{app_resp.json()['id']}/accept", headers=nurse_headers
    )
    booking_id = accept_resp.json()["id"]

    resp = await client.post(
        "/api/v1/reviews",
        headers=patient_headers,
        json={
            "booking_id": booking_id, "overall_rating": 5, "professionalism": 5,
            "communication": 5, "care_quality": 5,
        },
    )
    assert resp.status_code == 422


async def test_only_booking_owner_can_review(client, seed_lookup, db_session):
    _patient_headers, _nurse_headers, booking_id, _nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "3"
    )
    intruder_token = await register_and_get_token(client, "revintruder@example.com", "PATIENT")
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    await client.post("/api/v1/patients/me", headers=intruder_headers, json={"full_name": "Intruder Patient"})

    resp = await client.post(
        "/api/v1/reviews",
        headers=intruder_headers,
        json={
            "booking_id": booking_id, "overall_rating": 1, "professionalism": 1,
            "communication": 1, "care_quality": 1,
        },
    )
    assert resp.status_code == 403


async def test_rating_out_of_range_rejected(client, seed_lookup, db_session):
    patient_headers, _nurse_headers, booking_id, _nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "4"
    )
    resp = await client.post(
        "/api/v1/reviews",
        headers=patient_headers,
        json={
            "booking_id": booking_id, "overall_rating": 6, "professionalism": 5,
            "communication": 5, "care_quality": 5,
        },
    )
    assert resp.status_code == 422


async def test_list_nurse_reviews_public(client, seed_lookup, db_session):
    patient_headers, _nurse_headers, booking_id, nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "5"
    )
    await client.post(
        "/api/v1/reviews",
        headers=patient_headers,
        json={
            "booking_id": booking_id, "overall_rating": 4, "professionalism": 4,
            "communication": 4, "care_quality": 4, "comment": "Good experience.",
        },
    )

    resp = await client.get(f"/api/v1/nurses/{nurse_id}/reviews", headers=patient_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["comment"] == "Good experience."


async def test_average_rating_recomputed_across_multiple_reviews(client, seed_lookup, db_session):
    patient1_headers, nurse_headers, booking1_id, nurse_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "6"
    )
    await client.post(
        "/api/v1/reviews", headers=patient1_headers,
        json={"booking_id": booking1_id, "overall_rating": 5, "professionalism": 5,
              "communication": 5, "care_quality": 5},
    )

    patient2_token = await register_and_get_token(client, "revpatient6b@example.com", "PATIENT")
    patient2_headers = {"Authorization": f"Bearer {patient2_token}"}
    await client.post("/api/v1/patients/me", headers=patient2_headers, json={"full_name": "FM2"})
    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient2_headers,
        json={
            "patient_name": "Patient Y", "patient_age": 55, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr2_id = cr_resp.json()["id"]
    app_resp = await client.post(
        "/api/v1/applications", headers=patient2_headers,
        json={"care_request_id": cr2_id, "nurse_id": nurse_id},
    )
    accept_resp = await client.post(
        f"/api/v1/applications/{app_resp.json()['id']}/accept", headers=nurse_headers
    )
    booking2_id = accept_resp.json()["id"]
    await client.post(f"/api/v1/bookings/{booking2_id}/confirm", headers=patient2_headers)
    await client.post(f"/api/v1/bookings/{booking2_id}/start", headers=nurse_headers)
    await client.post(f"/api/v1/bookings/{booking2_id}/complete", headers=nurse_headers)

    await client.post(
        "/api/v1/reviews", headers=patient2_headers,
        json={"booking_id": booking2_id, "overall_rating": 3, "professionalism": 3,
              "communication": 3, "care_quality": 3},
    )

    nurse_resp = await client.get(f"/api/v1/nurses/{nurse_id}", headers=patient1_headers)
    assert nurse_resp.json()["review_count"] == 2
    assert nurse_resp.json()["average_rating"] == 4.0
