"""Shared utilities for the interactive DSL compiler console app."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from compiler_dsl.ast_nodes import Block, IfStatement, Program, Statement, WhileStatement


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
OUTPUT_DIR = PACKAGE_DIR / "outputs"
SAMPLE_PROGRAMS_DIR = PACKAGE_DIR / "sample_programs"


def ensure_output_dir() -> Path:
    """Create the outputs directory if it does not already exist."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def save_text_file(path: Path, content: str) -> None:
    """Write text content to a file, creating parent folders when needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def clear_screen() -> None:
    """Clear the terminal screen on Windows or Unix-like systems."""

    if not sys.stdout.isatty():
        return
    os.system("cls" if os.name == "nt" else "clear")


def timestamp() -> str:
    """Return a short human-readable timestamp string."""

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def count_program_statements(program: Program) -> int:
    """Count all executable statements in the AST, including nested blocks."""

    return _count_statements(program.statements)


def _count_statements(statements: Iterable[Statement]) -> int:
    count = 0
    for statement in statements:
        if isinstance(statement, Block):
            count += _count_statements(statement.statements)
        elif isinstance(statement, IfStatement):
            count += 1
            count += _count_statements(statement.then_branch.statements)
            if statement.else_branch is not None:
                count += _count_statements(statement.else_branch.statements)
        elif isinstance(statement, WhileStatement):
            count += 1
            count += _count_statements(statement.body.statements)
        else:
            count += 1
    return count
