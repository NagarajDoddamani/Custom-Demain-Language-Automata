"""Chatbot-style terminal application for JAN - Intelligent DSL Compiler Assistant."""

from __future__ import annotations

import sys

from compiler_dsl.core import CompilerSession, ExecutionError, LexerError, ParserError, SemanticError
from compiler_dsl.ui.animations import show_progress, spinner, step_pause, typing_dots
from compiler_dsl.ui.chatbot import (
    bot_error,
    bot_line,
    bot_say,
    bot_success,
    bot_warning,
    console,
    render_banner,
    render_error_panel,
    render_help_panel,
    render_menu_panel,
    render_saved_files_panel,
    render_source_panel,
    render_stage_panel,
    render_status_panel,
    render_summary_panel,
    render_welcome_card,
    welcome_name,
)
from compiler_dsl.ui.display import compiler_explanation
from compiler_dsl.ui.results import (
    RESULT_TABS,
    SAVED_TABS,
    build_current_view,
    build_saved_view,
    render_tab_bar,
)
from compiler_dsl.utils import SAMPLE_PROGRAMS_DIR, clear_screen, save_text_file


DEFAULT_SAMPLE = SAMPLE_PROGRAMS_DIR / "test.dsl"
EDITOR_SAMPLE = SAMPLE_PROGRAMS_DIR / "editor_input.dsl"


def wait_for_user(message: str = "Press Enter to continue...") -> None:
    """Pause when the terminal is interactive."""

    if not sys.stdin.isatty():
        return
    step_pause(message)


def load_default_program(session: CompilerSession) -> None:
    """Load the default sample program used by the assistant."""

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


def show_startup_screen() -> None:
    """Show the JAN startup banner and boot animation."""

    clear_screen()
    console.print(render_banner())
    bot_say("Initializing JAN...", tone="cyan")
    spinner("Booting assistant", duration=0.6)
    bot_say("Loading Compiler Modules...", tone="cyan")
    spinner("Loading core packages", duration=0.6)
    bot_say("Preparing Semantic Engine...", tone="cyan")
    spinner("Warming semantic analyzer", duration=0.6)
    bot_say("Starting TAC Generator...", tone="cyan")
    show_progress("Boot Sequence", values=(25, 50, 75, 100), delay=0.08)
    bot_success("JAN is ready.")



def show_home_screen(session: CompilerSession) -> None:
    """Render the chatbot home screen."""

    clear_screen()
    console.print(render_banner())
    console.print(render_welcome_card(welcome_name()))
    bot_say(f"Current program: {session.source_name}", tone="yellow")
    bot_say("I can compile your DSL program, explain each phase, and show the final output.", tone="white")
    console.print(render_status_panel(session))
    console.print(render_menu_panel())


def _run_lexical_stage(session: CompilerSession, step_mode: bool) -> None:
    console.print(render_stage_panel("Lexical Analysis", compiler_explanation("lexical")))
    bot_say("Lexical analysis converts source code into meaningful compiler tokens.", tone="white")
    typing_dots("Compiling", delay=0.16 if step_mode else 0.08)
    spinner("Processing tokens", duration=1.4 if step_mode else 0.8)
    tokens = session.run_lexical()
    bot_success("Tokens generated successfully.")
    bot_say(f"Total tokens found: {len(tokens) - 1}", tone="white")
    console.print(render_stage_panel("Token Preview", "JAN has identified the basic token stream for the parser."))
    console.print(build_current_view(session, "Tokens"))
    console.print(render_status_panel(session))


def _run_syntax_stage(session: CompilerSession, step_mode: bool) -> None:
    console.print(render_stage_panel("Syntax Analysis", compiler_explanation("syntax")))
    bot_say("Checking grammar rules and parse structure...", tone="white")
    typing_dots("Compiling", delay=0.16 if step_mode else 0.08)
    spinner("Parsing tokens", duration=1.4 if step_mode else 0.8)
    program = session.run_syntax()
    bot_success("Syntax validation completed successfully.")
    bot_say(f"Statements parsed: {len(program.statements)}", tone="white")
    console.print(render_status_panel(session))
    console.print(render_stage_panel("Parse Tree", "The parser has built a compact view of the program structure."))
    console.print(build_current_view(session, "Parse Tree"))


def _run_semantic_stage(session: CompilerSession, step_mode: bool) -> None:
    console.print(render_stage_panel("Semantic Analysis", compiler_explanation("semantic")))
    bot_say("Checking type safety and variable declarations.", tone="white")
    typing_dots("Compiling", delay=0.16 if step_mode else 0.08)
    spinner("Checking symbols", duration=1.4 if step_mode else 0.8)
    symbol_table = session.run_semantic()
    bot_success("No semantic issues detected.")
    bot_say(f"Variables declared: {len(symbol_table.items())}", tone="white")
    console.print(render_stage_panel("Symbol Table", "The semantic analyzer stores variable names, types, and values."))
    console.print(build_current_view(session, "Symbol Table"))
    console.print(render_status_panel(session))


def _run_tac_stage(session: CompilerSession, step_mode: bool) -> None:
    console.print(render_stage_panel("TAC Generation", compiler_explanation("tac")))
    bot_say("Generating machine-independent instructions...", tone="white")
    typing_dots("Compiling", delay=0.16 if step_mode else 0.08)
    spinner("Generating TAC", duration=1.4 if step_mode else 0.8)
    session.run_tac()
    bot_success("TAC generated successfully.")
    bot_say(f"Temporary variables created: {session.statistics()['temporary_vars']}", tone="white")
    console.print(render_stage_panel("TAC Preview", "The compiler converts expressions into three-address code."))
    console.print(build_current_view(session, "TAC"))
    console.print(render_status_panel(session))


def _run_execution_stage(session: CompilerSession, step_mode: bool) -> None:
    console.print(render_stage_panel("Program Output", compiler_explanation("execution")))
    bot_say("Simulating the DSL program output...", tone="white")
    typing_dots("Compiling", delay=0.16 if step_mode else 0.08)
    spinner("Running DSL program", duration=1.2 if step_mode else 0.7)
    outputs = session.run_execution()
    bot_success("Program output generated successfully.")
    bot_say(f"Output lines: {len(outputs)}", tone="white")
    console.print(render_stage_panel("Program Output", "This section shows what the DSL program prints at runtime."))
    console.print(build_current_view(session, "Output"))
    console.print(render_status_panel(session))


def _error_kind(exc: Exception) -> str:
    if isinstance(exc, LexerError):
        return "syntax"
    if isinstance(exc, ParserError):
        return "syntax"
    if isinstance(exc, SemanticError):
        return "semantic"
    if isinstance(exc, ExecutionError):
        return "runtime"
    return "runtime"


def _error_intro(kind: str) -> str:
    if kind == "syntax":
        return "I found a syntax issue in your code."
    if kind == "semantic":
        return "I found a semantic issue in your code."
    return "I found a runtime issue while simulating the program."


def run_compilation(session: CompilerSession, step_mode: bool = False) -> bool:
    """Run the full compiler assistant workflow."""

    if not session.has_source():
        bot_error("No DSL program is loaded.")
        return False

    session.load_source(session.source_code, session.source_name)
    clear_screen()
    console.print(render_banner())
    console.print(render_welcome_card(welcome_name()))
    bot_say(f"Compiling {session.source_name} now.", tone="yellow")
    console.print(render_source_panel(session.source_code, session.source_name))
    console.print(render_status_panel(session))

    try:
        _run_lexical_stage(session, step_mode)
        if step_mode:
            wait_for_user("Press Enter for Syntax Analysis...")

        _run_syntax_stage(session, step_mode)
        if step_mode:
            wait_for_user("Press Enter for Semantic Analysis...")

        _run_semantic_stage(session, step_mode)
        if step_mode:
            wait_for_user("Press Enter for TAC Generation...")

        _run_tac_stage(session, step_mode)
        if step_mode:
            wait_for_user("Press Enter for Program Output...")

        _run_execution_stage(session, step_mode)
        session.save_outputs()
        console.print(render_summary_panel(session, success=True))
        bot_success("Output generated successfully.")
        show_result_viewer(session)
        return True
    except (LexerError, ParserError, SemanticError, ExecutionError, RuntimeError) as exc:
        kind = _error_kind(exc)
        bot_error(_error_intro(kind))
        console.print(render_error_panel(kind, str(exc), session.source_code))
        session.save_outputs()
        console.print(render_summary_panel(session, success=False))
        bot_warning("Fix the highlighted issue and compile again.")
        return False
    finally:
        session.save_outputs()


def show_result_viewer(session: CompilerSession) -> None:
    """Show the interactive result tabs for the current compilation."""

    _show_tabbed_view(
        session=session,
        tabs=RESULT_TABS,
        title="Compilation Results",
        saved=False,
        include_summary=True,
    )


def show_saved_outputs() -> None:
    """Show the interactive viewer for saved compiler outputs."""

    _show_tabbed_view(
        session=None,
        tabs=SAVED_TABS,
        title="Saved Outputs",
        saved=True,
        include_summary=False,
    )


def show_help_screen() -> None:
    """Show the JAN help screen."""

    clear_screen()
    console.print(render_banner())
    bot_say("Here is how to use JAN.", tone="cyan")
    console.print(render_help_panel())
    wait_for_user()


def _show_tabbed_view(
    session: CompilerSession | None,
    tabs: list[str],
    title: str,
    saved: bool,
    include_summary: bool,
) -> None:
    """Render the tab viewer and let the user switch between results."""

    active_index = 0
    while True:
        clear_screen()
        console.print(render_banner())
        if include_summary and session is not None:
            console.print(render_summary_panel(session, success=True))
        if not include_summary and saved:
            console.print(render_saved_files_panel())

        bot_say(f"{title} - Select Result View:", tone="cyan")
        console.print(render_tab_bar(tabs[active_index], tabs))
        console.print()
        if saved:
            console.print(build_saved_view(tabs[active_index]))
        else:
            console.print(build_current_view(session, tabs[active_index]))
        console.print()
        for number, tab in enumerate(tabs, start=1):
            bot_say(f"[{number}] {tab}", tone="white")
        bot_say(f"[{len(tabs) + 1}] Back", tone="white")

        try:
            choice = console.input(f"[cyan]{bot_line('Choose a view:').plain}[/cyan] ").strip()
        except EOFError:
            return

        if choice == str(len(tabs) + 1):
            return
        if choice.isdigit() and 1 <= int(choice) <= len(tabs):
            active_index = int(choice) - 1
            continue
        bot_warning("Please choose a valid tab number.")
        wait_for_user()


def edit_dsl_program(session: CompilerSession) -> None:
    """Allow the user to type a DSL program directly in the terminal."""

    clear_screen()
    console.print(render_banner())
    console.print(render_welcome_card(welcome_name()))
    bot_say("Enter DSL Code (type END to finish)", tone="white")
    lines: list[str] = []
    while True:
        try:
            line = console.input("[cyan]>> [/cyan]")
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)

    source = "\n".join(lines).strip()
    if not source:
        bot_warning("No DSL code was entered.")
        wait_for_user()
        return

    save_text_file(EDITOR_SAMPLE, source + "\n")
    session.load_source(source, EDITOR_SAMPLE.name)
    bot_success(f"Program saved to {EDITOR_SAMPLE.name}")
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
        show_help_screen()
    elif choice == "6":
        bot_success("Exiting JAN assistant.")
        return False
    else:
        bot_warning("Please select a valid menu option.")
        wait_for_user()
    return True


def main() -> None:
    """Entry point for the compiler assistant."""

    session = CompilerSession()
    load_default_program(session)
    show_startup_screen()

    running = True
    while running:
        show_home_screen(session)
        try:
            choice = console.input(f"[cyan]{bot_line('Choose an option:').plain}[/cyan] ").strip()
        except EOFError:
            print()
            break
        running = handle_choice(session, choice)


if __name__ == "__main__":
    main()

