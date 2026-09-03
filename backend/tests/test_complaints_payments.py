import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _make_admin(db_session, email="cpadmin@example.com"):
    from app.core.security import create_access_token, hash_password
    from app.models.user import User, UserRole

    admin = User(email=email, password_hash=hash_password("Passw0rd1"), role=UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    token = create_access_token(str(admin.id), UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}, admin


async def test_file_and_list_own_complaint(client):
    token = await register_and_get_token(client, "complainant@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/complaints", headers=headers,
        json={"category": "billing", "description": "I was overcharged for the last booking."},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "OPEN"

    list_resp = await client.get("/api/v1/complaints", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_cannot_view_others_complaint(client):
    token1 = await register_and_get_token(client, "complainant2@example.com", "PATIENT")
    headers1 = {"Authorization": f"Bearer {token1}"}
    create_resp = await client.post(
        "/api/v1/complaints", headers=headers1,
        json={"category": "service", "description": "Nurse arrived late."},
    )
    complaint_id = create_resp.json()["id"]

    token2 = await register_and_get_token(client, "intruder_complaint@example.com", "PATIENT")
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp = await client.get(f"/api/v1/complaints/{complaint_id}", headers=headers2)
    assert resp.status_code == 403


async def test_admin_lists_and_resolves_complaint(client, db_session):
    admin_headers, _admin = await _make_admin(db_session)
    token = await register_and_get_token(client, "complainant3@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/api/v1/complaints", headers=headers,
        json={"category": "other", "description": "General issue with the app."},
    )
    complaint_id = create_resp.json()["id"]

    admin_list = await client.get("/api/v1/admin/complaints", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(c["id"] == complaint_id for c in admin_list.json())

    resolve_resp = await client.patch(
        f"/api/v1/admin/complaints/{complaint_id}", headers=admin_headers,
        json={"status": "RESOLVED", "admin_response": "Issue fixed, thank you for reporting."},
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["admin_response"] == "Issue fixed, thank you for reporting."

    own_resp = await client.get(f"/api/v1/complaints/{complaint_id}", headers=headers)
    assert own_resp.json()["status"] == "RESOLVED"


async def test_nurse_can_also_file_complaint(client):
    token = await register_and_get_token(client, "complainingnurse@example.com", "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/complaints", headers=headers,
        json={"category": "patient_behavior", "description": "Patient was verbally abusive."},
    )
    assert resp.status_code == 201


async def test_non_admin_cannot_list_all_complaints(client):
    token = await register_and_get_token(client, "notadmin_complaints@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/admin/complaints", headers=headers)
    assert resp.status_code == 403


async def _completed_booking_setup(client, seed_lookup, db_session, suffix):
    patient_token = await register_and_get_token(client, f"paypatient{suffix}@example.com", "PATIENT")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    await client.post("/api/v1/patients/me", headers=patient_headers, json={"full_name": "FM"})

    cr_resp = await client.post(
        "/api/v1/care-requests", headers=patient_headers,
        json={
            "patient_name": "Pay Patient", "patient_age": 65, "patient_gender": "MALE",
            "medical_condition": "Needs daily nursing care.", "mobility_status": "NEEDS_ASSISTANCE",
            "service_ids": [str(seed_lookup["service_general"])],
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "start_date": "2026-09-01", "payment_frequency": "MONTHLY",
        },
    )
    cr_id = cr_resp.json()["id"]

    nurse_token = await register_and_get_token(client, f"paynurse{suffix}@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers,
        json={
            "full_name": "Pay Nurse", "gender": "FEMALE", "experience_years": 5,
            "services": [
                {"service_id": str(seed_lookup["service_general"]), "price": 10000, "price_unit": "MONTHLY"}
            ],
        },
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
    await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=patient_headers)
    await client.post(f"/api/v1/bookings/{booking_id}/start", headers=nurse_headers)
    await client.post(f"/api/v1/bookings/{booking_id}/complete", headers=nurse_headers)

    return patient_headers, nurse_headers, booking_id


async def test_payment_created_on_booking_completion(client, seed_lookup, db_session):
    patient_headers, nurse_headers, booking_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "1"
    )

    resp = await client.get(f"/api/v1/bookings/{booking_id}/payment", headers=patient_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["amount"] == 10000
    assert data["platform_commission"] == 1000.0
    assert data["nurse_earnings"] == 9000.0


async def test_nurse_can_also_view_payment(client, seed_lookup, db_session):
    _patient_headers, nurse_headers, booking_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "2"
    )
    resp = await client.get(f"/api/v1/bookings/{booking_id}/payment", headers=nurse_headers)
    assert resp.status_code == 200


async def test_third_party_cannot_view_payment(client, seed_lookup, db_session):
    _patient_headers, _nurse_headers, booking_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "3"
    )
    intruder_token = await register_and_get_token(client, "paymentintruder@example.com", "PATIENT")
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    resp = await client.get(f"/api/v1/bookings/{booking_id}/payment", headers=intruder_headers)
    assert resp.status_code == 403


async def test_admin_marks_payment_paid(client, seed_lookup, db_session):
    admin_headers, _admin = await _make_admin(db_session, "payadmin@example.com")
    patient_headers, _nurse_headers, booking_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "4"
    )
    payment_resp = await client.get(f"/api/v1/bookings/{booking_id}/payment", headers=patient_headers)
    payment_id = payment_resp.json()["id"]

    mark_paid_resp = await client.post(
        f"/api/v1/admin/payments/{payment_id}/mark-paid", headers=admin_headers,
        json={"payment_method": "cash"},
    )
    assert mark_paid_resp.status_code == 200
    assert mark_paid_resp.json()["status"] == "PAID"
    assert mark_paid_resp.json()["payment_method"] == "cash"

    second_attempt = await client.post(
        f"/api/v1/admin/payments/{payment_id}/mark-paid", headers=admin_headers,
        json={"payment_method": "cash"},
    )
    assert second_attempt.status_code == 422


async def test_admin_can_list_payments(client, seed_lookup, db_session):
    admin_headers, _admin = await _make_admin(db_session, "payadmin2@example.com")
    await _completed_booking_setup(client, seed_lookup, db_session, "5")

    resp = await client.get("/api/v1/admin/payments", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_stats_reflect_paid_revenue(client, seed_lookup, db_session):
    admin_headers, _admin = await _make_admin(db_session, "payadmin3@example.com")
    patient_headers, _nurse_headers, booking_id = await _completed_booking_setup(
        client, seed_lookup, db_session, "6"
    )
    payment_resp = await client.get(f"/api/v1/bookings/{booking_id}/payment", headers=patient_headers)
    payment_id = payment_resp.json()["id"]
    await client.post(
        f"/api/v1/admin/payments/{payment_id}/mark-paid", headers=admin_headers,
        json={"payment_method": "cash"},
    )

    stats_resp = await client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats_resp.status_code == 200
    assert stats_resp.json()["total_revenue"] >= 10000
