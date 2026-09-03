"""
AI requirement extraction (Section 22): the patient writes a free-text
description of their situation; an LLM extracts structured scheduling/
demographic/care-type fields from it, which are then fed into the same
matching engine built in Phase 4 (MatchingService) -- no changes needed
there, since AIExtractionService produces the same shape of structured
data a human filling out the form would.

Critical safety boundary (Section 2, restated for this specific call):
the model is instructed, explicitly and repeatedly, to never diagnose a
condition, never suggest treatment or medication, and never comment on
the medical content at all beyond extracting a few descriptive keywords
(e.g. "post-operative", "elderly") needed to match against the specialty
catalog. It is a logistics/scheduling extractor, not a clinical tool.
"""
import json
from typing import Protocol

from anthropic import AsyncAnthropic

from app.core.config import settings

EXTRACTION_SYSTEM_PROMPT = """You extract SCHEDULING AND LOGISTICS fields from a home-care patient's free-text description, for a nurse-matching system. You are not a medical professional and this is not a clinical tool.

STRICT RULES:
- NEVER diagnose any condition, NEVER suggest treatment, medication, or clinical action of any kind.
- NEVER include medical advice, opinions, or interpretations in your output.
- Only extract the specific logistics fields listed below. If a field is not clearly stated, use null.
- For required_specialty_keywords and required_service_keywords, extract only short descriptive phrases already implied by the text (e.g. "post-operative", "elderly care", "wound care") -- do not invent clinical detail that was not stated.
- Output ONLY a single JSON object matching this exact schema, no other text:

{
  "age": <integer or null>,
  "gender": <"MALE" or "FEMALE" or null>,
  "patient_type": <short string like "elderly", "child", "adult", or null>,
  "duration_days": <integer or null>,
  "hours_per_day": <number or null>,
  "required_specialty_keywords": [<short strings>],
  "required_service_keywords": [<short strings>],
  "preferred_shift": <"MORNING", "EVENING", "NIGHT", "HOURS_24", "CUSTOM", or null>,
  "languages": [<short strings, e.g. "ar", "en">],
  "mobility_status": <"INDEPENDENT", "NEEDS_ASSISTANCE", "WHEELCHAIR", "BEDRIDDEN", or null>
}
"""


class LLMClient(Protocol):
    async def extract_requirements(self, text: str) -> dict:
        """Returns a dict matching the schema in EXTRACTION_SYSTEM_PROMPT."""
        ...


class AnthropicLLMClient:
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def extract_requirements(self, text: str) -> dict:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=500,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        try:
            return json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            return {}


def get_llm_client() -> LLMClient | None:
    """Returns None when no API key is configured -- callers must handle
    this gracefully (AIExtractionService raises a clear, actionable error
    rather than letting a None client blow up downstream)."""
    if not settings.LLM_API_KEY:
        return None
    return AnthropicLLMClient(api_key=settings.LLM_API_KEY)
