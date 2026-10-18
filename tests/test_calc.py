"""The calculator must compute deterministically and refuse everything that isn't arithmetic."""
import pytest

from agent.tools.calc import CalcInput, _calculate


def test_deterministic_arithmetic():
    assert _calculate(CalcInput(expression="3 * 40 + 18"))["value"] == 138
    assert _calculate(CalcInput(expression="round(138 * 61.651002)"))["value"] == 8508


def test_rejects_names_and_imports():
    for evil in [
        "__import__('os').system('id')",
        "open('/etc/passwd')",
        "().__class__.__mro__",
        "x + 1",
        "round(1, ndigits=0)",  # keywords blocked
    ]:
        with pytest.raises((ValueError, SyntaxError)):
            _calculate(CalcInput(expression=evil))


def test_rejects_oversized_expression():
    with pytest.raises(Exception):
        CalcInput(expression="1+" * 200 + "1")


def test_refuses_runaway_powers_before_computing_them():
    for runaway in [
        "9**9**9", "2**5000", "10**1001", "(-7)**2000", "10**309",
        "*".join(["9**999"] * 5),  # a product of allowed-looking powers
        "round(1, -999999999)",    # round() would compute 10**999999999 internally
        "round(1, -10**1000)",
        "1e308 * 10",              # float overflow to inf
    ]:
        with pytest.raises(ValueError):
            _calculate(CalcInput(expression=runaway))
    assert _calculate(CalcInput(expression="round(1000 * 1.005**360)"))["value"] == 6023  # 30 years of monthly growth


def test_refuses_booleans_and_complex_results():
    for bad in ["True + 1", "(-8) ** 0.5"]:
        with pytest.raises(ValueError):
            _calculate(CalcInput(expression=bad))
