"""Provider-agnostic LLM client.

The agent core depends on the LLMClient interface, not on a vendor SDK. Two
implementations ship here, Anthropic and OpenAI, with the same
structured-output discipline; `make_client` picks one.

Security notes:
- API keys come from the environment only. They are never logged, never
  echoed, never written to disk by this program.
- Every call demands schema-shaped JSON and is parsed and validated here;
  raw model text never crosses a boundary unvalidated, and a rejected reply
  is never quoted back to the model.
- A reply that was cut off or refused is an error, not something to guess
  at. A reply with no text is retried like any other invalid JSON.
"""
import json
import os
from typing import Callable, Optional, Protocol, Type, TypeVar

import pydantic_core
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

MAX_TOKENS = 2000
# Current Claude models think adaptively by default, and thinking tokens count
# toward max_tokens, so the Anthropic limit leaves room for thinking plus the
# JSON. Only the tokens actually generated are billed.
ANTHROPIC_MAX_TOKENS = 16000
SCHEMA_RETRIES = 2  # re-ask with the validation error appended
DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini"}


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        """Return a `schema`-validated object from the model."""
        ...


class SchemaRetryExhausted(RuntimeError):
    """Model failed to produce schema-valid JSON within the retry budget."""


class ModelResponseError(RuntimeError):
    """The provider's reply was cut off or refused, so it cannot be used."""


def make_client(provider: str, model: Optional[str] = None) -> "LLMClient":
    """Factory: the agent core never imports a vendor SDK directly."""
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"unknown LLM provider: {provider!r} (use 'anthropic' or 'openai')")
    model = model or DEFAULT_MODELS[provider]
    if provider == "anthropic":
        return AnthropicClient(model)
    return OpenAIClient(model)


def _extract_json(text: str) -> str:
    """Strip whitespace and a Markdown code fence, which some models add
    even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text[:4].lower() == "json":
            text = text[4:]
    return text.strip()


def _complete_json(send: Callable[[str], str], user: str, schema: Type[T]) -> T:
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
        text = _extract_json(send(prompt))
        try:
            # NaN, Infinity and 1e999 (which parses as infinity) are refused like
            # any invalid JSON: stdout and the audit log cannot carry them as JSON.
            reply = pydantic_core.from_json(text, allow_inf_nan=False)
            json.dumps(reply, allow_nan=False)
            return schema.model_validate(reply)
        except ValidationError as exc:
            # Field paths and messages only: pydantic's own text quotes the
            # rejected reply, which can carry injected tags such as "</task>",
            # and this line is not inside any fence.
            last_error = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'reply'}: {e['msg']}"
                for e in exc.errors(include_url=False, include_input=False)
            )[:500]
        except ValueError as exc:  # after ValidationError, which is a ValueError too
            last_error = f"invalid JSON: {exc}"[:500]
    raise SchemaRetryExhausted(
        f"No schema-valid {schema.__name__} after {SCHEMA_RETRIES} retries: {last_error}"
    )


class OpenAIClient:
    """Same contract as AnthropicClient: the reasoning loop can't tell them apart."""

    def __init__(self, model: str = DEFAULT_MODELS["openai"]) -> None:
        import openai  # imported here so tests can run without the SDK

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it before running; "
                "the agent never stores or logs it."
            )
        self._client = openai.OpenAI()
        self._model = model

    def _send(self, system: str, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            temperature=0,  # as repeatable as the model allows, for auditable runs
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise ModelResponseError(f"the reply was cut off at {MAX_TOKENS} tokens")
        refusal = getattr(choice.message, "refusal", None)
        if refusal:
            raise ModelResponseError(f"the model refused: {refusal}")
        return choice.message.content or ""

    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        return _complete_json(lambda prompt: self._send(system, prompt), user, schema)


class AnthropicClient:
    def __init__(self, model: str = DEFAULT_MODELS["anthropic"]) -> None:
        import anthropic  # imported here so tests can run without the SDK

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before running; "
                "the agent never stores or logs it."
            )
        self._client = anthropic.Anthropic()
        self._model = model

    def _send(self, system: str, prompt: str) -> str:
        # No temperature, top_p or top_k: current Claude models reject any
        # non-default sampling setting with HTTP 400.
        message = self._client.messages.create(
            model=self._model,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        # This call sends no tools and no stop sequences, so anything other
        # than end_turn (max_tokens, refusal, model_context_window_exceeded,
        # pause_turn) means there is no complete answer to read.
        if message.stop_reason != "end_turn":
            raise ModelResponseError(f"no complete answer: stop_reason={message.stop_reason}")
        # Thinking blocks can come before the text, so read the text blocks
        # by type rather than assuming the first block is text.
        return "".join(block.text for block in message.content if getattr(block, "type", None) == "text")

    def complete_json(self, system: str, user: str, schema: Type[T]) -> T:
        return _complete_json(lambda prompt: self._send(system, prompt), user, schema)
