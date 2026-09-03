import pytest

from app.core.config import settings
from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def test_security_headers_present_on_every_response(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in resp.headers


async def test_security_headers_present_even_on_error_response(client):
    resp = await client.get("/api/v1/nurses/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 401
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


async def test_health_endpoint_exempt_from_rate_limit(client):
    original = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 2
    try:
        for _ in range(5):
            resp = await client.get("/health")
            assert resp.status_code == 200
    finally:
        settings.RATE_LIMIT_PER_MINUTE = original


async def test_rate_limit_blocks_after_threshold(client):
    original = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 3
    try:
        statuses = []
        for _ in range(5):
            resp = await client.get("/api/v1/specialties")
            statuses.append(resp.status_code)
        assert statuses[:3] == [200, 200, 200]
        assert 429 in statuses

        limited_resp = await client.get("/api/v1/specialties")
        assert limited_resp.status_code == 429
        assert limited_resp.headers.get("Retry-After") == "60"
    finally:
        settings.RATE_LIMIT_PER_MINUTE = original


async def test_rate_limit_is_per_identity_not_global(client):
    """Two different authenticated users shouldn't share a rate-limit bucket."""
    original = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 2
    try:
        token1 = await register_and_get_token(client, "ratelimituser1@example.com", "PATIENT")
        headers1 = {"Authorization": f"Bearer {token1}"}
        for _ in range(2):
            resp = await client.get("/api/v1/auth/me", headers=headers1)
            assert resp.status_code == 200

        token2 = await register_and_get_token(client, "ratelimituser2@example.com", "PATIENT")
        headers2 = {"Authorization": f"Bearer {token2}"}
        resp2 = await client.get("/api/v1/auth/me", headers=headers2)
        assert resp2.status_code == 200
    finally:
        settings.RATE_LIMIT_PER_MINUTE = original


async def test_nurse_document_rejects_disallowed_extension(client):
    token = await register_and_get_token(client, "fileext_nurse@example.com", "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/v1/nurses/me", headers=headers,
        json={"full_name": "File Ext Nurse", "gender": "MALE"},
    )
    resp = await client.post(
        "/api/v1/nurses/me/documents", headers=headers,
        json={"document_type": "NATIONAL_ID", "file_url": "https://storage.example.com/id.exe"},
    )
    assert resp.status_code == 422


async def test_nurse_document_accepts_allowed_extension(client):
    token = await register_and_get_token(client, "fileext_nurse2@example.com", "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/v1/nurses/me", headers=headers,
        json={"full_name": "File Ext Nurse 2", "gender": "MALE"},
    )
    resp = await client.post(
        "/api/v1/nurses/me/documents", headers=headers,
        json={"document_type": "NATIONAL_ID", "file_url": "https://storage.example.com/id.pdf"},
    )
    assert resp.status_code == 201


async def test_chat_image_rejects_non_image_extension(client, db_session):
    patient_token = await register_and_get_token(client, "fileext_patient@example.com", "PATIENT")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    await client.post("/api/v1/patients/me", headers=patient_headers, json={"full_name": "FM"})

    nurse_token = await register_and_get_token(client, "fileext_nurse3@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers,
        json={"full_name": "File Ext Nurse 3", "gender": "FEMALE"},
    )
    nurse_id = nurse_resp.json()["id"]
    import uuid as uuid_module
    from app.models.nurse import Nurse
    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]

    bad_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages", headers=patient_headers,
        json={"message_type": "IMAGE", "attachment_url": "https://storage.example.com/malware.exe"},
    )
    assert bad_resp.status_code == 422

    good_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages", headers=patient_headers,
        json={"message_type": "IMAGE", "attachment_url": "https://storage.example.com/photo.png"},
    )
    assert good_resp.status_code == 201


async def test_cors_wildcard_does_not_allow_credentials():
    from app.main import app as fastapi_app

    cors_middlewares = [
        m for m in fastapi_app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    ]
    assert len(cors_middlewares) == 1
    if settings.CORS_ORIGINS == ["*"]:
        assert cors_middlewares[0].kwargs.get("allow_credentials") is False
