"""Deterministic arithmetic tool.

LLMs are unreliable at arithmetic, so the agent is not allowed to do money
math in its head: numeric computation is delegated to this tool, where the
result is deterministic and auditable. It uses Python's own int and float
arithmetic, so floats behave as usual (0.1 + 0.2 gives 0.30000000000000004)
and round() rounds halves to even (round(2.5) is 2).

Security: expressions are parsed with `ast` and evaluated against an
allowlist of node types (numbers, + - * / ** %, parentheses, unary minus,
round/min/max). There is NO eval/exec: anything outside the allowlist
(names, attributes, calls to other functions, subscripts, booleans) is
rejected. Every intermediate result is capped (whole numbers at 1000 bits,
about 300 digits; floats must be finite), powers are checked before they are
computed, and round()'s digits argument is limited, so a short expression
such as 9**9**9 or round(1, -999999999) cannot tie up the process, and every
result can be written to JSON and compared as a float. Same deny-by-default
philosophy as the tool registry.
"""
import ast
import math
import operator
from typing import Union

from pydantic import BaseModel, Field

from agent.tools.registry import ToolSpec

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_ALLOWED_CALLS = {"round": round, "min": min, "max": max}
_MAX_EXPR_LENGTH = 200
_MAX_EXPONENT = 1000  # enough for compound interest over decades of monthly periods
_MAX_RESULT_BITS = 1000  # about 300 digits: fits a float, and far below any str() limit
_MAX_ROUND_DIGITS = 100


def _check_power(base: Union[int, float], exponent: Union[int, float]) -> None:
    """Refuse powers whose cost or size would run away before computing them."""
    if abs(exponent) > _MAX_EXPONENT:
        raise ValueError(f"exponent {exponent} is larger than {_MAX_EXPONENT}")
    if abs(base) > 1 and abs(exponent) * math.log2(abs(base)) > _MAX_RESULT_BITS:
        raise ValueError(f"result of {base} ** {exponent} would be too large")


def _check_result(value: Union[int, float]) -> Union[int, float]:
    """Refuse a result that is too large to handle safely or is not a real number."""
    if isinstance(value, complex):  # e.g. (-8) ** 0.5
        raise ValueError("the result is not a real number")
    if isinstance(value, int) and value.bit_length() > _MAX_RESULT_BITS:
        raise ValueError("the result is too large (more than about 300 digits)")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("the result is not a finite number")
    return value


class CalcInput(BaseModel):
    expression: str = Field(
        min_length=1,
        max_length=_MAX_EXPR_LENGTH,
        description="Pure arithmetic, e.g. 'round((3 * 40 + 18) * 61.651002)'",
    )


def _eval_node(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return _check_result(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow):
            _check_power(left, right)
        return _check_result(_BINARY_OPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return _check_result(-_eval_node(node.operand))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _ALLOWED_CALLS
        and not node.keywords
    ):
        args = [_eval_node(a) for a in node.args]
        # round(x, -n) makes Python compute 10**n internally: limit n first.
        if node.func.id == "round" and len(args) == 2 and abs(args[1]) > _MAX_ROUND_DIGITS:
            raise ValueError(f"round() digits must be between -{_MAX_ROUND_DIGITS} and {_MAX_ROUND_DIGITS}")
        return _check_result(_ALLOWED_CALLS[node.func.id](*args))
    raise ValueError(f"disallowed expression element: {ast.dump(node)[:80]}")


def _calculate(params: CalcInput) -> dict:
    tree = ast.parse(params.expression, mode="eval")
    value = _eval_node(tree)
    return {"expression": params.expression, "value": value}


SPEC = ToolSpec(
    name="calc",
    description=(
        "Deterministic arithmetic (+ - * / ** %, round/min/max; floats as in Python, "
        "round() rounds halves to even). Use for ALL numeric computation."
    ),
    input_schema=CalcInput,
    fn=_calculate,
    readonly=True,
)
