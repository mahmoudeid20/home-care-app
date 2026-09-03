import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _setup_patient(client, email):
    token = await register_and_get_token(client, email, "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/patients/me", headers=headers, json={"full_name": "FM"})
    return headers


async def _setup_approved_nurse(client, email, db_session):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/nurses/me", headers=headers,
        json={"full_name": "Notif Nurse", "gender": "FEMALE", "experience_years": 4},
    )
    nurse_id = resp.json()["id"]

    import uuid as uuid_module
    from app.models.nurse import Nurse

    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    return headers, nurse_id


async def test_new_request_notifies_nurse(client, seed_lookup, db_session):
    patient_headers = await _setup_patient(client, "notifpatient1@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "notifnurse1@example.com", db_session)

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 60, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]

    await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )

    resp = await client.get("/api/v1/notifications", headers=nurse_headers)
    assert resp.status_code == 200
    notifications = resp.json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "NEW_REQUEST"
    assert notifications[0]["read_at"] is None


async def test_accept_notifies_patient_and_rejected_nurses(client, seed_lookup, db_session):
    patient_headers = await _setup_patient(client, "notifpatient2@example.com")
    nurse1_headers, nurse1_id = await _setup_approved_nurse(client, "notifnurse2a@example.com", db_session)
    nurse2_headers, nurse2_id = await _setup_approved_nurse(client, "notifnurse2b@example.com", db_session)

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 60, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]

    app1 = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse1_id},
    )
    await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse2_id},
    )

    await client.post(f"/api/v1/applications/{app1.json()['id']}/accept", headers=nurse1_headers)

    patient_notifs = (await client.get("/api/v1/notifications", headers=patient_headers)).json()
    assert any(n["type"] == "REQUEST_ACCEPTED" for n in patient_notifs)

    nurse2_notifs = (await client.get("/api/v1/notifications", headers=nurse2_headers)).json()
    assert any(n["type"] == "REQUEST_REJECTED" for n in nurse2_notifs)


async def test_booking_confirm_and_cancel_notify_other_party(client, seed_lookup, db_session):
    patient_headers = await _setup_patient(client, "notifpatient3@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "notifnurse3@example.com", db_session)

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 60, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]
    app_resp = await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    accept_resp = await client.post(
        f"/api/v1/applications/{app_resp.json()['id']}/accept", headers=nurse_headers
    )
    booking_id = accept_resp.json()["id"]

    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    nurse_notifs = (await client.get("/api/v1/notifications", headers=nurse_headers)).json()
    assert any(n["type"] == "BOOKING_CONFIRMED" for n in nurse_notifs)

    await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=patient_headers)
    nurse_notifs_after = (await client.get("/api/v1/notifications", headers=nurse_headers)).json()
    assert any(n["type"] == "BOOKING_CANCELLED" for n in nurse_notifs_after)


async def test_new_message_notifies_recipient(client, db_session):
    patient_headers = await _setup_patient(client, "notifpatient4@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "notifnurse4@example.com", db_session)

    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=patient_headers,
        json={"message_type": "TEXT", "content": "Hello"},
    )

    nurse_notifs = (await client.get("/api/v1/notifications", headers=nurse_headers)).json()
    assert any(n["type"] == "NEW_MESSAGE" for n in nurse_notifs)


async def test_unread_count_and_mark_read(client, seed_lookup, db_session):
    patient_headers = await _setup_patient(client, "notifpatient5@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "notifnurse5@example.com", db_session)

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 60, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]
    await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )

    unread_resp = await client.get("/api/v1/notifications/unread-count", headers=nurse_headers)
    assert unread_resp.json()["unread_count"] == 1

    notifs = (await client.get("/api/v1/notifications", headers=nurse_headers)).json()
    notif_id = notifs[0]["id"]

    read_resp = await client.post(f"/api/v1/notifications/{notif_id}/read", headers=nurse_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["read_at"] is not None

    unread_after = await client.get("/api/v1/notifications/unread-count", headers=nurse_headers)
    assert unread_after.json()["unread_count"] == 0


async def test_cannot_mark_others_notification_read(client, seed_lookup, db_session):
    patient_headers = await _setup_patient(client, "notifpatient6@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "notifnurse6@example.com", db_session)

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Patient X", "patient_age": 60, "patient_gender": "MALE",
            "medical_condition": "General care.", "mobility_status": "INDEPENDENT",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]
    await client.post(
        "/api/v1/applications", headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    notifs = (await client.get("/api/v1/notifications", headers=nurse_headers)).json()
    notif_id = notifs[0]["id"]

    resp = await client.post(f"/api/v1/notifications/{notif_id}/read", headers=patient_headers)
    assert resp.status_code == 403
