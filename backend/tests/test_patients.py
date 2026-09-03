import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _auth_headers(client, email="patient_profile@example.com", role="PATIENT"):
    token = await register_and_get_token(client, email, role)
    return {"Authorization": f"Bearer {token}"}


async def test_create_patient_profile_success(client):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/api/v1/patients/me",
        headers=headers,
        json={
            "full_name": "Fatma Ahmed",
            "preferred_language": "ar",
            "location": {"governorate": "Cairo", "city": "Nasr City", "area": "Zone 5"},
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "Fatma Ahmed"
    assert data["location"]["governorate"] == "Cairo"


async def test_create_patient_profile_with_photo(client):
    headers = await _auth_headers(client, email="patient_photo_create@example.com")
    resp = await client.post(
        "/api/v1/patients/me",
        headers=headers,
        json={
            "full_name": "Fatma Ahmed",
            "photo_url": "https://storage.example.com/patient-photos/fatma.jpg",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["photo_url"] == "https://storage.example.com/patient-photos/fatma.jpg"


async def test_create_patient_profile_rejects_non_image_photo_url(client):
    headers = await _auth_headers(client, email="patient_photo_bad_ext@example.com")
    resp = await client.post(
        "/api/v1/patients/me",
        headers=headers,
        json={
            "full_name": "Bad Photo Patient",
            "photo_url": "https://storage.example.com/patient-photos/fatma.exe",
        },
    )
    assert resp.status_code == 422


async def test_update_patient_profile_sets_and_replaces_photo(client):
    headers = await _auth_headers(client, email="patient_photo_update@example.com")
    await client.post("/api/v1/patients/me", headers=headers, json={"full_name": "No Photo Yet"})

    mine = await client.get("/api/v1/patients/me", headers=headers)
    assert mine.json()["photo_url"] is None

    resp = await client.patch(
        "/api/v1/patients/me",
        headers=headers,
        json={"photo_url": "https://storage.example.com/patient-photos/v1.png"},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_url"] == "https://storage.example.com/patient-photos/v1.png"

    resp2 = await client.patch(
        "/api/v1/patients/me",
        headers=headers,
        json={"photo_url": "https://storage.example.com/patient-photos/v2.png"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["photo_url"] == "https://storage.example.com/patient-photos/v2.png"


    headers = await _auth_headers(client, email="nolocation@example.com")
    resp = await client.post(
        "/api/v1/patients/me",
        headers=headers,
        json={"full_name": "No Location Patient"},
    )
    assert resp.status_code == 201
    assert resp.json()["location"] is None


async def test_create_duplicate_patient_profile_conflict(client):
    headers = await _auth_headers(client, email="dupprofile@example.com")
    payload = {"full_name": "First"}
    first = await client.post("/api/v1/patients/me", headers=headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/patients/me", headers=headers, json=payload)
    assert second.status_code == 409


async def test_nurse_cannot_create_patient_profile(client):
    headers = await _auth_headers(client, email="nurseasspatient@example.com", role="NURSE")
    resp = await client.post(
        "/api/v1/patients/me", headers=headers, json={"full_name": "Should Fail"}
    )
    assert resp.status_code == 403


async def test_get_patient_profile_not_found(client):
    headers = await _auth_headers(client, email="noprofileyet@example.com")
    resp = await client.get("/api/v1/patients/me", headers=headers)
    assert resp.status_code == 404


async def test_update_patient_profile(client):
    headers = await _auth_headers(client, email="updateprofile@example.com")
    await client.post(
        "/api/v1/patients/me", headers=headers, json={"full_name": "Old Name"}
    )
    resp = await client.patch(
        "/api/v1/patients/me",
        headers=headers,
        json={"full_name": "New Name", "location": {"governorate": "Giza", "city": "Dokki"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "New Name"
    assert data["location"]["governorate"] == "Giza"


async def test_unauthenticated_cannot_access_patient_endpoints(client):
    resp = await client.get("/api/v1/patients/me")
    assert resp.status_code == 401
