"""Evaluate arithmetic expressions safely using Python's AST."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Mapping, Optional


ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}
ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


@dataclass
class ExpressionEvaluator:
    expression: str
    variables: Optional[Mapping[str, Any]] = None

    def evaluate(self) -> Any:
        return evaluate_expression(self.expression, self.variables)


def evaluate_expression(expression: str, variables: Optional[Mapping[str, Any]] = None) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid arithmetic expression: {expression}") from exc
    return _evaluate_node(tree.body, variables or {})


def _evaluate_node(node: ast.AST, variables: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")

    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Unknown variable: {node.id}")
        return variables[node.id]

    if isinstance(node, ast.BinOp):
        operator_type = type(node.op)
        if operator_type not in ALLOWED_BINOPS:
            raise ValueError("Unsupported operator in expression")
        left = _evaluate_node(node.left, variables)
        right = _evaluate_node(node.right, variables)
        if operator_type is ast.Div and right == 0:
            raise ValueError("Division by zero")
        return ALLOWED_BINOPS[operator_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operator_type = type(node.op)
        if operator_type not in ALLOWED_UNARYOPS:
            raise ValueError("Unsupported unary operator in expression")
        operand = _evaluate_node(node.operand, variables)
        return ALLOWED_UNARYOPS[operator_type](operand)

    raise ValueError("Unsupported expression element")


if __name__ == "__main__":
    sample = "(5+3)*2"
    print(evaluate_expression(sample))

