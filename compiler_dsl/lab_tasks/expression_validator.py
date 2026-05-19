"""Validate arithmetic expressions using Python's AST safely."""

from __future__ import annotations

import ast
from dataclasses import dataclass


ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)


@dataclass
class ExpressionValidator:
    expression: str

    def validate(self) -> bool:
        return validate_expression(self.expression)


def validate_expression(expression: str) -> bool:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return False
    return _is_allowed(tree.body)


def _is_allowed(node: ast.AST) -> bool:
    if isinstance(node, ast.BinOp):
        return isinstance(node.op, ALLOWED_BINOPS) and _is_allowed(node.left) and _is_allowed(node.right)
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, ALLOWED_UNARYOPS) and _is_allowed(node.operand)
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float))
    if isinstance(node, ast.Expression):
        return _is_allowed(node.body)
    return False


if __name__ == "__main__":
    samples = ["a+b*5", "a+*5"]
    for sample in samples:
        print(f"{sample} -> {'Valid' if validate_expression(sample) else 'Invalid'}")

