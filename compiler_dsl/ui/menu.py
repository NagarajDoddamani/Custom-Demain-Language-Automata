"""Menu helpers for the educational compiler simulator."""

from __future__ import annotations

from compiler_dsl.ui.colors import section


def show_menu() -> None:
    """Print the compact five-option demonstration menu."""

    print()
    print("1. Run Full Compilation")
    print("2. Step-by-Step Demonstration")
    print("3. Edit DSL Program")
    print("4. Show Saved Outputs")
    print("5. Exit")
    print()


def show_title() -> None:
    """Print the application title banner."""

    print("=" * 56)
    print(f"{'DSL COMPILER SIMULATOR':^56}")
    print("=" * 56)


def show_description() -> None:
    """Print a short description under the dashboard."""

    print(section("Educational Compiler Visualization"))
    print("Automatic compilation, live phase status, parse tree, symbol table, and TAC output.")

