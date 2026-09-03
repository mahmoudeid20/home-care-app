import pytest

pytestmark = pytest.mark.asyncio


async def test_register_patient_success(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "patient1@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "patient1@example.com"
    assert data["user"]["role"] == "PATIENT"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]


async def test_register_admin_forbidden(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "admin1@example.com", "password": "Passw0rd1", "role": "ADMIN"},
    )
    assert resp.status_code == 422


async def test_register_duplicate_email_conflict(client):
    payload = {"email": "dup@example.com", "password": "Passw0rd1", "role": "NURSE"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "alllettersnodigits", "role": "PATIENT"},
    )
    assert resp.status_code == 422


async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login1@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login1@example.com", "password": "Passw0rd1"},
    )
    assert resp.status_code == 200
    assert resp.json()["tokens"]["access_token"]


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login2@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login2@example.com", "password": "WrongPass1"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_nonexistent_user(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "Passw0rd1"},
    )
    assert resp.status_code == 401


async def test_get_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_get_me_with_valid_token(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "Passw0rd1", "role": "NURSE"},
    )
    access_token = register.json()["tokens"]["access_token"]

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_refresh_rotates_token_and_invalidates_old(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh1@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    old_refresh = register.json()["tokens"]["refresh_token"]

    first_refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert first_refresh.status_code == 200
    new_tokens = first_refresh.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"] != old_refresh

    # Reusing the old (now-rotated) refresh token must fail.
    reuse_attempt = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert reuse_attempt.status_code == 401


async def test_logout_invalidates_refresh_token(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "logout1@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    refresh_token = register.json()["tokens"]["refresh_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_resp.status_code == 204

    refresh_after_logout = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_after_logout.status_code == 401


async def test_forgot_password_always_204(client):
    # Existing user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "forgot1@example.com", "password": "Passw0rd1", "role": "PATIENT"},
    )
    resp1 = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "forgot1@example.com"}
    )
    assert resp1.status_code == 204

    # Non-existent user — must not leak whether the account exists.
    resp2 = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert resp2.status_code == 204


async def test_invalid_access_token_rejected(client):
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
