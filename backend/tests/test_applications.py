import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _setup_patient_with_request(client, seed_lookup, email):
    token = await register_and_get_token(client, email, "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/patients/me", headers=headers, json={"full_name": "FM"})
    payload = {
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
        "budget_min": 8000,
        "budget_max": 15000,
    }
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return headers, resp.json()["id"]


async def _setup_approved_nurse(client, seed_lookup, email, db_session, price=12000):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": f"Nurse {email}",
            "gender": "FEMALE",
            "experience_years": 5,
            "services": [
                {"service_id": str(seed_lookup["service_general"]), "price": price, "price_unit": "MONTHLY"}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    nurse_id = resp.json()["id"]

    import uuid as uuid_module
    from app.models.nurse import Nurse

    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    return headers, nurse_id


async def test_send_application_success(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appsend@example.com")
    _, nurse_id = await _setup_approved_nurse(client, seed_lookup, "appnurse1@example.com", db_session)

    resp = await client.post(
        "/api/v1/applications",
        headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id, "message": "Please help my father"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["nurse_id"] == nurse_id


async def test_send_application_duplicate_conflict(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appdup@example.com")
    _, nurse_id = await _setup_approved_nurse(client, seed_lookup, "appnurse2@example.com", db_session)

    payload = {"care_request_id": cr_id, "nurse_id": nurse_id}
    first = await client.post("/api/v1/applications", headers=patient_headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/applications", headers=patient_headers, json=payload)
    assert second.status_code == 409


async def test_send_application_unapproved_nurse_rejected(client, seed_lookup):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appunapproved@example.com")
    nurse_token = await register_and_get_token(client, "unapprovednurse@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers, json={"full_name": "Nurse N", "gender": "MALE"}
    )
    nurse_id = nurse_resp.json()["id"]

    resp = await client.post(
        "/api/v1/applications",
        headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    assert resp.status_code == 422


async def test_send_application_wrong_owner_care_request(client, seed_lookup, db_session):
    _owner_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appowner@example.com")
    intruder_token = await register_and_get_token(client, "appintruder@example.com", "PATIENT")
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    await client.post("/api/v1/patients/me", headers=intruder_headers, json={"full_name": "X"})
    _, nurse_id = await _setup_approved_nurse(client, seed_lookup, "appnurse3@example.com", db_session)

    resp = await client.post(
        "/api/v1/applications",
        headers=intruder_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    assert resp.status_code == 404


async def test_accept_application_creates_booking_and_matches_request(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appaccept@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse4@example.com", db_session, price=12000
    )

    app_resp = await client.post(
        "/api/v1/applications",
        headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    app_id = app_resp.json()["id"]

    accept_resp = await client.post(f"/api/v1/applications/{app_id}/accept", headers=nurse_headers)
    assert accept_resp.status_code == 200, accept_resp.text
    booking = accept_resp.json()
    assert booking["status"] == "ACCEPTED"
    assert booking["nurse_id"] == nurse_id
    assert booking["agreed_price"] == 12000

    # Care request should now be MATCHED.
    cr_resp = await client.get(f"/api/v1/care-requests/{cr_id}", headers=patient_headers)
    assert cr_resp.json()["status"] == "MATCHED"

    # Application itself should now be ACCEPTED.
    sent_resp = await client.get("/api/v1/applications/sent", headers=patient_headers)
    assert sent_resp.json()[0]["status"] == "ACCEPTED"


async def test_accepting_one_application_rejects_others(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appmulti@example.com")
    nurse1_headers, nurse1_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse5@example.com", db_session
    )
    nurse2_headers, nurse2_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse6@example.com", db_session
    )

    app1 = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse1_id},
    )
    app2 = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse2_id},
    )
    app1_id, app2_id = app1.json()["id"], app2.json()["id"]

    accept_resp = await client.post(f"/api/v1/applications/{app1_id}/accept", headers=nurse1_headers)
    assert accept_resp.status_code == 200

    sent_resp = await client.get("/api/v1/applications/sent", headers=patient_headers)
    statuses = {a["id"]: a["status"] for a in sent_resp.json()}
    assert statuses[app1_id] == "ACCEPTED"
    assert statuses[app2_id] == "REJECTED"

    # The second (now auto-rejected) nurse can no longer accept it.
    second_accept = await client.post(f"/api/v1/applications/{app2_id}/accept", headers=nurse2_headers)
    assert second_accept.status_code == 422


async def test_reject_application(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appreject@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse7@example.com", db_session
    )
    app_resp = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    app_id = app_resp.json()["id"]

    reject_resp = await client.post(
        f"/api/v1/applications/{app_id}/reject", headers=nurse_headers, json={"reason": "Fully booked"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"
    assert reject_resp.json()["rejection_reason"] == "Fully booked"


async def test_withdraw_application(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appwithdraw@example.com")
    _nurse_headers, nurse_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse8@example.com", db_session
    )
    app_resp = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    app_id = app_resp.json()["id"]

    withdraw_resp = await client.post(f"/api/v1/applications/{app_id}/withdraw", headers=patient_headers)
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.json()["status"] == "WITHDRAWN"


async def test_nurse_cannot_reject_others_application(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appwrongnurse@example.com")
    _nurse1_headers, nurse1_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse9@example.com", db_session
    )
    nurse2_headers, _nurse2_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse10@example.com", db_session
    )
    app_resp = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse1_id},
    )
    app_id = app_resp.json()["id"]

    resp = await client.post(f"/api/v1/applications/{app_id}/reject", headers=nurse2_headers, json={})
    assert resp.status_code == 403


async def test_received_applications_list(client, seed_lookup, db_session):
    patient_headers, cr_id = await _setup_patient_with_request(client, seed_lookup, "appreceived@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(
        client, seed_lookup, "appnurse11@example.com", db_session
    )
    await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )

    resp = await client.get("/api/v1/applications/received", headers=nurse_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
