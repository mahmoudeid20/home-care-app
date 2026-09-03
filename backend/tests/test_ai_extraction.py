import pytest

from app.api.deps import get_llm_client_dep
from app.main import app
from tests.conftest import register_and_get_token

pytestmark = pytest.mark.asyncio


class _FakeLLMClient:
    """Returns canned, deterministic JSON instead of calling a real LLM --
    keeps these tests fast, free, and independent of any API key/network
    access, exactly like the FCM stub pattern used for notifications."""

    def __init__(self, response: dict):
        self.response = response
        self.last_text_seen = None

    async def extract_requirements(self, text: str) -> dict:
        self.last_text_seen = text
        return self.response


def _override_llm(fake_client):
    async def _dep():
        return fake_client

    app.dependency_overrides[get_llm_client_dep] = _dep


def _clear_llm_override():
    app.dependency_overrides.pop(get_llm_client_dep, None)


async def test_extraction_returns_prefilled_fields(client, seed_lookup):
    fake = _FakeLLMClient(
        {
            "age": 70,
            "gender": "MALE",
            "patient_type": "elderly",
            "duration_days": 30,
            "hours_per_day": 12,
            "required_specialty_keywords": ["Elderly Care"],
            "required_service_keywords": ["General Nursing"],
            "preferred_shift": "MORNING",
            "languages": ["ar", "en"],
            "mobility_status": "NEEDS_ASSISTANCE",
        }
    )
    _override_llm(fake)
    try:
        token = await register_and_get_token(client, "aiextract1@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={
                "text": "My father is 70 years old, recently had knee surgery, needs someone "
                "for 12 hours every day for one month, elderly care experience preferred."
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["age"] == 70
        assert data["gender"] == "MALE"
        assert data["duration_days"] == 30
        assert data["hours_per_day"] == 12
        assert data["preferred_shift"] == "MORNING"
        assert data["mobility_status"] == "NEEDS_ASSISTANCE"
        assert str(seed_lookup["specialty_elderly"]) in data["matched_specialty_ids"]
        assert str(seed_lookup["service_general"]) in data["matched_service_ids"]
        assert data["unmatched_specialty_keywords"] == []
        assert fake.last_text_seen.startswith("My father is 70")
    finally:
        _clear_llm_override()


async def test_extraction_never_diagnoses_only_extracts_logistics(client, seed_lookup):
    """The service only ever surfaces the fixed logistics schema — even if
    the (fake, here) model tried to sneak in extra fields like a diagnosis
    or treatment recommendation, the response schema can't carry them."""
    fake = _FakeLLMClient(
        {
            "age": 70,
            "diagnosis": "This is clearly early-stage arthritis, recommend ibuprofen",
            "treatment_plan": "Physical therapy 3x/week",
            "required_specialty_keywords": [],
            "required_service_keywords": [],
        }
    )
    _override_llm(fake)
    try:
        token = await register_and_get_token(client, "aiextract2@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={"text": "My father has some joint pain and needs help with daily activities."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "diagnosis" not in data
        assert "treatment_plan" not in data
        assert set(data.keys()) == {
            "age", "gender", "patient_type", "duration_days", "hours_per_day",
            "preferred_shift", "languages", "mobility_status",
            "matched_specialty_ids", "unmatched_specialty_keywords",
            "matched_service_ids", "unmatched_service_keywords",
        }
    finally:
        _clear_llm_override()


async def test_extraction_handles_unmatched_keywords_gracefully(client, seed_lookup):
    fake = _FakeLLMClient(
        {
            "required_specialty_keywords": ["Underwater Basket Weaving Therapy"],
            "required_service_keywords": ["Astral Projection Assistance"],
        }
    )
    _override_llm(fake)
    try:
        token = await register_and_get_token(client, "aiextract3@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={"text": "Some fairly generic long text describing a care need for someone."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["matched_specialty_ids"] == []
        assert data["unmatched_specialty_keywords"] == ["Underwater Basket Weaving Therapy"]
        assert data["matched_service_ids"] == []
        assert data["unmatched_service_keywords"] == ["Astral Projection Assistance"]
    finally:
        _clear_llm_override()


async def test_extraction_handles_garbage_llm_output_defensively(client, seed_lookup):
    """Out-of-range/invalid values from the model must never crash the
    endpoint or pass through unsanitized."""
    fake = _FakeLLMClient(
        {
            "age": 9999,
            "gender": "not-a-real-gender",
            "duration_days": -5,
            "hours_per_day": "not-a-number",
            "preferred_shift": "WHENEVER_I_FEEL_LIKE_IT",
            "mobility_status": "FLYING",
            "languages": "not-a-list",
            "required_specialty_keywords": "also-not-a-list",
        }
    )
    _override_llm(fake)
    try:
        token = await register_and_get_token(client, "aiextract4@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={"text": "A reasonably long piece of descriptive free text goes here."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["age"] is None
        assert data["gender"] is None
        assert data["duration_days"] is None
        assert data["hours_per_day"] is None
        assert data["preferred_shift"] is None
        assert data["mobility_status"] is None
        assert data["languages"] == []
        assert data["matched_specialty_ids"] == []
    finally:
        _clear_llm_override()


async def test_extraction_handles_non_json_llm_response(client, seed_lookup):
    """If the model returns something that isn't even valid JSON, the
    service must fail safe (empty extraction), not crash."""

    class _BrokenClient:
        async def extract_requirements(self, text: str) -> dict:
            return {}  # simulates AnthropicLLMClient's own fail-safe on bad JSON

    _override_llm(_BrokenClient())
    try:
        token = await register_and_get_token(client, "aiextract5@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={"text": "A reasonably long piece of descriptive free text goes here."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["age"] is None
        assert data["matched_specialty_ids"] == []
    finally:
        _clear_llm_override()


async def test_extraction_not_configured_returns_clear_error(client):
    """When no LLM client is available at all (e.g. LLM_API_KEY unset in
    production), the endpoint must fail with a clear, actionable error --
    not a generic 500."""

    async def _no_client_dep():
        return None

    app.dependency_overrides[get_llm_client_dep] = _no_client_dep
    try:
        token = await register_and_get_token(client, "aiextract6@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract",
            headers=headers,
            json={"text": "A reasonably long piece of descriptive free text goes here."},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "AI_NOT_CONFIGURED"
    finally:
        _clear_llm_override()


async def test_nurse_cannot_use_extraction(client):
    token = await register_and_get_token(client, "aiextractnurse@example.com", "NURSE")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/care-requests/extract",
        headers=headers,
        json={"text": "A reasonably long piece of descriptive free text goes here."},
    )
    assert resp.status_code == 403


async def test_extraction_text_too_short_rejected(client):
    fake = _FakeLLMClient({})
    _override_llm(fake)
    try:
        token = await register_and_get_token(client, "aiextract7@example.com", "PATIENT")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/care-requests/extract", headers=headers, json={"text": "short"}
        )
        assert resp.status_code == 422
    finally:
        _clear_llm_override()
