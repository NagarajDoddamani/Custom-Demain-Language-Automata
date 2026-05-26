"""High-level compiler session that stores the current program and stage outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Dict, List, Optional

from compiler_dsl.ast_nodes import Program
from compiler_dsl.core.executor import ExecutionError, ProgramExecutor
from compiler_dsl.core.lexer import Lexer, LexerError, Token
from compiler_dsl.core.parser import Parser, ParserError
from compiler_dsl.core.semantic import SemanticAnalyzer, SemanticError, SymbolTable
from compiler_dsl.core.tac import TACGenerator
from compiler_dsl.ui.display import render_parse_tree
from compiler_dsl.ui.table import render_table
from compiler_dsl.utils import (
    OUTPUT_DIR,
    count_program_statements,
    ensure_output_dir,
    save_text_file,
    timestamp,
)


def _default_stage_statuses() -> Dict[str, str]:
    """Return the initial compiler phase status map."""

    return {
        "lexical": "WAITING",
        "syntax": "WAITING",
        "semantic": "WAITING",
        "tac": "WAITING",
    }


@dataclass
class CompilerSession:
    """Stateful compilation session used by the interactive UI."""

    source_name: str = "Untitled"
    source_code: str = ""
    tokens: List[Token] = field(default_factory=list)
    program: Optional[Program] = None
    symbol_table: Optional[SymbolTable] = None
    tac_lines: List[str] = field(default_factory=list)
    program_output: List[str] = field(default_factory=list)
    lexer_trace: List[str] = field(default_factory=list)
    parser_trace: List[str] = field(default_factory=list)
    semantic_trace: List[str] = field(default_factory=list)
    tac_trace: List[str] = field(default_factory=list)
    execution_trace: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    phase_durations: Dict[str, float] = field(default_factory=dict)
    started_at: Optional[float] = None
    total_compilation_time: float = 0.0
    execution_time: float = 0.0
    last_error: Optional[str] = None
    stage_statuses: Dict[str, str] = field(default_factory=_default_stage_statuses)
    overall_status: str = "READY"
    active_stage: Optional[str] = None

    def load_source(self, source_code: str, source_name: str = "Untitled") -> None:
        """Load a fresh DSL source and reset all compilation artifacts."""

        self.source_name = source_name
        self.source_code = source_code
        self.tokens = []
        self.program = None
        self.symbol_table = None
        self.tac_lines = []
        self.program_output = []
        self.lexer_trace = []
        self.parser_trace = []
        self.semantic_trace = []
        self.tac_trace = []
        self.execution_trace = []
        self.phase_durations = {}
        self.last_error = None
        self.total_compilation_time = 0.0
        self.execution_time = 0.0
        self.started_at = None
        self.active_stage = None
        self.stage_statuses = _default_stage_statuses()
        self.overall_status = "READY"
        self.logs = []
        self._log("INFO", f"Loaded source: {source_name}")
        self.save_outputs()

    def has_source(self) -> bool:
        return bool(self.source_code.strip())

    def run_lexical(self) -> List[Token]:
        """Run lexical analysis and persist the token output."""

        self._require_source()
        if self.started_at is None:
            self.started_at = perf_counter()
        self._begin_stage("lexical", "Starting Lexical Analysis...")
        start = perf_counter()
        try:
            lexer = Lexer(self.source_code)
            self.tokens = lexer.tokenize()
            self.lexer_trace = [
                f"Matched Token: {token.value!r} -> {token.type}"
                for token in self.tokens
                if token.type != "EOF"
            ]
            self.phase_durations["lexical"] = perf_counter() - start
            self._log("SUCCESS", "Tokens Generated Successfully")
            self._log("INFO", f"Total Tokens Found: {len(self.tokens) - 1}")
            self._save_tokens(lexer.display_tokens(self.tokens))
            self._finish_stage("lexical")
            return self.tokens
        except LexerError as exc:
            self.phase_durations["lexical"] = perf_counter() - start
            self._fail_stage("lexical", str(exc))
            raise

    def run_syntax(self) -> Program:
        """Run syntax analysis and store the AST."""

        self._require_source()
        if not self.tokens:
            self.run_lexical()
        self._begin_stage("syntax", "Starting Syntax Analysis...")
        start = perf_counter()
        try:
            parser = Parser(self.tokens)
            self.program = parser.parse()
            self.parser_trace = list(parser.trace)
            self.phase_durations["syntax"] = perf_counter() - start
            self._log("SUCCESS", "Syntax Valid")
            self._log("INFO", f"Statements Parsed: {count_program_statements(self.program)}")
            self._finish_stage("syntax")
            return self.program
        except ParserError as exc:
            self.phase_durations["syntax"] = perf_counter() - start
            self._fail_stage("syntax", str(exc))
            raise

    def run_semantic(self) -> SymbolTable:
        """Run semantic analysis and update the symbol table."""

        self._require_source()
        if self.program is None:
            self.run_syntax()
        self._begin_stage("semantic", "Performing Semantic Analysis...")
        start = perf_counter()
        try:
            analyzer = SemanticAnalyzer()
            self.symbol_table = analyzer.analyze(self.program)
            self.semantic_trace = list(analyzer.trace)
            self.phase_durations["semantic"] = perf_counter() - start
            self._log("SUCCESS", "No Semantic Errors Found")
            self._log("INFO", f"Variables Declared: {len(self.symbol_table.items())}")
            self._save_symbol_table()
            self._finish_stage("semantic")
            return self.symbol_table
        except SemanticError as exc:
            self.phase_durations["semantic"] = perf_counter() - start
            self._fail_stage("semantic", str(exc))
            raise

    def run_tac(self) -> List[str]:
        """Generate three-address code from the AST."""

        self._require_source()
        if self.program is None:
            self.run_syntax()
        if self.symbol_table is None:
            self.run_semantic()
        self._begin_stage("tac", "Generating Three-Address Code...")
        start = perf_counter()
        try:
            generator = TACGenerator()
            self.tac_lines = generator.generate(self.program)
            self.tac_trace = list(generator.trace)
            self.phase_durations["tac"] = perf_counter() - start
            if self.started_at is not None:
                self.total_compilation_time = perf_counter() - self.started_at
            self._log("SUCCESS", "TAC Generated Successfully")
            self._log("INFO", f"Temporary Variables Created: {generator.temp_counter}")
            self._save_tac()
            self._finish_stage("tac", final=True)
            return self.tac_lines
        except Exception as exc:
            self.phase_durations["tac"] = perf_counter() - start
            self._fail_stage("tac", str(exc))
            raise

    def run_execution(self) -> List[str]:
        """Simulate the DSL program and collect program output."""

        self._require_source()
        if self.program is None:
            self.run_syntax()
        if self.symbol_table is None:
            self.run_semantic()
        if not self.tac_lines:
            self.run_tac()

        start = perf_counter()
        try:
            executor = ProgramExecutor()
            result = executor.execute(self.program)
            self.program_output = list(result.outputs)
            self.execution_trace = list(result.trace)
            self.execution_time = perf_counter() - start
            if self.started_at is not None:
                self.total_compilation_time = perf_counter() - self.started_at
            self._log("SUCCESS", "Program Output Generated Successfully")
            self._log("INFO", f"Program Output Lines: {len(self.program_output)}")
            self._save_output()
            self._save_logs()
            self.overall_status = "SUCCESS"
            return self.program_output
        except ExecutionError as exc:
            self.execution_time = perf_counter() - start
            self.last_error = str(exc)
            self.overall_status = "ERROR"
            self._log("ERROR", str(exc))
            self._save_logs()
            raise

    def show_tokens_text(self) -> str:
        """Return a token table for display or saving."""

        if not self.tokens:
            return "No tokens available. Run lexical analysis first."
        rows = [
            (
                token.value,
                "CONSTANT" if token.type in {"NUMBER", "STRING"} else token.type,
                token.line,
                token.column,
            )
            for token in self.tokens
            if token.type != "EOF"
        ]
        return render_table(rows, headers=("TOKEN", "TYPE", "LINE", "COLUMN"), tablefmt="grid")

    def show_symbol_table_text(self) -> str:
        """Return the semantic symbol table in formatted text."""

        if self.symbol_table is None:
            return "No symbol table available. Run semantic analysis first."
        return self.symbol_table.format_table()

    def show_parse_tree_text(self) -> str:
        """Return the current parse tree as formatted text."""

        if self.program is None:
            return "No parse tree available. Run syntax analysis first."
        return render_parse_tree(self.program)

    def show_tac_text(self) -> str:
        """Return the generated TAC as plain text."""

        if not self.tac_lines:
            return "No TAC available. Run TAC generation first."
        return "\n".join(self.tac_lines)

    def show_output_text(self) -> str:
        """Return the simulated program output as plain text."""

        if not self.program_output:
            return "No program output available. Run execution first."
        return "\n".join(self.program_output)

    def show_steps_text(self) -> str:
        """Combine the compilation logs and phase traces into one report."""

        sections = [
            self._format_section("Compilation Log", self.logs),
            self._format_section("Lexical Trace", self.lexer_trace),
            self._format_section("Parsing Trace", self.parser_trace),
            self._format_section("Semantic Trace", self.semantic_trace),
            self._format_section("TAC Trace", self.tac_trace),
            self._format_section("Execution Trace", self.execution_trace),
        ]
        return "\n\n".join(section for section in sections if section)

    def statistics(self) -> Dict[str, object]:
        """Return compilation statistics for the UI."""

        if self.total_compilation_time:
            compilation_time = self.total_compilation_time
        elif self.started_at is not None:
            compilation_time = perf_counter() - self.started_at
        else:
            compilation_time = 0.0

        return {
            "total_tokens": max(len(self.tokens) - 1, 0),
            "variables_declared": len(self.symbol_table.items()) if self.symbol_table else 0,
            "statements_parsed": count_program_statements(self.program) if self.program else 0,
            "temporary_vars": self._count_temporary_vars(),
            "program_output_lines": len(self.program_output),
            "compilation_time": compilation_time,
            "execution_time": self.execution_time,
        }

    def save_outputs(self) -> None:
        """Persist all available outputs to the outputs directory."""

        ensure_output_dir()
        self._save_tokens()
        self._save_parse_tree()
        self._save_symbol_table()
        self._save_tac()
        self._save_output()
        self._save_logs()

    def _save_tokens(self, token_table: Optional[str] = None) -> None:
        if token_table is None:
            token_table = self.show_tokens_text()
        save_text_file(OUTPUT_DIR / "tokens.txt", token_table)

    def _save_parse_tree(self) -> None:
        save_text_file(OUTPUT_DIR / "parse_tree.txt", self.show_parse_tree_text())

    def _save_symbol_table(self) -> None:
        save_text_file(OUTPUT_DIR / "symbol_table.txt", self.show_symbol_table_text())

    def _save_tac(self) -> None:
        save_text_file(OUTPUT_DIR / "tac.txt", self.show_tac_text())

    def _save_output(self) -> None:
        save_text_file(OUTPUT_DIR / "output.txt", self.show_output_text())

    def _save_logs(self) -> None:
        save_text_file(OUTPUT_DIR / "logs.txt", "\n".join(self.logs))

    def _log(self, level: str, message: str) -> None:
        self.logs.append(f"{timestamp()} [{level}] {message}")

    def log_event(self, level: str, message: str) -> None:
        """Public wrapper for recording a log entry from the UI layer."""

        if level.upper() == "ERROR":
            self.last_error = message
            self.overall_status = "ERROR"
        self._log(level.upper(), message)
        self._save_logs()

    def set_stage_status(self, stage: str, status: str) -> None:
        """Update the live status of a compiler stage for the dashboard."""

        self.stage_statuses[stage] = status
        if status == "ACTIVE":
            self.active_stage = stage
            self.overall_status = "COMPILING"
        elif status == "DONE":
            self.active_stage = None
            if all(current == "DONE" for current in self.stage_statuses.values()):
                self.overall_status = "SUCCESS"
            else:
                self.overall_status = "COMPILING"
        elif status == "ERROR":
            self.active_stage = stage
            self.overall_status = "ERROR"
        elif status == "WAITING" and self.active_stage == stage:
            self.active_stage = None

    def _begin_stage(self, stage: str, message: str) -> None:
        self.set_stage_status(stage, "ACTIVE")
        self._log("INFO", message)
        self._save_logs()

    def _finish_stage(self, stage: str, final: bool = False) -> None:
        self.set_stage_status(stage, "DONE")
        if final and self.started_at is not None:
            self.total_compilation_time = perf_counter() - self.started_at
        self._save_logs()

    def _fail_stage(self, stage: str, message: str) -> None:
        self.set_stage_status(stage, "ERROR")
        self.last_error = message
        self._log("ERROR", message)
        self._save_logs()

    def _require_source(self) -> None:
        if not self.has_source():
            raise RuntimeError("No DSL program loaded. Please load or edit a program first.")

    def _count_temporary_vars(self) -> int:
        return sum(1 for line in self.tac_lines if line.startswith("t") and "=" in line)

    @staticmethod
    def _format_section(title: str, lines: List[str]) -> str:
        if not lines:
            return ""
        output = [f"{title}:"]
        output.extend(f"  {line}" for line in lines)
        return "\n".join(output)
