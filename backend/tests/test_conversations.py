import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _setup_patient(client, email):
    token = await register_and_get_token(client, email, "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/patients/me", headers=headers, json={"full_name": "Family Member"})
    return headers


async def _setup_approved_nurse(client, email, db_session):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/nurses/me", headers=headers,
        json={"full_name": "Nurse Person", "gender": "FEMALE", "experience_years": 4},
    )
    nurse_id = resp.json()["id"]

    import uuid as uuid_module
    from app.models.nurse import Nurse

    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    await db_session.commit()

    return headers, nurse_id


async def test_start_conversation_creates_new(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient1@example.com")
    _nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse1@example.com", db_session)

    resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["nurse_id"] == nurse_id
    assert data["other_party_name"] == "Nurse Person"
    assert data["last_message_preview"] is None


async def test_start_conversation_idempotent(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient2@example.com")
    _nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse2@example.com", db_session)

    first = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    second = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    assert first.json()["id"] == second.json()["id"]


async def test_start_conversation_unapproved_nurse_rejected(client):
    patient_headers = await _setup_patient(client, "chatpatient3@example.com")
    nurse_token = await register_and_get_token(client, "chatnurse3@example.com", "NURSE")
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    nurse_resp = await client.post(
        "/api/v1/nurses/me", headers=nurse_headers, json={"full_name": "Unapproved", "gender": "MALE"}
    )
    nurse_id = nurse_resp.json()["id"]

    resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    assert resp.status_code == 422


async def test_nurse_cannot_start_conversation(client, db_session):
    _nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse4@example.com", db_session)
    other_nurse_token = await register_and_get_token(client, "chatnurse5@example.com", "NURSE")
    other_headers = {"Authorization": f"Bearer {other_nurse_token}"}
    resp = await client.post(
        "/api/v1/conversations", headers=other_headers, json={"nurse_id": nurse_id}
    )
    assert resp.status_code == 403


async def test_send_and_list_text_messages(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient6@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse6@example.com", db_session)

    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]

    send_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=patient_headers,
        json={"message_type": "TEXT", "content": "Hello, is my father's case something you can help with?"},
    )
    assert send_resp.status_code == 201, send_resp.text
    assert send_resp.json()["content"].startswith("Hello")

    reply_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=nurse_headers,
        json={"message_type": "TEXT", "content": "Yes, happy to help."},
    )
    assert reply_resp.status_code == 201

    list_resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages", headers=patient_headers
    )
    assert list_resp.status_code == 200
    messages = list_resp.json()
    assert len(messages) == 2
    assert messages[0]["content"].startswith("Hello")
    assert messages[1]["content"] == "Yes, happy to help."


async def test_send_image_message_requires_attachment_url(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient7@example.com")
    _nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse7@example.com", db_session)
    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=patient_headers,
        json={"message_type": "IMAGE"},
    )
    assert resp.status_code == 422

    good_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=patient_headers,
        json={"message_type": "IMAGE", "attachment_url": "https://storage.example.com/photo.jpg"},
    )
    assert good_resp.status_code == 201
    assert good_resp.json()["attachment_url"] == "https://storage.example.com/photo.jpg"


async def test_third_party_cannot_access_conversation(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient8@example.com")
    _nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse8@example.com", db_session)
    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]

    intruder_headers = await _setup_patient(client, "chatintruder@example.com")
    resp = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=intruder_headers)
    assert resp.status_code == 403

    send_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=intruder_headers,
        json={"message_type": "TEXT", "content": "I should not be able to send this"},
    )
    assert send_resp.status_code == 403


async def test_list_conversations_shows_last_message_preview(client, db_session):
    patient_headers = await _setup_patient(client, "chatpatient9@example.com")
    nurse_headers, nurse_id = await _setup_approved_nurse(client, "chatnurse9@example.com", db_session)
    conv_resp = await client.post(
        "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
    )
    conv_id = conv_resp.json()["id"]
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=patient_headers,
        json={"message_type": "TEXT", "content": "Last message here"},
    )

    patient_list = await client.get("/api/v1/conversations", headers=patient_headers)
    assert patient_list.status_code == 200
    assert patient_list.json()[0]["last_message_preview"] == "Last message here"

    nurse_list = await client.get("/api/v1/conversations", headers=nurse_headers)
    assert nurse_list.status_code == 200
    assert nurse_list.json()[0]["last_message_preview"] == "Last message here"
    assert nurse_list.json()[0]["other_party_name"] == "Family Member"


async def test_unauthenticated_cannot_access_chat(client):
    resp = await client.get("/api/v1/conversations")
    assert resp.status_code == 401
