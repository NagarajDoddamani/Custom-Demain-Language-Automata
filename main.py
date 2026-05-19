"""Interactive dashboard-driven console application for the DSL compiler."""

from __future__ import annotations

import sys

from compiler_dsl.core import CompilerSession, LexerError, ParserError, SemanticError
from compiler_dsl.ui.animations import step_pause
from compiler_dsl.ui.colors import Fore, Style, error, info, prompt, section, success, warning
from compiler_dsl.ui.dashboard import STAGES, render_dashboard, render_status_line
from compiler_dsl.ui.display import (
    compiler_explanation,
    render_compilation_summary,
    render_error,
    render_parse_tree,
    render_pipeline_diagram,
    render_source_code,
    render_symbol_table,
    render_tac,
    render_token_table,
)
from compiler_dsl.ui.menu import show_menu
from compiler_dsl.ui.progress import animate_progress, loading_dots
from compiler_dsl.utils import OUTPUT_DIR, SAMPLE_PROGRAMS_DIR, clear_screen, save_text_file


DEFAULT_SAMPLE = SAMPLE_PROGRAMS_DIR / "test.dsl"
EDITOR_SAMPLE = SAMPLE_PROGRAMS_DIR / "editor_input.dsl"


def wait_if_interactive(message: str = "Press Enter to continue...") -> None:
    """Pause only when the app is running in an interactive terminal."""

    if not sys.stdin.isatty():
        return
    step_pause(message)


def load_default_program(session: CompilerSession) -> None:
    """Load the default sample program that powers the demo dashboard."""

    if DEFAULT_SAMPLE.exists():
        source = DEFAULT_SAMPLE.read_text(encoding="utf-8")
        session.load_source(source, DEFAULT_SAMPLE.name)
        return

    fallback_source = "\n".join(
        [
            "num a = 10;",
            "num b = 20;",
            "num c;",
            "c = a + b;",
            "show(c);",
        ]
    )
    session.load_source(fallback_source, DEFAULT_SAMPLE.name)
    save_text_file(DEFAULT_SAMPLE, fallback_source + "\n")


def show_dashboard_screen(session: CompilerSession) -> None:
    """Render the main dashboard and menu layout."""

    clear_screen()
    print(render_dashboard(session))
    print()
    print(section("Compiler Pipeline"))
    print(render_pipeline_diagram())
    print()
    print(section("Live Status"))
    for stage_key, stage_name in STAGES:
        status = session.stage_statuses.get(stage_key, "WAITING")
        print(render_status_line(stage_name, status))
    print()
    show_menu()


def show_source_preview(session: CompilerSession) -> None:
    """Display the currently loaded DSL source code."""

    print(section("Source Code"))
    print(render_source_code(session.source_code))


def _run_lexical_stage(session: CompilerSession, step_mode: bool = False) -> None:
    print(section("Lexical Analysis"))
    print(compiler_explanation("lexical"))
    print()
    print(render_dashboard(session, active_stage="lexical"))
    print()
    loading_dots("Lexical Analysis in progress", delay=0.18 if step_mode else 0.08)
    animate_progress("Lexical Analysis", delay=0.18 if step_mode else 0.08)
    tokens = session.run_lexical()
    print(success("Tokens Generated Successfully"))
    print(info(f"Total Tokens Found: {len(tokens) - 1}"))
    print()
    print(section("Lexical Output"))
    print(render_token_table(tokens))
    print()
    print(section("Live Compiler Status"))
    print(render_dashboard(session))
    print()


def _run_syntax_stage(session: CompilerSession, step_mode: bool = False) -> None:
    print(section("Syntax Analysis"))
    print(compiler_explanation("syntax"))
    print()
    print(render_dashboard(session, active_stage="syntax"))
    print()
    loading_dots("Parsing source code", delay=0.18 if step_mode else 0.08)
    animate_progress("Syntax Analysis", delay=0.18 if step_mode else 0.08)
    program = session.run_syntax()
    print(success("Syntax Valid"))
    print(info(f"Statements Parsed: {len(program.statements)}"))
    print()
    print(section("Grammar Rules Matched"))
    for line in session.parser_trace:
        print(line)
    print()
    print(section("Parse Tree"))
    print(render_parse_tree(program))
    print()
    print(section("Live Compiler Status"))
    print(render_dashboard(session))
    print()


def _run_semantic_stage(session: CompilerSession, step_mode: bool = False) -> None:
    print(section("Semantic Analysis"))
    print(compiler_explanation("semantic"))
    print()
    print(render_dashboard(session, active_stage="semantic"))
    print()
    loading_dots("Checking symbols and types", delay=0.18 if step_mode else 0.08)
    animate_progress("Semantic Analysis", delay=0.18 if step_mode else 0.08)
    symbol_table = session.run_semantic()
    print(success("No Semantic Errors Found"))
    print(info(f"Variables Declared: {len(symbol_table.items())}"))
    print()
    print(section("Semantic Trace"))
    for line in session.semantic_trace:
        print(line)
    print()
    print(section("Symbol Table"))
    print(render_symbol_table(symbol_table))
    print()
    print(section("Live Compiler Status"))
    print(render_dashboard(session))
    print()


def _run_tac_stage(session: CompilerSession, step_mode: bool = False) -> None:
    print(section("Intermediate Code Generation"))
    print(compiler_explanation("tac"))
    print()
    print(render_dashboard(session, active_stage="tac"))
    print()
    loading_dots("Generating machine-independent code", delay=0.18 if step_mode else 0.08)
    animate_progress("TAC Generation", delay=0.18 if step_mode else 0.08)
    tac_lines = session.run_tac()
    print(success("TAC Generated Successfully"))
    print(info(f"Temporary Variables Created: {session.statistics()['temporary_vars']}"))
    print()
    print(section("TAC Trace"))
    for line in session.tac_trace:
        print(line)
    print()
    print(section("Three Address Code"))
    print(render_tac(tac_lines))
    print()
    print(Fore.GREEN + "=" * 56)
    print(f"{'COMPILATION SUCCESSFUL':^56}")
    print("=" * 56 + Style.RESET_ALL)
    print()
    print(section("Compilation Summary"))
    print(render_compilation_summary(session))
    print()
    print(section("Live Compiler Status"))
    print(render_dashboard(session))
    print()


def _format_compiler_error(exc: Exception, session: CompilerSession) -> str:
    """Convert internal exceptions into a friendly compiler error block."""

    if isinstance(exc, LexerError):
        return render_error("lexical", str(exc), session.source_code)
    if isinstance(exc, ParserError):
        return render_error("syntax", str(exc), session.source_code)
    if isinstance(exc, SemanticError):
        return render_error("semantic", str(exc), session.source_code)
    return render_error("tac", str(exc), session.source_code)


def run_compilation(session: CompilerSession, step_mode: bool = False) -> None:
    """Run the compiler automatically from start to finish."""

    if not session.has_source():
        print(error("No DSL program is loaded."))
        wait_if_interactive()
        return

    session.load_source(session.source_code, session.source_name)
    clear_screen()
    print(render_dashboard(session))
    print()
    print(section("Compiler Pipeline"))
    print(render_pipeline_diagram())
    print()
    show_source_preview(session)
    print()

    try:
        _run_lexical_stage(session, step_mode=step_mode)
        if step_mode:
            wait_if_interactive("Press Enter for Syntax Analysis...")

        _run_syntax_stage(session, step_mode=step_mode)
        if step_mode:
            wait_if_interactive("Press Enter for Semantic Analysis...")

        _run_semantic_stage(session, step_mode=step_mode)
        if step_mode:
            wait_if_interactive("Press Enter for TAC Generation...")

        _run_tac_stage(session, step_mode=step_mode)
    except (LexerError, ParserError, SemanticError, RuntimeError, ValueError) as exc:
        print(Fore.RED + _format_compiler_error(exc, session) + Style.RESET_ALL)
        print()
        print(section("Compilation Summary"))
        print(render_compilation_summary(session))
        print()
        print(info(f"Saved outputs are available in: {OUTPUT_DIR}"))
        print()
    finally:
        session.save_outputs()
        wait_if_interactive("Press Enter to return to the menu...")


def show_saved_outputs() -> None:
    """Display the text files written by the compiler session."""

    clear_screen()
    print(section("Saved Outputs"))
    print()
    files = [
        ("Tokens", OUTPUT_DIR / "tokens.txt"),
        ("Symbol Table", OUTPUT_DIR / "symbol_table.txt"),
        ("TAC", OUTPUT_DIR / "tac.txt"),
        ("Logs", OUTPUT_DIR / "logs.txt"),
    ]
    for label, path in files:
        print(section(label))
        if path.exists():
            print(path.read_text(encoding="utf-8"))
        else:
            print(warning("Output file not found yet. Run the compiler first."))
        print()
    wait_if_interactive("Press Enter to return to the menu...")


def edit_dsl_program(session: CompilerSession) -> None:
    """Allow the user to type a DSL program directly in the terminal."""

    clear_screen()
    print(section("DSL Editor Mode"))
    print("Enter DSL Code (type END on a new line to finish):")
    print()
    lines: list[str] = []
    while True:
        try:
            line = input(">> ")
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)

    source = "\n".join(lines).strip()
    if not source:
        print(error("No DSL code was entered."))
        wait_if_interactive()
        return

    save_text_file(EDITOR_SAMPLE, source + "\n")
    session.load_source(source, EDITOR_SAMPLE.name)
    run_compilation(session, step_mode=False)


def handle_choice(session: CompilerSession, choice: str) -> bool:
    """Dispatch a menu action. Returns False when the user wants to exit."""

    if choice == "1":
        run_compilation(session, step_mode=False)
    elif choice == "2":
        run_compilation(session, step_mode=True)
    elif choice == "3":
        edit_dsl_program(session)
    elif choice == "4":
        show_saved_outputs()
    elif choice == "5":
        print(success("Exiting compiler simulator..."))
        return False
    else:
        print(error("Invalid choice. Please select a valid menu option."))
        wait_if_interactive()
    return True


def main() -> None:
    """Entry point for the compiler simulator."""

    session = CompilerSession()
    load_default_program(session)

    running = True
    while running:
        show_dashboard_screen(session)
        try:
            choice = input(prompt("Enter Choice: ")).strip()
        except EOFError:
            print()
            break
        running = handle_choice(session, choice)


if __name__ == "__main__":
    main()
