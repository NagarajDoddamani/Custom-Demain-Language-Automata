"""Menu helpers for JAN."""

from __future__ import annotations

from compiler_dsl.ui.colors import section


def show_menu() -> None:
    """Print the JAN demonstration menu."""

    print()
    print("1. Run Full Compilation")
    print("2. Step-by-Step Demonstration")
    print("3. Open DSL Editor")
    print("4. View Compilation Outputs")
    print("5. Help")
    print("6. Exit")
    print()


def show_title() -> None:
    """Print the application title banner."""

    print("=" * 56)
    print(f"{'JAN':^56}")
    print(f"{'JAN - Intelligent DSL Compiler Assistant':^56}")
    print("=" * 56)


def show_description() -> None:
    """Print a short description under the dashboard."""

    print(section("Bot Style UI"))
    print("Automatic compilation, live phase status, parse tree, symbol table, TAC, output, and logs.")
