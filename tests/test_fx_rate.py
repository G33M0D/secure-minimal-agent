"""The FX tool with the network replaced by a stub: no request leaves the machine."""
from agent.tools import fx_rate
from agent.tools.fx_rate import SPEC, FxRateInput
from agent.tools.registry import ToolRegistry


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(SPEC)
    return reg


def test_reads_the_rate_from_the_pinned_host_with_a_timeout(monkeypatch):
    seen = {}

    def fake_get(url, timeout):
        seen.update(url=url, timeout=timeout)
        return FakeResponse({"result": "success", "rates": {"PHP": 61.5}, "time_last_update_utc": "test time"})

    monkeypatch.setattr(fx_rate.httpx, "get", fake_get)
    data = fx_rate._fetch_rate(FxRateInput(base="USD", quote="PHP"))
    assert data["rate"] == 61.5 and data["as_of_utc"] == "test time"
    assert seen == {"url": "https://open.er-api.com/v6/latest/USD", "timeout": 10}


def test_api_failure_comes_back_as_data(monkeypatch):
    monkeypatch.setattr(fx_rate.httpx, "get", lambda url, timeout: FakeResponse({"result": "error"}))
    result = _registry().call("fx_rate", {"base": "USD", "quote": "PHP"})
    assert not result.ok and "FX API returned 'error'" in result.error


def test_unknown_quote_currency_comes_back_as_data(monkeypatch):
    monkeypatch.setattr(fx_rate.httpx, "get", lambda url, timeout: FakeResponse({"result": "success", "rates": {}}))
    result = _registry().call("fx_rate", {"base": "USD", "quote": "XYZ"})
    assert not result.ok and "no rate for XYZ" in result.error
