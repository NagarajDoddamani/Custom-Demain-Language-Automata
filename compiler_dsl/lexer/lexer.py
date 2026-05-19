"""Lexical analyzer for the custom DSL."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int
    literal_type: Optional[str] = None


class LexerError(Exception):
    """Raised when the source contains an invalid token."""


class Lexer:
    KEYWORDS = {"num", "dec", "text", "show", "when", "otherwise", "loop"}
    OPERATORS = ["<=", ">=", "==", "!=", "+", "-", "*", "/", "=", "<", ">"]
    SEPARATORS = {";", "(", ")", "{", "}", ","}

    _identifier_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    _number_re = re.compile(r"\d+(?:\.\d+)?")
    _string_re = re.compile(r'"(?:\\.|[^"\\])*"')

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break

            start_line = self.line
            start_column = self.column
            current = self._current_char()

            if current.isalpha() or current == "_":
                lexeme = self._match_pattern(self._identifier_re)
                token_type = "KEYWORD" if lexeme in self.KEYWORDS else "IDENTIFIER"
                tokens.append(Token(token_type, lexeme, start_line, start_column))
                continue

            if current.isdigit():
                lexeme = self._match_pattern(self._number_re)
                literal_type = "dec" if "." in lexeme else "num"
                tokens.append(Token("NUMBER", lexeme, start_line, start_column, literal_type))
                continue

            if current == '"':
                lexeme = self._match_pattern(self._string_re)
                tokens.append(Token("STRING", lexeme, start_line, start_column, "text"))
                continue

            operator = self._match_operator()
            if operator is not None:
                tokens.append(Token("OPERATOR", operator, start_line, start_column))
                continue

            if current in self.SEPARATORS:
                self._advance()
                tokens.append(Token("SEPARATOR", current, start_line, start_column))
                continue

            raise LexerError(
                f"Unexpected character {current!r} at line {start_line}, column {start_column}"
            )

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens

    def display_tokens(self, tokens: Iterable[Token]) -> str:
        """Return a token table suitable for console display."""

        lines = [f"{'TOKEN':<18}{'TYPE':<14}{'LINE':<8}{'COLUMN':<8}"]
        for token in tokens:
            if token.type == "EOF":
                continue
            display_type = "CONSTANT" if token.type in {"NUMBER", "STRING"} else token.type
            lines.append(
                f"{token.value:<18}{display_type:<14}{token.line:<8}{token.column:<8}"
            )
        return "\n".join(lines)

    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            current = self._current_char()
            if current.isspace():
                self._advance()
                continue

            if self.source.startswith("//", self.position):
                while not self._at_end() and self._current_char() != "\n":
                    self._advance()
                continue

            if self.source.startswith("/*", self.position):
                end_index = self.source.find("*/", self.position + 2)
                if end_index == -1:
                    raise LexerError(
                        f"Unterminated multi-line comment at line {self.line}, column {self.column}"
                    )
                self._advance_text(self.source[self.position : end_index + 2])
                continue

            break

    def _match_pattern(self, pattern: re.Pattern[str]) -> str:
        match = pattern.match(self.source, self.position)
        if not match:
            raise LexerError(
                f"Invalid token at line {self.line}, column {self.column}"
            )
        lexeme = match.group(0)
        self._advance_text(lexeme)
        return lexeme

    def _match_operator(self) -> Optional[str]:
        for operator in self.OPERATORS:
            if self.source.startswith(operator, self.position):
                self._advance_text(operator)
                return operator
        return None

    def _advance(self) -> None:
        self._advance_text(self.source[self.position])

    def _advance_text(self, text: str) -> None:
        for char in text:
            self.position += 1
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1

    def _current_char(self) -> str:
        return self.source[self.position]

    def _at_end(self) -> bool:
        return self.position >= self.length

