"""High-level formatting helpers for the compiler simulator UI."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, List, Optional, Sequence

from compiler_dsl.ast_nodes import (
    Assignment,
    BinaryOp,
    Block,
    Declaration,
    Expression,
    FunctionCall,
    IfStatement,
    Literal,
    PrintStatement,
    Program,
    Statement,
    UnaryOp,
    Variable,
    WhileStatement,
)
from compiler_dsl.ui.colors import warning
from compiler_dsl.ui.table import render_table


@dataclass
class TreeNode:
    """A tiny tree structure used to render a simple parse tree."""

    label: str
    children: List["TreeNode"] = field(default_factory=list)


def compiler_explanation(stage: str) -> str:
    """Return a short educational explanation for a compiler stage."""

    explanations = {
        "lexical": [
            "Lexical Analysis:",
            "The source code is broken into meaningful tokens.",
            "Each token is classified as a keyword, identifier, operator, constant, or separator.",
        ],
        "syntax": [
            "Syntax Analysis:",
            "The parser checks whether the token sequence follows grammar rules.",
            "If the structure is valid, the compiler builds an internal parse tree.",
        ],
        "semantic": [
            "Semantic Analysis:",
            "The compiler checks whether variables are declared and types are compatible.",
            "This phase prevents meaningful but incorrect code from passing through.",
        ],
        "tac": [
            "Intermediate Code Generation:",
            "The compiler converts the program into machine-independent Three-Address Code.",
            "Temporary variables are created for sub-expressions to keep the code simple.",
        ],
    }
    lines = explanations.get(stage, ["Compiler Stage:", "Processing the current compilation phase."])
    return "\n".join(lines)


def render_dashboard_text(
    project: str,
    language: str,
    input_file: str,
    status: str,
    stage_status_rows: Sequence[Sequence[Any]],
) -> str:
    """Render the top dashboard area as a bordered block."""

    header = [
        "=" * 56,
        f"{'DSL COMPILER SIMULATOR':^56}",
        "=" * 56,
        f"{'Project':<14}: {project}",
        f"{'Language':<14}: {language}",
        f"{'Input File':<14}: {input_file}",
        f"{'Status':<14}: {status}",
        "=" * 56,
    ]
    stage_table = render_table(stage_status_rows, headers=("Stage", "State"), tablefmt="grid")
    return "\n".join(header + [stage_table])


def render_stage_status_table(stage_status_rows: Sequence[Sequence[Any]]) -> str:
    """Render the active compiler phase board."""

    return render_table(stage_status_rows, headers=("Compiler Phase", "Status"), tablefmt="grid")


def render_source_code(source_code: str) -> str:
    """Render source code with line numbers."""

    lines = source_code.splitlines()
    if not lines:
        return warning("No DSL source loaded.")
    rows = [(index, line) for index, line in enumerate(lines, start=1)]
    return render_table(rows, headers=("LINE", "SOURCE"), tablefmt="grid")


def render_pipeline_diagram() -> str:
    """Render a compact compiler pipeline diagram."""

    return "\n".join(
        [
            "Source Code",
            "   |",
            "   v",
            "Lexical Analyzer",
            "   |",
            "   v",
            "Parser",
            "   |",
            "   v",
            "Semantic Analyzer",
            "   |",
            "   v",
            "Intermediate Code Generator",
            "   |",
            "   v",
            "Three Address Code",
        ]
    )


def render_token_table(tokens: Iterable[Any]) -> str:
    """Render lexical tokens in a pretty table."""

    rows = []
    for token in tokens:
        if getattr(token, "type", "") == "EOF":
            continue
        token_type = "CONSTANT" if token.type in {"NUMBER", "STRING"} else token.type
        rows.append((token.value, token_type, token.line, token.column))
    if not rows:
        return warning("No tokens available. Run lexical analysis first.")
    return render_table(rows, headers=("TOKEN", "TYPE", "LINE", "COLUMN"), tablefmt="grid")


def render_symbol_table(symbol_table: Any) -> str:
    """Render the symbol table in a simple table view."""

    if symbol_table is None:
        return warning("No symbol table available. Run semantic analysis first.")
    rows = []
    for _, entry in symbol_table.items():
        value = "-" if entry.value is None else entry.value
        rows.append((entry.name, entry.type_name, value))
    if not rows:
        return warning("Symbol table is empty.")
    return render_table(rows, headers=("Variable", "Type", "Value"), tablefmt="grid")


def render_tac(tac_lines: Sequence[str]) -> str:
    """Render Three-Address Code as a numbered table."""

    if not tac_lines:
        return warning("No TAC available. Run TAC generation first.")
    rows = [(index, instruction) for index, instruction in enumerate(tac_lines, start=1)]
    return render_table(rows, headers=("NO", "INSTRUCTION"), tablefmt="grid")


def render_parse_tree(program: Optional[Program]) -> str:
    """Render a simple parse tree for the current AST."""

    if program is None:
        return warning("No parse tree available. Run syntax analysis first.")
    root = TreeNode("program", [statement_to_tree(statement) for statement in program.statements])
    return _render_tree(root)


def render_compilation_summary(session: Any) -> str:
    """Render a compact summary of compilation results."""

    stats = session.statistics()
    rows = [
        ("Lexical Analysis", _summary_status(session.stage_statuses.get("lexical", "WAITING"))),
        ("Syntax Analysis", _summary_status(session.stage_statuses.get("syntax", "WAITING"))),
        ("Semantic Analysis", _summary_status(session.stage_statuses.get("semantic", "WAITING"))),
        ("TAC Generation", _summary_status(session.stage_statuses.get("tac", "WAITING"))),
        ("Tokens Generated", stats["total_tokens"]),
        ("Variables Declared", stats["variables_declared"]),
        ("Statements Parsed", stats["statements_parsed"]),
        ("Temporary Variables", stats["temporary_vars"]),
        ("Compilation Time", f"{stats['compilation_time']:.2f} sec"),
    ]
    return render_table(rows, headers=("Summary", "Value"), tablefmt="grid")


def render_error(kind: str, message: str, source_code: str = "") -> str:
    """Format compiler errors with a helpful suggested fix."""

    kind_upper = kind.upper()
    line_number = _extract_line_number(message)
    line_text = _extract_line_text(source_code, line_number)
    suggestion = _suggest_fix(kind_upper, message, line_text)

    lines = [f"[{kind_upper}]"]
    lines.append(message)
    if line_number is not None:
        lines.append(f"Line {line_number}: {line_text or 'Unavailable'}")
    if suggestion:
        lines.append("")
        lines.append("Suggested Fix:")
        lines.append(suggestion)
    return "\n".join(lines)


def statement_to_tree(statement: Statement) -> TreeNode:
    """Convert a statement node into a compact tree node."""

    if isinstance(statement, Declaration):
        label = f"declaration({statement.var_type} {statement.name})"
        children = [expression_to_tree(statement.initializer)] if statement.initializer else []
        return TreeNode(label, children)

    if isinstance(statement, Assignment):
        return TreeNode(
            "assignment",
            [
                TreeNode(f"identifier({statement.name})"),
                TreeNode("="),
                expression_to_tree(statement.expression),
            ],
        )

    if isinstance(statement, PrintStatement):
        return TreeNode("show", [expression_to_tree(statement.expression)])

    if isinstance(statement, FunctionCall):
        return TreeNode(
            f"call({statement.name})",
            [expression_to_tree(argument) for argument in statement.arguments],
        )

    if isinstance(statement, IfStatement):
        children = [
            TreeNode("condition", [expression_to_tree(statement.condition)]),
            TreeNode("then", [block_to_tree(statement.then_branch)]),
        ]
        if statement.else_branch is not None:
            children.append(TreeNode("otherwise", [block_to_tree(statement.else_branch)]))
        return TreeNode("when", children)

    if isinstance(statement, WhileStatement):
        return TreeNode(
            "loop",
            [
                TreeNode("condition", [expression_to_tree(statement.condition)]),
                TreeNode("body", [block_to_tree(statement.body)]),
            ],
        )

    if isinstance(statement, Block):
        return block_to_tree(statement)

    return TreeNode("statement")


def block_to_tree(block: Block) -> TreeNode:
    """Convert a block node to a tree node."""

    return TreeNode("block", [statement_to_tree(statement) for statement in block.statements])


def expression_to_tree(expression: Optional[Expression]) -> TreeNode:
    """Convert an expression node into a tree node."""

    if expression is None:
        return TreeNode("empty")

    if isinstance(expression, Literal):
        if expression.literal_type == "text":
            return TreeNode(f'string("{expression.value}")')
        return TreeNode(f"constant({expression.value})")

    if isinstance(expression, Variable):
        return TreeNode(f"identifier({expression.name})")

    if isinstance(expression, UnaryOp):
        return TreeNode(f"unary({expression.operator})", [expression_to_tree(expression.operand)])

    if isinstance(expression, BinaryOp):
        return TreeNode(
            "expression",
            [
                expression_to_tree(expression.left),
                TreeNode(expression.operator),
                expression_to_tree(expression.right),
            ],
        )

    return TreeNode("expression")


def _render_tree(node: TreeNode) -> str:
    """Render a tree node hierarchy with ASCII branch characters."""

    lines: List[str] = []

    def walk(current: TreeNode, prefix: str = "", is_last: bool = True, is_root: bool = False) -> None:
        if is_root:
            lines.append(current.label)
            total = len(current.children)
            for index, child in enumerate(current.children):
                walk(child, "", index == total - 1, False)
            return

        connector = "+-- " if is_last else "|-- "
        lines.append(f"{prefix}{connector}{current.label}")
        next_prefix = prefix + ("    " if is_last else "|   ")
        total = len(current.children)
        for index, child in enumerate(current.children):
            walk(child, next_prefix, index == total - 1, False)

    walk(node, is_root=True)
    return "\n".join(lines)


def _extract_line_number(message: str) -> Optional[int]:
    match = re.search(r"line\s+(\d+)", message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_line_text(source_code: str, line_number: Optional[int]) -> str:
    if line_number is None:
        return ""
    lines = source_code.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _suggest_fix(kind: str, message: str, line_text: str) -> str:
    lowered = message.lower()
    if "unexpected character" in lowered or "invalid token" in lowered:
        return "Remove unsupported symbols or check for a missing quote, operator, or separator."
    if "unterminated multi-line comment" in lowered:
        return "Close the comment with */ before continuing the program."
    if "expected ';'" in lowered or "missing ';'" in lowered:
        if line_text:
            return f"Add a semicolon at the end of the statement.\nExample: {line_text.rstrip(';')};"
        return "Add a semicolon at the end of the statement."
    if "undeclared variable" in lowered:
        return "Declare the variable before using it.\nExample: num x = 0;"
    if "type mismatch" in lowered:
        return "Make both sides the same type before assignment."
    if "duplicate declaration" in lowered:
        return "Use a different variable name or remove the duplicate declaration."
    if "condition must be relational" in lowered:
        return "Use a relational expression such as a < b or x == y."
    return "Review the highlighted line and correct the compiler message."


def _summary_status(status: str) -> str:
    """Convert live stage states into user-friendly summary labels."""

    normalized = status.upper()
    if normalized == "DONE":
        return "SUCCESS"
    if normalized == "ACTIVE":
        return "RUNNING"
    return normalized
