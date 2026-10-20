import json
import os
import re
from typing import Optional

from .prompts import SYSTEM_PROMPT, build_user_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Thin wrapper around the Anthropic Messages API returning parsed JSON."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("BUG_ANALYZER_MODEL", DEFAULT_MODEL)
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise LLMError("Install the 'anthropic' package to use LLM analysis") from e
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def analyze(self, report: str) -> dict:
        try:
            resp = self._get_client().messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.2,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(report)}],
            )
        except Exception as e:  # network/auth/rate-limit
            raise LLMError(f"LLM request failed: {e}") from e

        raw = "".join(b.text for b in resp.content if getattr(b, "text", None))
        return self.parse_json(raw)

    @staticmethod
    def parse_json(raw: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", cleaned, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
        raise LLMError("LLM returned invalid JSON")
