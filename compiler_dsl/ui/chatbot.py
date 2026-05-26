"""Chatbot-style terminal UI helpers for JAN."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:
    from pyfiglet import Figlet
except Exception:  # pragma: no cover - optional dependency
    Figlet = None

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from compiler_dsl.ui.display import compiler_explanation, render_error, render_source_code


console = Console(width=110)
BOT_PREFIX = "JAN >"
JAN_TITLE = "JAN"
JAN_SUBTITLE = "JAN - Intelligent DSL Compiler Assistant"
JAN_TAGLINE = "Bot Style UI"
JAN_ASCII_LOGO = r"""     JJJJJ   AAAAA   N   N
       J     A   A   NN  N
       J     AAAAA   N N N
     J J     A   A   N  NN
      J      A   A   N   N"""


@dataclass(frozen=True)
class MenuOption:
    number: str
    title: str
    description: str


MAIN_MENU_OPTIONS = [
    MenuOption("1", "Run Full Compilation", "Compile the loaded DSL program automatically."),
    MenuOption("2", "Step-by-Step Demonstration", "Pause between phases and explain each stage."),
    MenuOption("3", "Open DSL Editor", "Type DSL code directly in the terminal."),
    MenuOption("4", "View Compilation Outputs", "Open saved compiler outputs from the outputs folder."),
    MenuOption("5", "Help", "Learn how to use JAN and the compiler phases."),
    MenuOption("6", "Exit", "Close the compiler assistant."),
]


def render_banner() -> Panel:
    """Render the JAN startup banner."""

    logo = _logo_text()
    subtitle = Text(JAN_SUBTITLE, style="bold white")
    tagline = Text(JAN_TAGLINE, style="cyan")
    return Panel(
        Group(Align.center(logo), Align.center(subtitle), Align.center(tagline)),
        border_style="magenta",
        box=box.DOUBLE,
        padding=(0, 2),
        title=JAN_TITLE,
    )


def bot_line(message: str, tone: str = "cyan") -> Text:
    """Return a single chatbot-style line."""

    text = Text()
    text.append(BOT_PREFIX, style="bold cyan")
    text.append(" ")
    text.append(message, style=tone)
    return text


def bot_say(message: str, tone: str = "cyan") -> None:
    """Print a chatbot-style message."""

    console.print(bot_line(message, tone=tone))


def bot_success(message: str) -> None:
    """Print a success message from the assistant."""

    bot_say(message, tone="green")


def bot_warning(message: str) -> None:
    """Print a warning message from the assistant."""

    bot_say(message, tone="yellow")


def bot_error(message: str) -> None:
    """Print an error message from the assistant."""

    bot_say(message, tone="red")


def welcome_name() -> str:
    """Return a friendly name for the welcome message."""

    raw = (os.getenv("COMPILERBOT_NAME") or os.getenv("USERNAME") or os.getenv("USER") or "").strip()
    if not raw or len(raw) < 3 or raw.lower() in {"hp", "user", "admin", "root", "compiler explorer"}:
        return "Nagaraj"
    return raw.title()


def render_welcome_card(name: str | None = None) -> Panel:
    """Render the welcome card shown at startup."""

    display_name = name or welcome_name()
    message = Group(
        bot_line(f"Welcome {display_name}", tone="white"),
        bot_line("Ready to compile your DSL program.", tone="cyan"),
    )
    return Panel(message, border_style="cyan", title="JAN", box=box.ROUNDED)


def render_menu_panel() -> Panel:
    """Render the main menu as a chatbot-friendly panel."""

    table = Table.grid(padding=(0, 1))
    table.add_column(justify="right", style="bold cyan", width=4)
    table.add_column(style="white")
    table.add_column(style="dim")

    for option in MAIN_MENU_OPTIONS:
        table.add_row(f"[{option.number}]", option.title, option.description)

    content = Group(
        bot_line("Select an option", tone="cyan"),
        table,
    )
    return Panel(content, border_style="cyan", box=box.ROUNDED, title="JAN Menu")


def render_status_panel(session: Any) -> Panel:
    """Render the live compiler status sidebar."""

    details = Table.grid(padding=(0, 1))
    details.add_column(justify="left", style="bold magenta")
    details.add_column(justify="left", style="white")
    details.add_row("Project", "JAN - Intelligent DSL Compiler Assistant")
    details.add_row("Language", "Custom DSL")
    details.add_row("Input File", getattr(session, "source_name", "Untitled"))
    details.add_row("Status", _status_style(getattr(session, "overall_status", "READY")))

    phases = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta", expand=True)
    phases.add_column("Status Panel", style="white")
    phases.add_column("State", justify="center")

    stage_map = getattr(session, "stage_statuses", {})
    for key, label in [
        ("lexical", "Lexical Analysis"),
        ("syntax", "Syntax Analysis"),
        ("semantic", "Semantic Analysis"),
        ("tac", "TAC Generation"),
    ]:
        phases.add_row(label, _phase_state(stage_map.get(key, "WAITING")))

    return Panel(Group(details, phases), border_style="bright_black", box=box.ROUNDED, title="JAN Status Panel")


def render_stage_panel(stage_title: str, explanation: str | None = None) -> Panel:
    """Render a visual stage card for compiler phases."""

    body = Group(
        bot_line(f"Starting {stage_title}...", tone="cyan"),
        Text(explanation or compiler_explanation(stage_title.lower().split()[0]), style="white"),
    )
    return Panel(body, border_style="magenta", box=box.ROUNDED, title=stage_title.upper())


def render_source_panel(source_code: str, source_name: str | None = None) -> Panel:
    """Render the currently loaded DSL source code."""

    text = render_source_code(source_code)
    title = f"Source: {source_name}" if source_name else "Source Code"
    return Panel(text, border_style="blue", box=box.ROUNDED, title=title)


def render_summary_panel(session: Any, success: bool = True) -> Panel:
    """Render the final compilation dashboard summary."""

    stats = session.statistics()
    summary = Table(box=box.SIMPLE_HEAVY, expand=True, show_lines=False)
    summary.add_column("Metric", style="bold magenta")
    summary.add_column("Value", style="white")

    summary.add_row("Lexical Analysis", _summary_label(session.stage_statuses.get("lexical", "WAITING")))
    summary.add_row("Syntax Analysis", _summary_label(session.stage_statuses.get("syntax", "WAITING")))
    summary.add_row("Semantic Analysis", _summary_label(session.stage_statuses.get("semantic", "WAITING")))
    summary.add_row("TAC Generation", _summary_label(session.stage_statuses.get("tac", "WAITING")))
    summary.add_row("Tokens Generated", str(stats["total_tokens"]))
    summary.add_row("Variables Declared", str(stats["variables_declared"]))
    summary.add_row("Temporary Variables", str(stats["temporary_vars"]))
    summary.add_row("Program Output Lines", str(stats.get("program_output_lines", 0)))
    summary.add_row("Compilation Time", f"{stats['compilation_time']:.2f} sec")

    title = "JAN COMPILATION SUCCESSFUL" if success else "JAN COMPILATION STOPPED"
    border = "green" if success else "red"
    header_lines = [Text(title, justify="center", style=f"bold {border}")]
    if success:
        header_lines.append(Text("Program Output Ready", justify="center", style="cyan"))
    else:
        header_lines.append(Text("Fix the highlighted issue and compile again.", justify="center", style="yellow"))
    header = Panel(
        Group(*header_lines),
        border_style=border,
        box=box.DOUBLE,
    )
    return Panel(Group(header, summary), border_style=border, box=box.ROUNDED, title="JAN Dashboard")


def render_error_panel(kind: str, message: str, source_code: str = "") -> Panel:
    """Render a user-friendly error assistant panel."""

    text = render_error(kind, message, source_code)
    return Panel(text, border_style="red", box=box.ROUNDED, title="JAN Error Assistant")


def render_saved_files_panel() -> Panel:
    """Render a small panel describing the saved outputs feature."""

    content = Group(
        bot_line("Saved outputs are stored in the outputs folder.", tone="yellow"),
        bot_line("Use the result tabs to revisit tokens, parse tree, TAC, logs, and program output.", tone="white"),
    )
    return Panel(content, border_style="yellow", box=box.ROUNDED, title="JAN Saved Outputs")


def render_help_panel() -> Panel:
    """Render a compact help panel for the JAN assistant."""

    help_table = Table.grid(padding=(0, 1))
    help_table.add_column(style="bold cyan", width=22)
    help_table.add_column(style="white")
    help_table.add_row("Run Full Compilation", "Compiles the current DSL program from start to finish.")
    help_table.add_row("Step-by-Step Demo", "Explains each compiler phase with short pauses.")
    help_table.add_row("Open DSL Editor", "Type DSL code directly and compile it immediately.")
    help_table.add_row("View Outputs", "Open saved tokens, parse tree, TAC, output, and logs.")
    help_table.add_row("Help", "Show this guide again.")
    help_table.add_row("Exit", "Close the JAN assistant.")

    tips = Group(
        bot_line("JAN explains each compiler phase in simple language.", tone="cyan"),
        bot_line("Use show(...) to print output from the DSL.", tone="white"),
        bot_line("Type END in editor mode when you finish entering code.", tone="white"),
    )
    return Panel(Group(help_table, tips), border_style="cyan", box=box.ROUNDED, title="JAN Help")


def _logo_text() -> Text:
    if Figlet is not None:
        try:
            return Text(Figlet(font="slant").renderText(JAN_TITLE), style="bold magenta")
        except Exception:
            pass
    return Text(JAN_ASCII_LOGO, style="bold cyan")


def _phase_state(status: str) -> Text:
    normalized = status.upper()
    if normalized == "DONE":
        return Text("DONE", style="green")
    if normalized == "ACTIVE":
        return Text("ACTIVE", style="yellow")
    if normalized == "ERROR":
        return Text("ERROR", style="red")
    if normalized == "WAITING":
        return Text("WAITING", style="dim")
    return Text(normalized, style="cyan")


def _summary_label(status: str) -> Text:
    normalized = status.upper()
    if normalized == "DONE":
        return Text("SUCCESS", style="green")
    if normalized == "ACTIVE":
        return Text("RUNNING", style="yellow")
    if normalized == "ERROR":
        return Text("ERROR", style="red")
    if normalized == "WAITING":
        return Text("WAITING", style="dim")
    return Text(normalized, style="cyan")


def _status_style(status: str) -> Text:
    normalized = status.upper()
    if normalized == "READY":
        return Text("READY", style="cyan")
    if normalized == "SUCCESS":
        return Text("SUCCESS", style="green")
    if normalized == "COMPILING":
        return Text("COMPILING", style="yellow")
    if normalized == "ERROR":
        return Text("ERROR", style="red")
    return Text(normalized, style="white")

