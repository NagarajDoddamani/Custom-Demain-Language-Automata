"""Progress bar helpers for the compiler simulator."""

from __future__ import annotations

import sys
import time
from typing import Sequence

from compiler_dsl.ui.colors import Fore, Style


def progress_bar(percent: int, width: int = 18) -> str:
    """Return a text progress bar for the given percentage."""

    percent = max(0, min(100, percent))
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{('#' * filled)}{('-' * empty)}] {percent}%"


def animate_progress(
    title: str,
    milestones: Sequence[int] = (30, 60, 100),
    delay: float = 0.15,
) -> None:
    """Animate a compiler phase progress bar."""

    if not sys.stdout.isatty():
        final_value = milestones[-1] if milestones else 100
        print(f"{Fore.CYAN}{title}: {progress_bar(final_value)}{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}{title}...{Style.RESET_ALL}")
    for milestone in milestones:
        sys.stdout.write(f"\r{Fore.CYAN}{progress_bar(milestone)}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def loading_dots(message: str, dots: int = 3, delay: float = 0.12) -> None:
    """Show a small animated message with dots."""

    if not sys.stdout.isatty():
        print(f"{Fore.CYAN}{message}...{Style.RESET_ALL}")
        return

    sys.stdout.write(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
    sys.stdout.flush()
    for _ in range(dots):
        time.sleep(delay)
        sys.stdout.write(".")
        sys.stdout.flush()
    sys.stdout.write("\n")
