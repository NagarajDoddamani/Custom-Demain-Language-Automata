"""Runtime executor that simulates DSL program output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

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


class ExecutionError(Exception):
    """Raised when the runtime simulation cannot continue."""


@dataclass
class ExecutionResult:
    """Container for the runtime output and execution trace."""

    outputs: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)


class ProgramExecutor:
    """Evaluate a DSL program and collect the printed output."""

    def __init__(self, max_iterations: int = 1000) -> None:
        self.max_iterations = max_iterations
        self.environment: Dict[str, Any] = {}
        self.variable_types: Dict[str, str] = {}
        self.outputs: List[str] = []
        self.trace: List[str] = []

    def execute(self, program: Program) -> ExecutionResult:
        """Run the program statement by statement."""

        self.environment = {}
        self.variable_types = {}
        self.outputs = []
        self.trace = ["[INFO] Starting program output simulation"]
        for statement in program.statements:
            self._execute_statement(statement)
        self.trace.append("[SUCCESS] Program output generated successfully")
        return ExecutionResult(
            outputs=list(self.outputs),
            trace=list(self.trace),
            variables=dict(self.environment),
        )

    def _execute_statement(self, statement: Statement) -> None:
        if isinstance(statement, Declaration):
            self._execute_declaration(statement)
        elif isinstance(statement, Assignment):
            self._execute_assignment(statement)
        elif isinstance(statement, PrintStatement):
            value = self._evaluate_expression(statement.expression)
            rendered = self._stringify(value)
            self.outputs.append(rendered)
            self.trace.append(f"show -> {rendered}")
        elif isinstance(statement, IfStatement):
            self._execute_if(statement)
        elif isinstance(statement, WhileStatement):
            self._execute_while(statement)
        elif isinstance(statement, Block):
            self._execute_block(statement)
        elif isinstance(statement, FunctionCall):
            raise ExecutionError(
                f"Semantic Error: Function '{statement.name}' is not supported in this DSL at line {statement.line}"
            )
        else:
            raise ExecutionError("Runtime Error: Unsupported statement encountered")

    def _execute_block(self, block: Block) -> None:
        for statement in block.statements:
            self._execute_statement(statement)

    def _execute_declaration(self, declaration: Declaration) -> None:
        self.variable_types[declaration.name] = declaration.var_type
        if declaration.initializer is None:
            self.environment[declaration.name] = None
            self.trace.append(
                f"Declared {declaration.var_type} {declaration.name}"
            )
            return

        value = self._evaluate_expression(declaration.initializer)
        coerced = self._coerce_value(declaration.var_type, value)
        self.environment[declaration.name] = coerced
        self.trace.append(
            f"Declared {declaration.var_type} {declaration.name} = {self._stringify(coerced)}"
        )

    def _execute_assignment(self, assignment: Assignment) -> None:
        if assignment.name not in self.environment:
            raise ExecutionError(
                f"Runtime Error: Variable '{assignment.name}' not declared before assignment at line {assignment.line}"
            )
        value = self._evaluate_expression(assignment.expression)
        target_type = self.variable_types.get(assignment.name, "")
        coerced = self._coerce_value(target_type, value)
        self.environment[assignment.name] = coerced
        self.trace.append(
            f"Assigned {assignment.name} = {self._stringify(coerced)}"
        )

    def _execute_if(self, statement: IfStatement) -> None:
        condition = self._evaluate_expression(statement.condition)
        self.trace.append(f"Evaluated when condition -> {self._stringify(condition)}")
        if self._is_truthy(condition):
            self.trace.append("Entering then branch")
            self._execute_block(statement.then_branch)
        elif statement.else_branch is not None:
            self.trace.append("Entering otherwise branch")
            self._execute_block(statement.else_branch)

    def _execute_while(self, statement: WhileStatement) -> None:
        iterations = 0
        while self._is_truthy(self._evaluate_expression(statement.condition)):
            iterations += 1
            if iterations > self.max_iterations:
                raise ExecutionError("Runtime Error: Loop iteration limit exceeded")
            self.trace.append(f"loop iteration {iterations}")
            self._execute_block(statement.body)

    def _evaluate_expression(self, expression: Expression) -> Any:
        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, Variable):
            if expression.name not in self.environment:
                raise ExecutionError(
                    f"Runtime Error: Variable '{expression.name}' used before declaration at line {expression.line}"
                )
            value = self.environment[expression.name]
            if value is None:
                raise ExecutionError(
                    f"Runtime Error: Variable '{expression.name}' used before initialization at line {expression.line}"
                )
            return value

        if isinstance(expression, UnaryOp):
            operand = self._evaluate_expression(expression.operand)
            if expression.operator == "-":
                if not self._is_numeric(operand):
                    raise ExecutionError(
                        f"Runtime Error: Unary '-' requires a numeric operand at line {expression.line}"
                    )
                return -operand
            raise ExecutionError(
                f"Runtime Error: Unsupported unary operator '{expression.operator}' at line {expression.line}"
            )

        if isinstance(expression, BinaryOp):
            left = self._evaluate_expression(expression.left)
            right = self._evaluate_expression(expression.right)
            return self._evaluate_binary(expression.operator, left, right, expression.line)

        raise ExecutionError("Runtime Error: Invalid expression encountered")

    def _evaluate_binary(self, operator: str, left: Any, right: Any, line: int) -> Any:
        if operator in {"+", "-", "*", "/"}:
            if not self._is_numeric(left) or not self._is_numeric(right):
                raise ExecutionError(
                    f"Runtime Error: Arithmetic operator '{operator}' requires numeric operands at line {line}"
                )
            if operator == "+":
                return left + right
            if operator == "-":
                return left - right
            if operator == "*":
                return left * right
            if operator == "/":
                if right == 0:
                    raise ExecutionError(f"Runtime Error: Division by zero at line {line}")
                return left / right

        if operator in {"<", ">", "<=", ">=", "==", "!="}:
            if operator in {"<", ">", "<=", ">="} and (
                not self._is_numeric(left) or not self._is_numeric(right)
            ):
                raise ExecutionError(
                    f"Runtime Error: Relational operator '{operator}' requires numeric operands at line {line}"
                )
            if operator == "<":
                return left < right
            if operator == ">":
                return left > right
            if operator == "<=":
                return left <= right
            if operator == ">=":
                return left >= right
            if operator == "==":
                return left == right
            if operator == "!=":
                return left != right

        raise ExecutionError(
            f"Runtime Error: Unsupported operator '{operator}' at line {line}"
        )

    @staticmethod
    def _coerce_value(type_name: str, value: Any) -> Any:
        if value is None:
            return None
        if type_name == "dec":
            return float(value)
        if type_name == "num" and isinstance(value, float) and value.is_integer():
            return int(value)
        if type_name == "text":
            return str(value)
        return value

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, str):
            return len(value) > 0
        return bool(value)

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)