"""Tabular text rendering with a tabulate fallback."""

from __future__ import annotations

from typing import Iterable, Sequence

try:
    from tabulate import tabulate
except Exception:  # pragma: no cover - fallback when tabulate is unavailable
    def tabulate(
        rows: Iterable[Sequence[object]],
        headers: Sequence[str],
        tablefmt: str = "grid",
    ) -> str:
        return _fallback_table(rows, headers)


def render_table(rows: Iterable[Sequence[object]], headers: Sequence[str], tablefmt: str = "grid") -> str:
    """Render a table using tabulate when present, otherwise a simple ASCII table."""

    return tabulate(rows, headers=headers, tablefmt=tablefmt)


def _fallback_table(rows: Iterable[Sequence[object]], headers: Sequence[str]) -> str:
    rows = [list(map(str, row)) for row in rows]
    headers = list(map(str, headers))
    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            if index >= len(widths):
                widths.append(len(cell))
            else:
                widths[index] = max(widths[index], len(cell))

    def format_row(row: Sequence[str]) -> str:
        cells = [cell.ljust(widths[i]) for i, cell in enumerate(row)]
        return " | ".join(cells)

    separator = "-+-".join("-" * width for width in widths)
    output = [format_row(headers), separator]
    for row in rows:
        output.append(format_row(row))
    return "\n".join(output)

