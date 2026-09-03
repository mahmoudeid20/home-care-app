import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _make_patient_with_request(client, seed_lookup, email="match_patient@example.com", **overrides):
    token = await register_and_get_token(client, email, "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/patients/me", headers=headers, json={"full_name": "Family Member"})

    payload = {
        "patient_name": "Elderly Parent",
        "patient_age": 72,
        "patient_gender": "MALE",
        "medical_condition": "Post-operative recovery, needs daily assistance.",
        "mobility_status": "NEEDS_ASSISTANCE",
        "service_ids": [str(seed_lookup["service_general"])],
        "required_specialty_ids": [str(seed_lookup["specialty_elderly"])],
        "languages": ["ar"],
        "verified_nurses_only": False,
        "preferred_shift": "MORNING",
        "location": {
            "governorate": "Cairo", "city": "Maadi", "area": "Zone 1",
            "latitude": 29.96, "longitude": 31.25,
        },
        "start_date": "2026-09-01",
        "hours_per_day": 8,
        "payment_frequency": "MONTHLY",
        "budget_min": 8000,
        "budget_max": 13000,
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/care-requests", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return headers, resp.json()["id"]


async def _make_approved_nurse(
    client, seed_lookup, email, experience_years=5, price=12000, lat=29.97, lng=31.24, gender="FEMALE",
    approved=True, db_session=None,
):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/nurses/me",
        headers=headers,
        json={
            "full_name": f"Nurse {email}",
            "gender": gender,
            "experience_years": experience_years,
            "location": {"governorate": "Cairo", "city": "Maadi", "latitude": lat, "longitude": lng},
            "specialty_ids": [str(seed_lookup["specialty_elderly"])],
            "services": [
                {"service_id": str(seed_lookup["service_general"]), "price": price, "price_unit": "MONTHLY"}
            ],
            "availability": [{"shift_type": "MORNING", "start_time": "08:00:00", "end_time": "16:00:00"}],
        },
    )
    assert resp.status_code == 201, resp.text
    nurse_id = resp.json()["id"]

    if approved and db_session is not None:
        from app.models.nurse import Nurse
        nurse = await db_session.get(Nurse, __import__("uuid").UUID(nurse_id))
        nurse.is_approved = True
        nurse.identity_verified = True
        nurse.qualification_verified = True
        nurse.experience_verified = True
        await db_session.commit()

    return nurse_id


async def test_matches_exclude_unapproved_nurses(client, seed_lookup, db_session):
    patient_headers, cr_id = await _make_patient_with_request(client, seed_lookup)
    # Nurse created but never approved.
    await _make_approved_nurse(
        client, seed_lookup, "unapproved@example.com", approved=False, db_session=db_session
    )

    resp = await client.get(f"/api/v1/care-requests/{cr_id}/matches", headers=patient_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_matches_return_ranked_approved_nurses(client, seed_lookup, db_session):
    patient_headers, cr_id = await _make_patient_with_request(client, seed_lookup)

    good_id = await _make_approved_nurse(
        client, seed_lookup, "good_match@example.com",
        experience_years=8, price=12000, lat=29.97, lng=31.24, db_session=db_session,
    )
    far_id = await _make_approved_nurse(
        client, seed_lookup, "far_match@example.com",
        experience_years=1, price=25000, lat=31.2, lng=29.9, db_session=db_session,  # Alexandria-ish, far away
    )

    resp = await client.get(f"/api/v1/care-requests/{cr_id}/matches", headers=patient_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2

    by_id = {r["nurse_id"]: r for r in results}
    assert by_id[good_id]["match_score"] > by_id[far_id]["match_score"]
    assert by_id[good_id]["distance_km"] < by_id[far_id]["distance_km"]
    assert "Matches required specialties/services" in by_id[good_id]["matching_reasons"]
    # Results are sorted descending by match_score.
    assert results[0]["match_score"] >= results[1]["match_score"]


async def test_matches_respect_preferred_gender_hard_filter(client, seed_lookup, db_session):
    patient_headers, cr_id = await _make_patient_with_request(
        client, seed_lookup, email="genderpref@example.com"
    )
    # Request has no gender preference by default in the helper — set one explicitly this time.
    token = await register_and_get_token(client, "genderpref2@example.com", "PATIENT")
    headers2 = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/patients/me", headers=headers2, json={"full_name": "FM"})
    payload = {
        "patient_name": "Someone",
        "patient_age": 60,
        "patient_gender": "FEMALE",
        "medical_condition": "General care needed.",
        "mobility_status": "INDEPENDENT",
        "service_ids": [str(seed_lookup["service_general"])],
        "preferred_nurse_gender": "MALE",
        "location": {"governorate": "Cairo", "city": "Maadi"},
        "start_date": "2026-09-01",
        "payment_frequency": "MONTHLY",
    }
    cr_resp = await client.post("/api/v1/care-requests", headers=headers2, json=payload)
    cr_id2 = cr_resp.json()["id"]

    await _make_approved_nurse(
        client, seed_lookup, "femalenurse@example.com", gender="FEMALE", db_session=db_session
    )

    resp = await client.get(f"/api/v1/care-requests/{cr_id2}/matches", headers=headers2)
    assert resp.status_code == 200
    assert resp.json() == []  # only a FEMALE nurse exists, request wants MALE


async def test_matches_forbidden_for_non_owner(client, seed_lookup, db_session):
    patient_headers, cr_id = await _make_patient_with_request(
        client, seed_lookup, email="matchowner@example.com"
    )
    intruder_token = await register_and_get_token(client, "matchintruder@example.com", "PATIENT")
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    await client.post("/api/v1/patients/me", headers=intruder_headers, json={"full_name": "X"})

    resp = await client.get(f"/api/v1/care-requests/{cr_id}/matches", headers=intruder_headers)
    assert resp.status_code == 403


async def test_admin_can_view_and_update_matching_weights(client, db_session):
    # ADMIN accounts cannot self-register via the API by design (Section 7) —
    # create one directly in the DB to test the admin-only endpoint, the
    # same way a real deployment would seed its first admin.
    from app.core.security import create_access_token, hash_password
    from app.models.user import User, UserRole

    admin = User(
        email="realadmin@example.com",
        password_hash=hash_password("Passw0rd1"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    admin_token = create_access_token(str(admin.id), UserRole.ADMIN.value)
    headers = {"Authorization": f"Bearer {admin_token}"}

    get_resp = await client.get("/api/v1/admin/matching-weights", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert abs(sum(data.values()) - 1.0) < 0.01
    assert data["skills_weight"] == 0.3

    patch_resp = await client.patch(
        "/api/v1/admin/matching-weights",
        headers=headers,
        json={
            "skills_weight": 0.4,
            "experience_weight": 0.2,
            "location_weight": 0.1,
            "availability_weight": 0.1,
            "price_weight": 0.1,
            "rating_weight": 0.05,
            "verification_weight": 0.05,
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["skills_weight"] == 0.4


async def test_non_admin_cannot_view_matching_weights(client):
    token = await register_and_get_token(client, "notadmin2@example.com", "PATIENT")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/admin/matching-weights", headers=headers)
    assert resp.status_code == 403


async def test_matching_weights_must_sum_to_one():
    from app.schemas.matching import MatchingWeightsUpdate
    import pytest as pytest_module

    with pytest_module.raises(Exception):
        MatchingWeightsUpdate(
            skills_weight=0.5,
            experience_weight=0.5,
            location_weight=0.5,
            availability_weight=0.0,
            price_weight=0.0,
            rating_weight=0.0,
            verification_weight=0.0,
        )
