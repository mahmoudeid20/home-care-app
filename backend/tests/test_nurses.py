import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _auth_headers(client, email="nurse_profile@example.com", role="NURSE"):
    token = await register_and_get_token(client, email, role)
    return {"Authorization": f"Bearer {token}"}


async def test_create_nurse_profile_success(client, seed_lookup):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": "Ahmed Mohamed",
            "professional_title": "Registered Nurse",
            "gender": "MALE",
            "experience_years": 7,
            "location": {"governorate": "Cairo", "city": "Maadi"},
            "specialty_ids": [str(seed_lookup["specialty_elderly"])],
            "services": [
                {
                    "service_id": str(seed_lookup["service_general"]),
                    "price": 12000,
                    "price_unit": "MONTHLY",
                }
            ],
            "availability": [
                {"shift_type": "MORNING", "start_time": "08:00:00", "end_time": "16:00:00"}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "Ahmed Mohamed"
    assert data["experience_years"] == 7
    assert data["is_approved"] is False  # not verified yet — correct default
    assert data["identity_verified"] is False
    assert len(data["specialties"]) == 1
    assert data["specialties"][0]["name_en"] == "Elderly Care"
    assert len(data["services"]) == 1
    assert data["services"][0]["price"] == 12000
    assert len(data["availability"]) == 1


async def test_create_nurse_profile_with_photo(client, seed_lookup):
    headers = await _auth_headers(client, email="photo_create@example.com")
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": "Heba El-Sayed",
            "gender": "FEMALE",
            "photo_url": "https://storage.example.com/nurse-photos/heba.jpg",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["photo_url"] == "https://storage.example.com/nurse-photos/heba.jpg"


async def test_create_nurse_profile_rejects_non_image_photo_url(client, seed_lookup):
    headers = await _auth_headers(client, email="photo_bad_ext@example.com")
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": "Bad Photo Nurse",
            "gender": "MALE",
            "photo_url": "https://storage.example.com/nurse-photos/heba.exe",
        },
    )
    assert resp.status_code == 422


async def test_update_nurse_profile_sets_and_replaces_photo(client, seed_lookup):
    headers = await _auth_headers(client, email="photo_update@example.com")
    await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={"full_name": "No Photo Yet", "gender": "FEMALE"},
    )
    # starts unset
    mine = await client.get("/api/v1/nurses/me", headers=headers)
    assert mine.json()["photo_url"] is None

    resp = await client.patch(
        "/api/v1/nurses/me",
        headers=headers,
        json={"photo_url": "https://storage.example.com/nurse-photos/v1.png"},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_url"] == "https://storage.example.com/nurse-photos/v1.png"

    # replacing with a new photo overwrites the old URL, doesn't append
    resp2 = await client.patch(
        "/api/v1/nurses/me",
        headers=headers,
        json={"photo_url": "https://storage.example.com/nurse-photos/v2.png"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["photo_url"] == "https://storage.example.com/nurse-photos/v2.png"


async def test_nurse_search_result_includes_photo_url(client, seed_lookup, db_session):
    import uuid as uuid_module
    from app.models.nurse import Nurse

    headers = await _auth_headers(client, email="photo_search@example.com")
    create_resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": "Searchable Photo Nurse",
            "gender": "FEMALE",
            "photo_url": "https://storage.example.com/nurse-photos/search.webp",
            "specialty_ids": [str(seed_lookup["specialty_elderly"])],
        },
    )
    nurse_id = create_resp.json()["id"]
    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    resp = await client.get(
        "/api/v1/nurses", headers=headers, params={"specialty_id": str(seed_lookup["specialty_elderly"])}
    )
    assert resp.status_code == 200
    results = resp.json()
    match = next(r for r in results if r["id"] == nurse_id)
    assert match["photo_url"] == "https://storage.example.com/nurse-photos/search.webp"


async def test_create_nurse_profile_unknown_specialty_rejected(client, seed_lookup):
    headers = await _auth_headers(client, email="badspecialty@example.com")
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": "Bad Specialty Nurse",
            "gender": "FEMALE",
            "specialty_ids": ["00000000-0000-0000-0000-000000000000"],
        },
    )
    assert resp.status_code == 422


async def test_patient_cannot_create_nurse_profile(client, seed_lookup):
    headers = await _auth_headers(client, email="patientasnurse@example.com", role="PATIENT")
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={"full_name": "Should Fail", "gender": "MALE"},
    )
    assert resp.status_code == 403


async def test_duplicate_nurse_profile_conflict(client, seed_lookup):
    headers = await _auth_headers(client, email="dupnurse@example.com")
    payload = {"full_name": "First Profile", "gender": "MALE"}
    first = await client.post("/api/v1/nurses/me", headers=headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/nurses/me", headers=headers, json=payload)
    assert second.status_code == 409


async def test_update_nurse_profile(client, seed_lookup):
    headers = await _auth_headers(client, email="updatenurse@example.com")
    await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={"full_name": "Original Name", "gender": "FEMALE", "experience_years": 2},
    )
    resp = await client.patch(
        "/api/v1/nurses/me",
        headers=headers,
        json={"experience_years": 5, "bio": "Updated bio"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["experience_years"] == 5
    assert data["bio"] == "Updated bio"
    assert data["full_name"] == "Original Name"  # untouched fields preserved


async def test_get_nurse_public_profile(client, seed_lookup):
    nurse_headers = await _auth_headers(client, email="publicnurse@example.com")
    create_resp = await client.post(
        "/api/v1/nurses/me",
        headers=nurse_headers,
        json={"full_name": "Public Nurse", "gender": "MALE"},
    )
    nurse_id = create_resp.json()["id"]

    patient_headers = await _auth_headers(
        client, email="viewingpatient@example.com", role="PATIENT"
    )
    resp = await client.get(f"/api/v1/nurses/{nurse_id}", headers=patient_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Public Nurse"


async def test_get_nurse_public_profile_not_found(client, seed_lookup):
    patient_headers = await _auth_headers(
        client, email="viewingpatient2@example.com", role="PATIENT"
    )
    resp = await client.get(
        "/api/v1/nurses/00000000-0000-0000-0000-000000000000", headers=patient_headers
    )
    assert resp.status_code == 404


async def test_upload_and_list_nurse_documents(client, seed_lookup):
    headers = await _auth_headers(client, email="docsnurse@example.com")
    await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={"full_name": "Docs Nurse", "gender": "FEMALE"},
    )

    upload_resp = await client.post(
        "/api/v1/nurses/me/documents",
        headers=headers,
        json={"document_type": "NATIONAL_ID", "file_url": "https://storage.example.com/id123.pdf"},
    )
    assert upload_resp.status_code == 201
    assert upload_resp.json()["status"] == "PENDING"

    list_resp = await client.get("/api/v1/nurses/me/documents", headers=headers)
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) == 1
    assert docs[0]["document_type"] == "NATIONAL_ID"


async def test_list_specialties_and_services_public(client, seed_lookup):
    specialties_resp = await client.get("/api/v1/specialties")
    assert specialties_resp.status_code == 200
    names = {s["name_en"] for s in specialties_resp.json()}
    assert "Elderly Care" in names

    services_resp = await client.get("/api/v1/services")
    assert services_resp.status_code == 200
    assert any(s["name_en"] == "General Nursing" for s in services_resp.json())
