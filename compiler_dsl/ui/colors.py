"""Colored console output helpers built on top of colorama."""

from __future__ import annotations

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except Exception:  # pragma: no cover - fallback for environments without colorama
    class _Fallback:
        BLACK = ""
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        BRIGHT = ""
        RESET = ""
        RESET_ALL = ""

    Fore = _Fallback()  # type: ignore[assignment]
    Style = _Fallback()  # type: ignore[assignment]


def banner(text: str) -> str:
    return f"{Style.BRIGHT}{Fore.CYAN}{text}{Style.RESET_ALL}"


def info(text: str) -> str:
    return f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {text}"


def success(text: str) -> str:
    return f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {text}"


def warning(text: str) -> str:
    return f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {text}"


def error(text: str) -> str:
    return f"{Fore.RED}[ERROR]{Style.RESET_ALL} {text}"


def section(text: str) -> str:
    return f"{Style.BRIGHT}{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def prompt(text: str) -> str:
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def muted(text: str) -> str:
    return f"{Fore.WHITE}{text}{Style.RESET_ALL}"
