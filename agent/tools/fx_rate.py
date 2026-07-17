"""External tool: live FX rates (keyless public API, HTTPS, pinned host).

Network isolation: this module is the only place in the codebase that makes
an outbound request, and it can only reach the single pinned host below.
"""
import httpx
from pydantic import BaseModel, Field

from agent.tools.registry import ToolSpec

_HOST = "https://open.er-api.com"
_TIMEOUT_SECONDS = 10


class FxRateInput(BaseModel):
    base: str = Field(pattern=r"^[A-Z]{3}$", description="ISO currency code, e.g. USD")
    quote: str = Field(pattern=r"^[A-Z]{3}$", description="ISO currency code, e.g. PHP")


def _fetch_rate(params: FxRateInput) -> dict:
    response = httpx.get(f"{_HOST}/v6/latest/{params.base}", timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    if payload.get("result") != "success":
        raise RuntimeError(f"FX API returned {payload.get('result')!r}")
    rate = payload["rates"].get(params.quote)
    if rate is None:
        raise RuntimeError(f"no rate for {params.quote}")
    return {
        "base": params.base,
        "quote": params.quote,
        "rate": rate,
        "as_of_utc": payload.get("time_last_update_utc", "unknown"),
        "source": _HOST,
    }


SPEC = ToolSpec(
    name="fx_rate",
    description="Live foreign-exchange rate between two ISO currency codes",
    input_schema=FxRateInput,
    fn=_fetch_rate,
    readonly=True,
)
