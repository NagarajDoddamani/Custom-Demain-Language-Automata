"""Rich result tabs and output panels for JAN."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group

from compiler_dsl.ast_nodes import Program
from compiler_dsl.core import CompilerSession
from compiler_dsl.ui.display import render_parse_tree
from compiler_dsl.utils import OUTPUT_DIR


RESULT_TABS = ["Tokens", "Parse Tree", "Symbol Table", "TAC", "Output", "Logs"]
SAVED_TABS = ["Tokens", "Parse Tree", "Symbol Table", "TAC", "Output", "Logs"]


def render_tab_bar(active_tab: str, tabs: Sequence[str]) -> Panel:
    """Render the JAN tab strip used by the result viewer."""

    if len(tabs) > 3:
        top = _tab_line(tabs[:3], active_tab)
        bottom = _tab_line(tabs[3:], active_tab)
        content = Group(Align.center(top), Align.center(bottom))
    else:
        content = Align.center(_tab_line(tabs, active_tab))
    return Panel(content, border_style="magenta", box=box.ROUNDED, title="JAN Result Tabs")


def render_tokens_table(tokens: Iterable[Any]) -> Panel:
    """Render lexical tokens as a rich table."""

    table = Table(box=box.ROUNDED, border_style="cyan", header_style="bold magenta", expand=True)
    table.add_column("TOKEN", style="cyan")
    table.add_column("TYPE", style="white")
    table.add_column("LINE", justify="right", style="yellow")
    table.add_column("COLUMN", justify="right", style="yellow")

    rows_added = 0
    for token in tokens:
        if getattr(token, "type", "") == "EOF":
            continue
        token_type = "CONSTANT" if token.type in {"NUMBER", "STRING"} else token.type
        table.add_row(token.value, token_type, str(token.line), str(token.column))
        rows_added += 1

    if rows_added == 0:
        return _warning_panel("No tokens available. Run lexical analysis first.", "TOKENS")
    return Panel(table, border_style="cyan", box=box.ROUNDED, title="TOKENS")


def render_parse_tree_panel(program: Program | None) -> Panel:
    """Render the AST as a compact tree diagram."""

    if program is None:
        return _warning_panel("No parse tree available. Run syntax analysis first.", "PARSE TREE")
    tree_text = render_parse_tree(program)
    return Panel(tree_text, border_style="magenta", box=box.ROUNDED, title="PARSE TREE")


def render_symbol_table_panel(symbol_table: Any) -> Panel:
    """Render the semantic symbol table."""

    if symbol_table is None:
        return _warning_panel("No symbol table available. Run semantic analysis first.", "SYMBOL TABLE")

    table = Table(box=box.ROUNDED, border_style="green", header_style="bold magenta", expand=True)
    table.add_column("Variable", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Value", style="yellow")

    rows_added = 0
    for _, entry in symbol_table.items():
        value = "-" if entry.value is None else str(entry.value)
        table.add_row(entry.name, entry.type_name, value)
        rows_added += 1

    if rows_added == 0:
        return _warning_panel("Symbol table is empty.", "SYMBOL TABLE")
    return Panel(table, border_style="green", box=box.ROUNDED, title="SYMBOL TABLE")


def render_tac_panel(tac_lines: Sequence[str]) -> Panel:
    """Render the generated three-address code."""

    if not tac_lines:
        return _warning_panel("No TAC available. Run TAC generation first.", "TAC")

    table = Table(box=box.ROUNDED, border_style="yellow", header_style="bold magenta", expand=True)
    table.add_column("NO", justify="right", style="cyan")
    table.add_column("INSTRUCTION", style="white")
    for index, instruction in enumerate(tac_lines, start=1):
        table.add_row(str(index), instruction)
    return Panel(table, border_style="yellow", box=box.ROUNDED, title="TAC")


def render_program_output_panel(outputs: Sequence[str]) -> Panel:
    """Render the simulated program output."""

    if not outputs:
        return _warning_panel("No program output generated yet.", "OUTPUT")

    text = Text()
    for index, line in enumerate(outputs, start=1):
        text.append(line)
        if index < len(outputs):
            text.append("\n")
    return Panel(text, border_style="green", box=box.ROUNDED, title="OUTPUT")


def render_logs_panel(log_text: str) -> Panel:
    """Render compilation logs and execution traces."""

    if not log_text.strip():
        return _warning_panel("No logs available yet.", "LOGS")
    return Panel(log_text, border_style="magenta", box=box.ROUNDED, title="LOGS")


def render_file_panel(path: Path, title: str) -> Panel:
    """Render a saved text file as a panel."""

    if not path.exists():
        return _warning_panel(f"{title} file not found. Run the compiler first.", title.upper())
    return Panel(path.read_text(encoding="utf-8"), border_style="blue", box=box.ROUNDED, title=title.upper())


def build_current_view(session: CompilerSession, tab: str) -> Panel:
    """Return the current-session renderable for the selected tab."""

    normalized = tab.lower()
    if normalized == "tokens":
        return render_tokens_table(session.tokens)
    if normalized == "parse tree":
        return render_parse_tree_panel(session.program)
    if normalized == "symbol table":
        return render_symbol_table_panel(session.symbol_table)
    if normalized == "tac":
        return render_tac_panel(session.tac_lines)
    if normalized in {"program output", "output"}:
        return render_program_output_panel(session.program_output)
    if normalized == "logs":
        return render_logs_panel(session.show_steps_text())
    return _warning_panel("Unknown tab selected.", tab.upper())


def build_saved_view(tab: str) -> Panel:
    """Return a saved-output renderable for the selected tab."""

    normalized = tab.lower()
    if normalized == "tokens":
        return render_file_panel(OUTPUT_DIR / "tokens.txt", "Tokens")
    if normalized == "parse tree":
        return render_file_panel(OUTPUT_DIR / "parse_tree.txt", "Parse Tree")
    if normalized == "symbol table":
        return render_file_panel(OUTPUT_DIR / "symbol_table.txt", "Symbol Table")
    if normalized == "tac":
        return render_file_panel(OUTPUT_DIR / "tac.txt", "TAC")
    if normalized in {"program output", "output"}:
        return render_file_panel(OUTPUT_DIR / "output.txt", "Program Output")
    if normalized == "logs":
        return render_file_panel(OUTPUT_DIR / "logs.txt", "Logs")
    return _warning_panel("Unknown saved view selected.", tab.upper())


def _tab_line(tabs: Sequence[str], active_tab: str) -> Text:
    bar = Text()
    for index, tab in enumerate(tabs):
        label = f" {tab.upper()} "
        if tab == active_tab:
            bar.append(label, style="black on cyan bold")
        else:
            bar.append(label, style="cyan")
        if index < len(tabs) - 1:
            bar.append(" ")
    return bar


def _warning_panel(message: str, title: str) -> Panel:
    return Panel(message, border_style="yellow", box=box.ROUNDED, title=title)


