"""The calculator must compute exactly and refuse everything that isn't arithmetic."""
import pytest

from agent.tools.calc import CalcInput, _calculate


def test_exact_arithmetic():
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
