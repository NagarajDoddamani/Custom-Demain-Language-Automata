"""Validate simple C statements such as headers and declarations."""

from __future__ import annotations

import re
from dataclasses import dataclass


HEADER_RE = re.compile(r"^\s*#include\s*<stdio\.h>\s*$")
DECL_RE = re.compile(r"^\s*(int|float|double|char)\s+[A-Za-z_][A-Za-z0-9_]*\s*;\s*$")


@dataclass
class CStatementChecker:
    source: str

    def validate(self) -> tuple[bool, str]:
        return check_c_statements(self.source)


def check_c_statements(source: str) -> tuple[bool, str]:
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines:
        return False, "Invalid: empty C source"

    if not HEADER_RE.fullmatch(lines[0]):
        return False, "Invalid header section"

    if len(lines) == 1:
        return True, "Valid C source with header only"

    for line in lines[1:]:
        if not DECL_RE.fullmatch(line):
            return False, f"Invalid definition/declaration: {line}"

    return True, "Valid C statements"


if __name__ == "__main__":
    sample = "#include<stdio.h>\nint a;"
    print(check_c_statements(sample)[1])

