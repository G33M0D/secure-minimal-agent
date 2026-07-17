"""Deterministic arithmetic tool.

LLMs are unreliable at arithmetic, so the agent is not allowed to do money
math in its head: numeric computation is delegated to this tool, where the
answer is exact and auditable.

Security: expressions are parsed with `ast` and evaluated against an
allowlist of node types (numbers, + - * / ** %, parentheses, unary minus,
round/min/max). There is NO eval/exec — anything outside the allowlist
(names, attributes, calls to other functions, subscripts) is rejected.
Same deny-by-default philosophy as the tool registry itself.
"""
import ast
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


class CalcInput(BaseModel):
    expression: str = Field(
        min_length=1,
        max_length=_MAX_EXPR_LENGTH,
        description="Pure arithmetic, e.g. 'round((3 * 40 + 18) * 61.651002)'",
    )


def _eval_node(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        return _BINARY_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _ALLOWED_CALLS
        and not node.keywords
    ):
        return _ALLOWED_CALLS[node.func.id](*[_eval_node(a) for a in node.args])
    raise ValueError(f"disallowed expression element: {ast.dump(node)[:80]}")


def _calculate(params: CalcInput) -> dict:
    tree = ast.parse(params.expression, mode="eval")
    value = _eval_node(tree)
    return {"expression": params.expression, "value": value}


SPEC = ToolSpec(
    name="calc",
    description="Exact arithmetic (+ - * / ** %, round/min/max). Use for ALL numeric computation.",
    input_schema=CalcInput,
    fn=_calculate,
    readonly=True,
)
