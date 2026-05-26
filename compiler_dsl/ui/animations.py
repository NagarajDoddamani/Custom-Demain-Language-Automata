"""Simple terminal animations for JAN."""

from __future__ import annotations

import sys
import time
from typing import Iterable

from compiler_dsl.ui.colors import Fore, Style


JAN_PREFIX = "JAN >"


def typing_message(message: str, delay: float = 0.02, dots: int = 3) -> None:
    """Print a short animated message with dots."""

    if not sys.stdout.isatty():
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
        return
    sys.stdout.write(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
    sys.stdout.flush()
    for _ in range(dots):
        time.sleep(delay)
        sys.stdout.write(".")
        sys.stdout.flush()
    sys.stdout.write("\n")


def typing_dots(message: str = "Initializing JAN", delay: float = 0.18, dots: int = 3) -> None:
    """Print JAN-style loading dots."""

    if not sys.stdout.isatty():
        print(f"{JAN_PREFIX} {message}")
        return
    sys.stdout.write(f"{JAN_PREFIX} {message}")
    sys.stdout.flush()
    for _ in range(dots):
        time.sleep(delay)
        sys.stdout.write(".")
        sys.stdout.flush()
    sys.stdout.write("\n")


def spinner(message: str = "Processing Tokens", duration: float = 1.0, delay: float = 0.08) -> None:
    """Show a small spinner animation in the terminal."""

    frames = ["|", "/", "-", "\\"]
    if not sys.stdout.isatty():
        print(f"{JAN_PREFIX} {message}")
        time.sleep(min(duration, 0.2))
        return

    end_time = time.time() + duration
    frame_index = 0
    while time.time() < end_time:
        frame = frames[frame_index % len(frames)]
        sys.stdout.write(f"\r{JAN_PREFIX} [{Fore.CYAN}{frame}{Style.RESET_ALL}] {message}   ")
        sys.stdout.flush()
        time.sleep(delay)
        frame_index += 1
    sys.stdout.write("\n")


def loading_sequence(message: str, delay: float = 0.12, cycles: int = 1) -> None:
    """Animate a loading line by cycling through dots."""

    if not sys.stdout.isatty():
        print(f"{Fore.CYAN}{message}...{Style.RESET_ALL}")
        return
    for _ in range(cycles):
        for dots in ("", ".", "..", "..."):
            sys.stdout.write(f"\r{JAN_PREFIX} {message}{dots}{Style.RESET_ALL}   ")
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write("\n")


def progress_bar(percent: int, width: int = 20) -> str:
    """Return a textual progress bar for the given percentage."""

    percent = max(0, min(100, percent))
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent}%"


def show_progress(title: str, values: Iterable[int] = (25, 50, 75, 100), delay: float = 0.12) -> None:
    """Display a simple progress bar animation."""

    if not sys.stdout.isatty():
        final_value = list(values)[-1] if values else 100
        print(f"{Fore.YELLOW}{title}: {progress_bar(final_value)}{Style.RESET_ALL}")
        return
    for value in values:
        sys.stdout.write(f"\r{JAN_PREFIX} {title}: {progress_bar(value)}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def pause(seconds: float = 0.3) -> None:
    """Small pause used to make transitions feel deliberate."""

    time.sleep(seconds)


def step_pause(prompt_text: str = "Press Enter to continue...") -> None:
    """Pause for user input when running interactively."""

    if not sys.stdin.isatty():
        return
    try:
        input(f"{Fore.YELLOW}{prompt_text}{Style.RESET_ALL}")
    except EOFError:
        return
