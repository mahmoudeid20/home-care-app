import pytest

from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


async def _approve_nurse(db_session, nurse_id: str, **flags):
    import uuid as uuid_module
    from app.models.nurse import Nurse

    nurse = await db_session.get(Nurse, uuid_module.UUID(nurse_id))
    nurse.is_approved = True
    for k, v in flags.items():
        setattr(nurse, k, v)
    await db_session.commit()


async def _create_nurse(client, seed_lookup, email, **overrides):
    token = await register_and_get_token(client, email, "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": f"Nurse {email}",
        "gender": "FEMALE",
        "experience_years": 5,
        "location": {"governorate": "Cairo", "city": "Maadi"},
        "specialty_ids": [str(seed_lookup["specialty_elderly"])],
        "services": [
            {"service_id": str(seed_lookup["service_general"]), "price": 10000, "price_unit": "MONTHLY"}
        ],
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/nurses/me", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _patient_headers(client, email):
    token = await register_and_get_token(client, email, "PATIENT")
    return {"Authorization": f"Bearer {token}"}


async def test_unapproved_nurses_excluded_from_search(client, seed_lookup, db_session):
    await _create_nurse(client, seed_lookup, "notapproved_search@example.com")
    headers = await _patient_headers(client, "searcher1@example.com")

    resp = await client.get("/api/v1/nurses", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_approved_nurse_appears_in_search(client, seed_lookup, db_session):
    nurse_id = await _create_nurse(client, seed_lookup, "approved_search@example.com")
    await _approve_nurse(db_session, nurse_id)

    headers = await _patient_headers(client, "searcher2@example.com")
    resp = await client.get("/api/v1/nurses", headers=headers)
    assert resp.status_code == 200
    ids = [n["id"] for n in resp.json()]
    assert nurse_id in ids


async def test_search_filter_by_gender(client, seed_lookup, db_session):
    male_id = await _create_nurse(client, seed_lookup, "male_search@example.com", gender="MALE")
    female_id = await _create_nurse(client, seed_lookup, "female_search@example.com", gender="FEMALE")
    await _approve_nurse(db_session, male_id)
    await _approve_nurse(db_session, female_id)

    headers = await _patient_headers(client, "searcher3@example.com")
    resp = await client.get("/api/v1/nurses?gender=MALE", headers=headers)
    assert resp.status_code == 200
    ids = [n["id"] for n in resp.json()]
    assert male_id in ids
    assert female_id not in ids


async def test_search_filter_by_min_experience(client, seed_lookup, db_session):
    junior_id = await _create_nurse(
        client, seed_lookup, "junior@example.com", experience_years=1
    )
    senior_id = await _create_nurse(
        client, seed_lookup, "senior@example.com", experience_years=10
    )
    await _approve_nurse(db_session, junior_id)
    await _approve_nurse(db_session, senior_id)

    headers = await _patient_headers(client, "searcher4@example.com")
    resp = await client.get("/api/v1/nurses?min_experience_years=5", headers=headers)
    ids = [n["id"] for n in resp.json()]
    assert senior_id in ids
    assert junior_id not in ids


async def test_search_filter_verified_only(client, seed_lookup, db_session):
    verified_id = await _create_nurse(client, seed_lookup, "verifiedsearch@example.com")
    unverified_id = await _create_nurse(client, seed_lookup, "unverifiedsearch@example.com")
    await _approve_nurse(
        db_session, verified_id,
        identity_verified=True, qualification_verified=True, experience_verified=True,
    )
    await _approve_nurse(db_session, unverified_id)  # approved but not verified

    headers = await _patient_headers(client, "searcher5@example.com")
    resp = await client.get("/api/v1/nurses?verified_only=true", headers=headers)
    ids = [n["id"] for n in resp.json()]
    assert verified_id in ids
    assert unverified_id not in ids


async def test_search_filter_price_range(client, seed_lookup, db_session):
    cheap_id = await _create_nurse(
        client, seed_lookup, "cheapnurse@example.com",
        services=[{"service_id": str(seed_lookup["service_general"]), "price": 5000, "price_unit": "MONTHLY"}],
    )
    expensive_id = await _create_nurse(
        client, seed_lookup, "expensivenurse@example.com",
        services=[{"service_id": str(seed_lookup["service_general"]), "price": 20000, "price_unit": "MONTHLY"}],
    )
    await _approve_nurse(db_session, cheap_id)
    await _approve_nurse(db_session, expensive_id)

    headers = await _patient_headers(client, "searcher6@example.com")
    resp = await client.get("/api/v1/nurses?price_max=10000", headers=headers)
    ids = [n["id"] for n in resp.json()]
    assert cheap_id in ids
    assert expensive_id not in ids


async def test_search_response_shape(client, seed_lookup, db_session):
    nurse_id = await _create_nurse(client, seed_lookup, "shapetest@example.com")
    await _approve_nurse(db_session, nurse_id)

    headers = await _patient_headers(client, "searcher7@example.com")
    resp = await client.get("/api/v1/nurses", headers=headers)
    card = resp.json()[0]
    assert set(["id", "full_name", "is_verified", "experience_years", "specialties",
                "average_rating", "review_count", "governorate", "city",
                "starting_price", "price_unit"]).issubset(card.keys())
    assert card["starting_price"] == 10000
