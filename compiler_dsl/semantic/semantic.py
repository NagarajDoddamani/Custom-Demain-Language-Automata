"""Semantic analysis for the custom DSL."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from compiler_dsl.ast_nodes import (
    Assignment,
    BinaryOp,
    Block,
    Declaration,
    FunctionCall,
    Expression,
    IfStatement,
    Literal,
    PrintStatement,
    Program,
    Statement,
    UnaryOp,
    Variable,
    WhileStatement,
)


class SemanticError(Exception):
    """Raised when the program fails semantic checks."""


@dataclass
class SymbolInfo:
    name: str
    type_name: str
    value: Any
    line: int


class SymbolTable:
    def __init__(self) -> None:
        self._symbols: "OrderedDict[str, SymbolInfo]" = OrderedDict()

    def declare(self, name: str, type_name: str, value: Any, line: int) -> None:
        if name in self._symbols:
            existing = self._symbols[name]
            raise SemanticError(
                f"Semantic Error: Duplicate declaration of '{name}' at line {line}. "
                f"Previously declared at line {existing.line}."
            )
        self._symbols[name] = SymbolInfo(name, type_name, value, line)

    def lookup(self, name: str) -> SymbolInfo:
        if name not in self._symbols:
            raise SemanticError(f"Semantic Error: Undeclared variable '{name}'")
        return self._symbols[name]

    def update(self, name: str, value: Any) -> None:
        if name not in self._symbols:
            raise SemanticError(f"Semantic Error: Undeclared variable '{name}'")
        self._symbols[name].value = value

    def items(self):
        return self._symbols.items()

    def format_table(self) -> str:
        lines = [f"{'NAME':<18}{'TYPE':<14}{'VALUE':<20}"]
        for symbol in self._symbols.values():
            lines.append(
                f"{symbol.name:<18}{symbol.type_name:<14}{self._format_value(symbol.value):<20}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)


class SemanticAnalyzer:
    NUMERIC_TYPES = {"num", "dec"}
    RELATIONAL_OPERATORS = {"<", ">", "<=", ">=", "==", "!="}
    ARITHMETIC_OPERATORS = {"+", "-", "*", "/"}

    def __init__(self) -> None:
        self.symbol_table = SymbolTable()
        self.trace: list[str] = []

    def analyze(self, program: Program) -> SymbolTable:
        self.trace = ["[INFO] Performing semantic checks"]
        for statement in program.statements:
            self._analyze_statement(statement)
        self.trace.append("[SUCCESS] Semantic analysis completed")
        return self.symbol_table

    def _analyze_statement(self, statement: Statement) -> None:
        if isinstance(statement, Declaration):
            self._analyze_declaration(statement)
        elif isinstance(statement, Assignment):
            self._analyze_assignment(statement)
        elif isinstance(statement, PrintStatement):
            self._infer_expression(statement.expression)
        elif isinstance(statement, FunctionCall):
            raise SemanticError(
                f"Semantic Error: Function '{statement.name}' is not supported in this DSL at line {statement.line}"
            )
        elif isinstance(statement, IfStatement):
            self._analyze_if(statement)
        elif isinstance(statement, WhileStatement):
            self._analyze_while(statement)
        elif isinstance(statement, Block):
            self._analyze_block(statement)
        else:
            raise SemanticError("Semantic Error: Unsupported statement encountered")

    def _analyze_block(self, block: Block) -> None:
        self.trace.append("[INFO] Entering block scope")
        for statement in block.statements:
            self._analyze_statement(statement)
        self.trace.append("[INFO] Leaving block scope")

    def _analyze_declaration(self, declaration: Declaration) -> None:
        value = None
        if declaration.initializer is not None:
            self.trace.append(f"Checking declaration for '{declaration.name}'")
            expr_type, expr_value = self._infer_expression(declaration.initializer)
            self.trace.append(
                f"Checking type compatibility: {declaration.var_type} <- {expr_type}"
            )
            if not self._is_assignable(declaration.var_type, expr_type):
                raise SemanticError(
                    f"Semantic Error: Type mismatch between {declaration.var_type} and {expr_type} "
                    f"at line {declaration.line}"
                )
            value = self._coerce_value(declaration.var_type, expr_type, expr_value)
        else:
            self.trace.append(f"Declaring variable '{declaration.name}' as {declaration.var_type}")
        self.symbol_table.declare(declaration.name, declaration.var_type, value, declaration.line)
        self.trace.append(
            f"Inserted variable '{declaration.name}' into symbol table as {declaration.var_type}"
        )

    def _analyze_assignment(self, assignment: Assignment) -> None:
        symbol = self.symbol_table.lookup(assignment.name)
        self.trace.append(f"Checking assignment to '{assignment.name}'")
        expr_type, expr_value = self._infer_expression(assignment.expression)
        self.trace.append(
            f"Checking type compatibility: {symbol.type_name} <- {expr_type}"
        )
        if not self._is_assignable(symbol.type_name, expr_type):
            raise SemanticError(
                f"Semantic Error: Type mismatch between {symbol.type_name} and {expr_type} "
                f"at line {assignment.line}"
            )
        self.symbol_table.update(
            assignment.name,
            self._coerce_value(symbol.type_name, expr_type, expr_value),
        )
        self.trace.append(f"Updated symbol table entry for '{assignment.name}'")

    def _analyze_if(self, statement: IfStatement) -> None:
        self.trace.append("Evaluating 'when' condition")
        condition_type, _ = self._infer_expression(statement.condition)
        if condition_type != "bool":
            raise SemanticError(
                f"Semantic Error: 'when' condition must be relational/bool at line {statement.line}"
            )
        self._analyze_block(statement.then_branch)
        if statement.else_branch is not None:
            self._analyze_block(statement.else_branch)

    def _analyze_function_call(self, statement: FunctionCall) -> None:
        self.trace.append(f"Checking function call '{statement.name}'")
        for argument in statement.arguments:
            self._infer_expression(argument)
        self.trace.append(
            f"Function call '{statement.name}' accepted with {len(statement.arguments)} argument(s)"
        )

    def _analyze_while(self, statement: WhileStatement) -> None:
        self.trace.append("Evaluating 'loop' condition")
        condition_type, _ = self._infer_expression(statement.condition)
        if condition_type != "bool":
            raise SemanticError(
                f"Semantic Error: 'loop' condition must be relational/bool at line {statement.line}"
            )
        self._analyze_block(statement.body)

    def _infer_expression(self, expression: Expression) -> Tuple[str, Any]:
        if isinstance(expression, Literal):
            return expression.literal_type, expression.value

        if isinstance(expression, Variable):
            symbol = self.symbol_table.lookup(expression.name)
            self.trace.append(
                f"Resolved identifier '{expression.name}' with type {symbol.type_name}"
            )
            return symbol.type_name, symbol.value

        if isinstance(expression, UnaryOp):
            operand_type, operand_value = self._infer_expression(expression.operand)
            self.trace.append(f"Checking unary operator '{expression.operator}'")
            if operand_type not in self.NUMERIC_TYPES:
                raise SemanticError(
                    f"Semantic Error: Unary '{expression.operator}' requires a numeric operand "
                    f"at line {expression.line}"
                )
            if operand_value is None:
                return operand_type, None
            return operand_type, -operand_value

        if isinstance(expression, BinaryOp):
            left_type, left_value = self._infer_expression(expression.left)
            right_type, right_value = self._infer_expression(expression.right)
            self.trace.append(
                f"Checking expression types: {left_type} {expression.operator} {right_type}"
            )

            if expression.operator in self.ARITHMETIC_OPERATORS:
                return self._analyze_arithmetic(expression, left_type, right_type, left_value, right_value)
            if expression.operator in self.RELATIONAL_OPERATORS:
                return self._analyze_relational(expression, left_type, right_type, left_value, right_value)

            raise SemanticError(
                f"Semantic Error: Unsupported operator '{expression.operator}' at line {expression.line}"
            )

        raise SemanticError("Semantic Error: Invalid expression encountered")

    def _analyze_arithmetic(
        self,
        expression: BinaryOp,
        left_type: str,
        right_type: str,
        left_value: Any,
        right_value: Any,
    ) -> Tuple[str, Any]:
        if left_type not in self.NUMERIC_TYPES or right_type not in self.NUMERIC_TYPES:
            raise SemanticError(
                f"Semantic Error: Arithmetic operator '{expression.operator}' requires numeric operands "
                f"at line {expression.line}"
            )

        result_type = "dec" if expression.operator == "/" or "dec" in {left_type, right_type} else "num"
        self.trace.append(
            f"Arithmetic operation '{expression.operator}' is valid and yields {result_type}"
        )

        if left_value is None or right_value is None:
            return result_type, None

        if expression.operator == "+":
            return result_type, left_value + right_value
        if expression.operator == "-":
            return result_type, left_value - right_value
        if expression.operator == "*":
            return result_type, left_value * right_value
        if expression.operator == "/":
            if right_value == 0:
                raise SemanticError(f"Semantic Error: Division by zero at line {expression.line}")
            return result_type, left_value / right_value
        raise SemanticError("Semantic Error: Unknown arithmetic operator")

    def _analyze_relational(
        self,
        expression: BinaryOp,
        left_type: str,
        right_type: str,
        left_value: Any,
        right_value: Any,
    ) -> Tuple[str, Any]:
        if expression.operator in {"<", ">", "<=", ">="}:
            if left_type not in self.NUMERIC_TYPES or right_type not in self.NUMERIC_TYPES:
                raise SemanticError(
                    f"Semantic Error: Operator '{expression.operator}' requires numeric operands "
                    f"at line {expression.line}"
                )
        else:
            numeric_pair = left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES
            same_text_pair = left_type == right_type == "text"
            if not (numeric_pair or same_text_pair):
                raise SemanticError(
                    f"Semantic Error: Cannot compare {left_type} and {right_type} at line {expression.line}"
                )
        self.trace.append(f"Relational operation '{expression.operator}' type check passed")

        if left_value is None or right_value is None:
            return "bool", None

        if expression.operator == "<":
            return "bool", left_value < right_value
        if expression.operator == ">":
            return "bool", left_value > right_value
        if expression.operator == "<=":
            return "bool", left_value <= right_value
        if expression.operator == ">=":
            return "bool", left_value >= right_value
        if expression.operator == "==":
            return "bool", left_value == right_value
        if expression.operator == "!=":
            return "bool", left_value != right_value
        raise SemanticError("Semantic Error: Unknown relational operator")

    @staticmethod
    def _is_assignable(target_type: str, source_type: str) -> bool:
        if target_type == source_type:
            return True
        if target_type == "dec" and source_type == "num":
            return True
        return False

    @staticmethod
    def _coerce_value(target_type: str, source_type: str, value: Any) -> Any:
        if value is None:
            return None
        if target_type == source_type:
            return value
        if target_type == "dec" and source_type == "num":
            return float(value)
        return value
