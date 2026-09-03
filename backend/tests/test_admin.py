import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _make_admin(db_session, email="admin@example.com"):
    from app.core.security import create_access_token, hash_password
    from app.models.user import User, UserRole

    admin = User(email=email, password_hash=hash_password("Passw0rd1"), role=UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    token = create_access_token(str(admin.id), UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}, admin


async def _register_nurse_with_docs(client, email):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/nurses/me", headers=headers,
        json={"full_name": "Pending Nurse", "gender": "FEMALE", "experience_years": 3},
    )
    nurse_id = resp.json()["id"]

    doc_ids = {}
    for doc_type in ["NATIONAL_ID", "NURSING_CERTIFICATE", "EXPERIENCE_CERTIFICATE"]:
        doc_resp = await client.post(
            "/api/v1/nurses/me/documents", headers=headers,
            json={"document_type": doc_type, "file_url": f"https://storage.example.com/{doc_type}.pdf"},
        )
        doc_ids[doc_type] = doc_resp.json()["id"]

    return headers, nurse_id, doc_ids


async def test_admin_list_users(client, db_session):
    admin_headers, _admin = await _make_admin(db_session)
    await register_and_get_token(client, "listeduser@example.com", "PATIENT")

    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "listeduser@example.com" in emails


async def test_admin_deactivate_and_activate_user(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin2@example.com")
    token = await register_and_get_token(client, "deactivateme@example.com", "PATIENT")
    user_headers = {"Authorization": f"Bearer {token}"}

    me_resp = await client.get("/api/v1/auth/me", headers=user_headers)
    user_id = me_resp.json()["id"]

    deactivate_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/deactivate", headers=admin_headers, json={"reason": "test"}
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "deactivateme@example.com", "password": "Passw0rd1"}
    )
    assert login_resp.status_code == 401

    activate_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/activate", headers=admin_headers
    )
    assert activate_resp.status_code == 200
    assert activate_resp.json()["is_active"] is True


async def test_non_admin_cannot_list_users(client):
    token = await register_and_get_token(client, "notadminusers@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403


async def test_full_nurse_verification_flow(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin3@example.com")
    nurse_headers, nurse_id, doc_ids = await _register_nurse_with_docs(client, "verifyme@example.com")

    early_approve = await client.post(f"/api/v1/admin/nurses/{nurse_id}/approve", headers=admin_headers)
    assert early_approve.status_code == 422

    docs_resp = await client.get(f"/api/v1/admin/nurses/{nurse_id}/documents", headers=admin_headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) == 3

    for doc_type, doc_id in doc_ids.items():
        approve_resp = await client.post(
            f"/api/v1/admin/nurses/{nurse_id}/documents/{doc_id}/approve", headers=admin_headers
        )
        assert approve_resp.status_code == 200, approve_resp.text
        assert approve_resp.json()["status"] == "APPROVED"

    profile_resp = await client.get("/api/v1/nurses/me", headers=nurse_headers)
    profile = profile_resp.json()
    assert profile["identity_verified"] is True
    assert profile["qualification_verified"] is True
    assert profile["experience_verified"] is True
    assert profile["is_approved"] is False

    approve_resp = await client.post(f"/api/v1/admin/nurses/{nurse_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_approved"] is True

    profile_after = await client.get("/api/v1/nurses/me", headers=nurse_headers)
    assert profile_after.json()["is_approved"] is True

    notifs = await client.get("/api/v1/notifications", headers=nurse_headers)
    assert sum(1 for n in notifs.json() if n["type"] == "DOCUMENT_VERIFICATION_RESULT") == 3


async def test_reject_document_with_reason(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin4@example.com")
    nurse_headers, nurse_id, doc_ids = await _register_nurse_with_docs(client, "rejectme@example.com")

    doc_id = doc_ids["NATIONAL_ID"]
    resp = await client.post(
        f"/api/v1/admin/nurses/{nurse_id}/documents/{doc_id}/reject",
        headers=admin_headers,
        json={"reason": "Blurry image, please re-upload"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"
    assert resp.json()["rejection_reason"] == "Blurry image, please re-upload"

    profile = (await client.get("/api/v1/nurses/me", headers=nurse_headers)).json()
    assert profile["identity_verified"] is False


async def test_suspend_and_reactivate_nurse(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin5@example.com")
    nurse_headers, nurse_id, doc_ids = await _register_nurse_with_docs(client, "suspendme@example.com")
    for doc_id in doc_ids.values():
        await client.post(
            f"/api/v1/admin/nurses/{nurse_id}/documents/{doc_id}/approve", headers=admin_headers
        )
    await client.post(f"/api/v1/admin/nurses/{nurse_id}/approve", headers=admin_headers)

    suspend_resp = await client.post(
        f"/api/v1/admin/nurses/{nurse_id}/suspend", headers=admin_headers, json={"reason": "complaint"}
    )
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["is_suspended"] is True

    patient_token = await register_and_get_token(client, "searchingpatient@example.com", "PATIENT")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    search_resp = await client.get("/api/v1/nurses", headers=patient_headers)
    assert nurse_id not in [n["id"] for n in search_resp.json()]

    reactivate_resp = await client.post(
        f"/api/v1/admin/nurses/{nurse_id}/reactivate", headers=admin_headers
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["is_suspended"] is False

    search_after = await client.get("/api/v1/nurses", headers=patient_headers)
    assert nurse_id in [n["id"] for n in search_after.json()]


async def test_list_nurses_pending_verification_filter(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin6@example.com")
    _headers, nurse_id, _docs = await _register_nurse_with_docs(client, "pendingfilter@example.com")

    resp = await client.get(
        "/api/v1/admin/nurses?pending_verification=true", headers=admin_headers
    )
    assert resp.status_code == 200
    assert nurse_id in [n["id"] for n in resp.json()]


async def test_non_admin_cannot_approve_documents(client, db_session):
    _admin_headers, _admin = await _make_admin(db_session, "admin7@example.com")
    _nurse_headers, nurse_id, doc_ids = await _register_nurse_with_docs(client, "nonadmin_approve@example.com")
    token = await register_and_get_token(client, "notadminreviewer@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        f"/api/v1/admin/nurses/{nurse_id}/documents/{doc_ids['NATIONAL_ID']}/approve", headers=headers
    )
    assert resp.status_code == 403


async def test_admin_create_and_update_service(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin8@example.com")
    create_resp = await client.post(
        "/api/v1/admin/services", headers=admin_headers,
        json={"name_en": "Physiotherapy", "name_ar": "علاج طبيعي", "is_active": True},
    )
    assert create_resp.status_code == 200, create_resp.text
    service_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/services")
    assert any(s["id"] == service_id for s in list_resp.json())

    update_resp = await client.patch(
        f"/api/v1/admin/services/{service_id}", headers=admin_headers,
        json={"name_en": "Physiotherapy", "name_ar": "علاج طبيعي", "is_active": False},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False

    list_after = await client.get("/api/v1/services")
    assert not any(s["id"] == service_id for s in list_after.json())


async def test_admin_list_services_includes_inactive(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin8b@example.com")
    create_resp = await client.post(
        "/api/v1/admin/services", headers=admin_headers,
        json={"name_en": "Wound Dressing", "name_ar": "تضميد الجروح", "is_active": True},
    )
    service_id = create_resp.json()["id"]
    await client.patch(
        f"/api/v1/admin/services/{service_id}", headers=admin_headers,
        json={"name_en": "Wound Dressing", "name_ar": "تضميد الجروح", "is_active": False},
    )

    # The public endpoint hides it (inactive)...
    public_list = await client.get("/api/v1/services")
    assert not any(s["id"] == service_id for s in public_list.json())

    # ...but the admin listing must still show it, so admins can reactivate it.
    admin_list = await client.get("/api/v1/admin/services", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(s["id"] == service_id for s in admin_list.json())


async def test_non_admin_cannot_list_admin_services(client):
    token = await register_and_get_token(client, "notadmin_catalog@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/admin/services", headers=headers)
    assert resp.status_code == 403


async def test_admin_list_specialties_includes_inactive(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin8c@example.com")
    create_resp = await client.post(
        "/api/v1/admin/specialties", headers=admin_headers,
        json={"name_en": "Oncology Care", "name_ar": "رعاية الأورام", "is_active": True},
    )
    specialty_id = create_resp.json()["id"]
    await client.patch(
        f"/api/v1/admin/specialties/{specialty_id}", headers=admin_headers,
        json={"name_en": "Oncology Care", "name_ar": "رعاية الأورام", "is_active": False},
    )

    public_list = await client.get("/api/v1/specialties")
    assert not any(s["id"] == specialty_id for s in public_list.json())

    admin_list = await client.get("/api/v1/admin/specialties", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(s["id"] == specialty_id for s in admin_list.json())


async def test_admin_create_specialty(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin9@example.com")
    resp = await client.post(
        "/api/v1/admin/specialties", headers=admin_headers,
        json={"name_en": "Pediatric Care", "name_ar": "رعاية الأطفال", "is_active": True},
    )
    assert resp.status_code == 200
    list_resp = await client.get("/api/v1/specialties")
    assert any(s["name_en"] == "Pediatric Care" for s in list_resp.json())


async def test_admin_get_and_update_commission_settings(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin10@example.com")
    get_resp = await client.get("/api/v1/admin/settings", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["commission_percentage"] == 0.1

    update_resp = await client.patch(
        "/api/v1/admin/settings", headers=admin_headers, json={"commission_percentage": 0.15}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["commission_percentage"] == 0.15


async def test_admin_stats(client, db_session):
    admin_headers, _admin = await _make_admin(db_session, "admin11@example.com")
    await register_and_get_token(client, "statspatient@example.com", "PATIENT")

    resp = await client.get("/api/v1/admin/stats", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_patients" in data
    assert "total_nurses" in data
    assert isinstance(data["total_revenue"], (int, float))
