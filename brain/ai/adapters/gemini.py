"""Google Gemini adapter."""
import json
import re

from google import genai

from brain.config import settings


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.+?)\s*```", stripped, re.DOTALL)
        if match:
            return match.group(1).strip()
    return stripped


class GeminiAdapter:
    """LLM adapter for Google Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_model
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _build_config(
        self,
        *,
        system_instruction: str | None = None,
        response_mime_type: str | None = None,
    ):
        kwargs = {}
        if system_instruction:
            kwargs["systemInstruction"] = system_instruction
        if response_mime_type:
            kwargs["responseMimeType"] = response_mime_type
        return genai.types.GenerateContentConfig(**kwargs) if kwargs else None

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        response = self.client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._build_config(system_instruction=system_instruction),
        )
        return response.text or ""

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict | list:
        response = self.client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._build_config(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, (dict, list)):
            return parsed

        text = _extract_json_payload(response.text or "")
        return json.loads(text)
