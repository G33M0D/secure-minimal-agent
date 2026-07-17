"""Provider-agnostic LLM client.

The agent core depends on this interface, not on a vendor SDK. The Anthropic
implementation ships here; an OpenAI implementation is a ~30-line drop-in
(same structured-output discipline, different SDK).

Security notes:
- API key comes from the environment only. It is never logged, never echoed,
  never written to disk by this program.
- Temperature 0: deterministic-as-possible behavior for auditable runs.
- Every call demands schema-shaped JSON and is parsed/validated by the caller;
  raw model text never crosses a boundary unvalidated.
"""
import json
import os
from typing import Protocol, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

MAX_TOKENS = 2000
SCHEMA_RETRIES = 2  # re-ask with the validation error appended


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        """Return a `schema`-validated object from the model."""
        ...


class SchemaRetryExhausted(RuntimeError):
    """Model failed to produce schema-valid JSON within the retry budget."""


def make_client(provider: str) -> "LLMClient":
    """Factory: the agent core never imports a vendor SDK directly."""
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    raise ValueError(f"unknown LLM provider: {provider!r} (use 'anthropic' or 'openai')")


class OpenAIClient:
    """Same contract as AnthropicClient — the reasoning loop can't tell them apart."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        import openai  # imported here so tests can run without the SDK

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it before running; "
                "the agent never stores or logs it."
            )
        self._client = openai.OpenAI()
        self._model = model

    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        request = (
            f"{user}\n\n"
            f"Respond with ONLY a JSON object matching this JSON schema "
            f"(no prose, no markdown fences):\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        last_error = ""
        for _ in range(1 + SCHEMA_RETRIES):
            prompt = request if not last_error else (
                f"{request}\n\nYour previous response was invalid: "
                f"{last_error}\nReturn corrected JSON only."
            )
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            try:
                return schema.model_validate_json(text)
            except ValidationError as exc:
                last_error = str(exc)[:500]
        raise SchemaRetryExhausted(
            f"No schema-valid {schema.__name__} after {SCHEMA_RETRIES} retries: {last_error}"
        )


class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-5") -> None:
        import anthropic  # imported here so tests can run without the SDK

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before running; "
                "the agent never stores or logs it."
            )
        self._client = anthropic.Anthropic()
        self._model = model

    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        """Ask for JSON matching `schema`; on invalid output, retry with the
        validator's error message appended so the model can self-correct."""
        request = (
            f"{user}\n\n"
            f"Respond with ONLY a JSON object matching this JSON schema "
            f"(no prose, no markdown fences):\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        last_error = ""
        for _ in range(1 + SCHEMA_RETRIES):
            prompt = request if not last_error else (
                f"{request}\n\nYour previous response was invalid: "
                f"{last_error}\nReturn corrected JSON only."
            )
            message = self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.strip("`").removeprefix("json").strip()
            try:
                return schema.model_validate_json(text)
            except ValidationError as exc:
                last_error = str(exc)[:500]
        raise SchemaRetryExhausted(
            f"No schema-valid {schema.__name__} after {SCHEMA_RETRIES} retries: {last_error}"
        )
