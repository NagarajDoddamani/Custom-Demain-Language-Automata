"""Shared AST node definitions for the custom DSL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


@dataclass
class Program:
    statements: List["Statement"] = field(default_factory=list)


@dataclass
class Block:
    statements: List["Statement"] = field(default_factory=list)


@dataclass
class Declaration:
    var_type: str
    name: str
    initializer: Optional["Expression"]
    line: int
    column: int


@dataclass
class Assignment:
    name: str
    expression: "Expression"
    line: int
    column: int


@dataclass
class PrintStatement:
    expression: "Expression"
    line: int
    column: int


@dataclass
class FunctionCall:
    name: str
    arguments: List["Expression"]
    line: int
    column: int


@dataclass
class IfStatement:
    condition: "Expression"
    then_branch: Block
    else_branch: Optional[Block]
    line: int
    column: int


@dataclass
class WhileStatement:
    condition: "Expression"
    body: Block
    line: int
    column: int


@dataclass
class BinaryOp:
    left: "Expression"
    operator: str
    right: "Expression"
    line: int
    column: int


@dataclass
class UnaryOp:
    operator: str
    operand: "Expression"
    line: int
    column: int


@dataclass
class Literal:
    value: Any
    literal_type: str
    line: int
    column: int


@dataclass
class Variable:
    name: str
    line: int
    column: int


Statement = Union[
    Declaration,
    Assignment,
    PrintStatement,
    FunctionCall,
    IfStatement,
    WhileStatement,
    Block,
]
Expression = Union[BinaryOp, UnaryOp, Literal, Variable]
