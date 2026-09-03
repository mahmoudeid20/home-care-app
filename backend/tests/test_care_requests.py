import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _patient_headers(client, email="cr_patient@example.com"):
    token = await register_and_get_token(client, email, "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/patients/me", headers=headers, json={"full_name": "Family Member"}
    )
    assert resp.status_code == 201, resp.text
    return headers


def _base_payload(service_id, **overrides):
    payload = {
        "patient_name": "Mohamed Ali",
        "patient_age": 70,
        "patient_gender": "MALE",
        "medical_condition": "Recovering from knee surgery, needs daily assistance.",
        "mobility_status": "NEEDS_ASSISTANCE",
        "special_requirements": "Prefers Arabic-speaking nurse",
        "service_ids": [str(service_id)],
        "preferred_nurse_gender": "FEMALE",
        "min_experience_years": 3,
        "required_specialty_ids": [],
        "languages": ["ar", "en"],
        "verified_nurses_only": True,
        "preferred_shift": "MORNING",
        "location": {"governorate": "Cairo", "city": "Heliopolis", "area": "Zone 3"},
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "hours_per_day": 12,
        "number_of_days": 30,
        "payment_frequency": "MONTHLY",
        "budget_min": 10000,
        "budget_max": 15000,
    }
    payload.update(overrides)
    return payload


async def test_create_care_request_success(client, seed_lookup):
    headers = await _patient_headers(client)
    payload = _base_payload(seed_lookup["service_general"])
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "OPEN"
    assert data["patient_name"] == "Mohamed Ali"
    assert data["budget_min"] == 10000
    assert data["budget_max"] == 15000
    assert data["location"]["governorate"] == "Cairo"
    assert len(data["required_services"]) == 1
    assert data["languages"] == ["ar", "en"]


async def test_create_care_request_without_patient_profile(client, seed_lookup):
    token = await register_and_get_token(client, "noprofile_cr@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    payload = _base_payload(seed_lookup["service_general"])
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 404


async def test_create_care_request_unknown_service_rejected(client, seed_lookup):
    headers = await _patient_headers(client, email="badservice@example.com")
    payload = _base_payload("00000000-0000-0000-0000-000000000000")
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 422


async def test_create_care_request_requires_at_least_one_service(client, seed_lookup):
    headers = await _patient_headers(client, email="noservice@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    payload["service_ids"] = []
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 422


async def test_create_care_request_invalid_budget_range(client, seed_lookup):
    headers = await _patient_headers(client, email="badbudget@example.com")
    payload = _base_payload(seed_lookup["service_general"], budget_min=20000, budget_max=10000)
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 422


async def test_create_care_request_end_before_start_rejected(client, seed_lookup):
    headers = await _patient_headers(client, email="baddates@example.com")
    payload = _base_payload(
        seed_lookup["service_general"], start_date="2026-09-10", end_date="2026-09-01"
    )
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 422


async def test_nurse_cannot_create_care_request(client, seed_lookup):
    token = await register_and_get_token(client, "nurseascr@example.com", "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    payload = _base_payload(seed_lookup["service_general"])
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 403


async def test_get_care_request_owner_only(client, seed_lookup):
    headers = await _patient_headers(client, email="owner1@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    create_resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    cr_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/care-requests/{cr_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == cr_id

    other_headers = await _patient_headers(client, email="intruder@example.com")
    forbidden_resp = await client.get(f"/api/v1/care-requests/{cr_id}", headers=other_headers)
    assert forbidden_resp.status_code == 403


async def test_get_care_request_not_found(client, seed_lookup):
    headers = await _patient_headers(client, email="notfound_cr@example.com")
    resp = await client.get(
        "/api/v1/care-requests/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404


async def test_nurse_who_applied_can_view_care_request(client, seed_lookup, db_session):
    from tests.test_applications import _setup_approved_nurse

    patient_headers = await _patient_headers(client, email="cr_owner_for_nurse_view@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    cr_resp = await client.post("/api/v1/care-requests", headers=patient_headers, json=payload)
    cr_id = cr_resp.json()["id"]

    nurse_headers, nurse_id = await _setup_approved_nurse(
        client, seed_lookup, "cr_view_nurse@example.com", db_session
    )

    # Before applying: no access, matches the pre-existing "owner only" rule.
    forbidden = await client.get(f"/api/v1/care-requests/{cr_id}", headers=nurse_headers)
    assert forbidden.status_code == 403

    app_resp = await client.post(
        "/api/v1/applications",
        headers=patient_headers,
        json={"care_request_id": cr_id, "nurse_id": nurse_id},
    )
    assert app_resp.status_code == 201, app_resp.text

    # After applying: the nurse can now view the request they applied to.
    allowed = await client.get(f"/api/v1/care-requests/{cr_id}", headers=nurse_headers)
    assert allowed.status_code == 200
    assert allowed.json()["id"] == cr_id


async def test_unrelated_nurse_still_forbidden_from_care_request(client, seed_lookup, db_session):
    from tests.test_applications import _setup_approved_nurse

    patient_headers = await _patient_headers(client, email="cr_owner_unrelated@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    cr_resp = await client.post("/api/v1/care-requests", headers=patient_headers, json=payload)
    cr_id = cr_resp.json()["id"]

    # A different nurse who never applied to this request.
    bystander_headers, _ = await _setup_approved_nurse(
        client, seed_lookup, "cr_view_bystander@example.com", db_session
    )
    resp = await client.get(f"/api/v1/care-requests/{cr_id}", headers=bystander_headers)
    assert resp.status_code == 403


async def test_list_my_care_requests(client, seed_lookup):
    headers = await _patient_headers(client, email="lister@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    await client.post("/api/v1/care-requests", headers=headers, json=payload)
    await client.post("/api/v1/care-requests", headers=headers, json=payload)

    resp = await client.get("/api/v1/care-requests", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_care_request_while_open(client, seed_lookup):
    headers = await _patient_headers(client, email="updater@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    create_resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    cr_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/care-requests/{cr_id}",
        headers=headers,
        json={"patient_age": 71, "budget_max": 16000},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["patient_age"] == 71
    assert data["budget_max"] == 16000
    assert data["patient_name"] == "Mohamed Ali"  # untouched


async def test_cancel_care_request(client, seed_lookup):
    headers = await _patient_headers(client, email="canceller@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    create_resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    cr_id = create_resp.json()["id"]

    cancel_resp = await client.post(f"/api/v1/care-requests/{cr_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Cancelling again should fail — already terminal.
    second_cancel = await client.post(f"/api/v1/care-requests/{cr_id}/cancel", headers=headers)
    assert second_cancel.status_code == 422


async def test_cannot_update_cancelled_care_request(client, seed_lookup):
    headers = await _patient_headers(client, email="updatecancelled@example.com")
    payload = _base_payload(seed_lookup["service_general"])
    create_resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    cr_id = create_resp.json()["id"]
    await client.post(f"/api/v1/care-requests/{cr_id}/cancel", headers=headers)

    update_resp = await client.patch(
        f"/api/v1/care-requests/{cr_id}", headers=headers, json={"patient_age": 80}
    )
    assert update_resp.status_code == 422


async def test_unauthenticated_cannot_access_care_requests(client):
    resp = await client.get("/api/v1/care-requests")
    assert resp.status_code == 401
