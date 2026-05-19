"""Dashboard rendering helpers for the compiler simulator."""

from __future__ import annotations

from typing import Any, List, Sequence

from compiler_dsl.ui.colors import Fore, Style
from compiler_dsl.ui.table import render_table


STAGES = [
    ("lexical", "Lexical Analysis"),
    ("syntax", "Syntax Analysis"),
    ("semantic", "Semantic Analysis"),
    ("tac", "TAC Generation"),
]


def render_dashboard(session: Any, active_stage: str | None = None) -> str:
    """Render the dashboard header and live compiler status board."""

    header = [
        "=" * 56,
        f"{'DSL COMPILER SIMULATOR':^56}",
        "=" * 56,
    ]
    details = render_table(
        [
            ("Project", "Compiler Front-End"),
            ("Language", "Custom DSL"),
            ("Input File", getattr(session, "source_name", "Untitled")),
            ("Status", _status_label(getattr(session, "overall_status", "READY"))),
        ],
        headers=("Field", "Value"),
        tablefmt="grid",
    )
    stage_rows = []
    for key, label in STAGES:
        status = getattr(session, "stage_statuses", {}).get(key, "WAITING")
        if active_stage == key:
            status = "ACTIVE"
        stage_rows.append((label, _status_label(status)))
    stage_board = render_table(stage_rows, headers=("Compiler Phase", "Status"), tablefmt="grid")
    return "\n".join(header + [details, stage_board])


def render_status_line(stage: str, status: str) -> str:
    """Render one status line for step-by-step demonstrations."""

    return f"{_status_label(status)} {stage}"


def _status_label(status: str) -> str:
    """Return a colored status label."""

    normalized = status.upper()
    if normalized == "DONE":
        return f"{Fore.GREEN}[DONE]{Style.RESET_ALL}"
    if normalized == "ACTIVE":
        return f"{Fore.YELLOW}[ACTIVE]{Style.RESET_ALL}"
    if normalized == "WAITING":
        return f"{Fore.WHITE}[WAITING]{Style.RESET_ALL}"
    if normalized == "ERROR":
        return f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
    if normalized == "READY":
        return f"{Fore.CYAN}[READY]{Style.RESET_ALL}"
    if normalized == "SUCCESS":
        return f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL}"
    return f"{Fore.CYAN}[{normalized}]{Style.RESET_ALL}"

