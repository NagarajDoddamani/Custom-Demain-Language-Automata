"""Recognize whether a token is a keyword, identifier, constant, operator, or separator."""

from __future__ import annotations

import re
from dataclasses import dataclass


KEYWORDS = {"num", "dec", "text", "show", "when", "otherwise", "loop"}
OPERATORS = {"+", "-", "*", "/", "=", "<", ">", "<=", ">=", "==", "!="}
SEPARATORS = {";", ",", "(", ")", "{", "}"}


@dataclass
class TokenRecognizer:
    token: str

    def recognize(self) -> str:
        return recognize_token(self.token)


def recognize_token(text: str) -> str:
    candidate = text.strip()
    if candidate in KEYWORDS:
        return "Keyword"
    if candidate in OPERATORS:
        return "Operator"
    if candidate in SEPARATORS:
        return "Separator"
    if re.fullmatch(r"\d+(?:\.\d+)?", candidate):
        return "Constant"
    if re.fullmatch(r'"(?:\\.|[^"\\])*"', candidate):
        return "Constant"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
        return "Identifier"
    return "Unknown"


if __name__ == "__main__":
    samples = ["num", "value", "123", "+"]
    for sample in samples:
        print(f"{sample} -> {recognize_token(sample)}")

