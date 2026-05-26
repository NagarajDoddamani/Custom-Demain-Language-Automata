"""Three-address code generator for the custom DSL."""

from __future__ import annotations

from typing import List

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


class TACGenerator:
    def __init__(self) -> None:
        self.instructions: List[str] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.trace: List[str] = []

    def generate(self, program: Program) -> List[str]:
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.trace = ["[INFO] Generating TAC"]
        for statement in program.statements:
            self._emit_statement(statement)
        self.trace.append("[SUCCESS] TAC generation completed")
        return self.instructions

    def display(self) -> str:
        return "\n".join(self.instructions)

    def _emit_statement(self, statement: Statement) -> None:
        if isinstance(statement, Declaration):
            self._emit_declaration(statement)
        elif isinstance(statement, Assignment):
            value = self._emit_expression(statement.expression)
            self._emit(f"{statement.name} = {value}")
        elif isinstance(statement, PrintStatement):
            value = self._emit_expression(statement.expression)
            self._emit(f"print {value}")
        elif isinstance(statement, FunctionCall):
            raise RuntimeError(
                f"Unsupported function call '{statement.name}' at line {statement.line}"
            )
        elif isinstance(statement, IfStatement):
            self._emit_if(statement)
        elif isinstance(statement, WhileStatement):
            self._emit_while(statement)
        elif isinstance(statement, Block):
            self._emit_block(statement)

    def _emit_block(self, block: Block) -> None:
        for statement in block.statements:
            self._emit_statement(statement)

    def _emit_declaration(self, declaration: Declaration) -> None:
        if declaration.initializer is None:
            instruction = f"# declare {declaration.var_type} {declaration.name}"
            self._emit(instruction)
            return
        value = self._emit_expression(declaration.initializer)
        instruction = f"{declaration.name} = {value}"
        self._emit(instruction)

    def _emit_function_call(self, statement: FunctionCall) -> None:
        for argument in statement.arguments:
            value = self._emit_expression(argument)
            self._emit(f"param {value}")
        self._emit(f"call {statement.name}, {len(statement.arguments)}")

    def _emit_if(self, statement: IfStatement) -> None:
        condition_value = self._emit_expression(statement.condition)
        else_label = self._new_label()
        end_label = self._new_label()

        if statement.else_branch is not None:
            self._emit(f"ifFalse {condition_value} goto {else_label}")
            self._emit_block(statement.then_branch)
            self._emit(f"goto {end_label}")
            self._emit(f"{else_label}:")
            self._emit_block(statement.else_branch)
            self._emit(f"{end_label}:")
        else:
            self._emit(f"ifFalse {condition_value} goto {end_label}")
            self._emit_block(statement.then_branch)
            self._emit(f"{end_label}:")

    def _emit_while(self, statement: WhileStatement) -> None:
        start_label = self._new_label()
        end_label = self._new_label()
        self._emit(f"{start_label}:")
        condition_value = self._emit_expression(statement.condition)
        self._emit(f"ifFalse {condition_value} goto {end_label}")
        self._emit_block(statement.body)
        self._emit(f"goto {start_label}")
        self._emit(f"{end_label}:")

    def _emit_expression(self, expression: Expression) -> str:
        if isinstance(expression, Literal):
            return self._format_literal(expression)
        if isinstance(expression, Variable):
            return expression.name
        if isinstance(expression, UnaryOp):
            operand = self._emit_expression(expression.operand)
            temp = self._new_temp()
            instruction = f"{temp} = {expression.operator}{operand}"
            self.trace.append(f"Creating temporary variable {temp}")
            self._emit(instruction)
            return temp
        if isinstance(expression, BinaryOp):
            left = self._emit_expression(expression.left)
            right = self._emit_expression(expression.right)
            temp = self._new_temp()
            instruction = f"{temp} = {left} {expression.operator} {right}"
            self.trace.append(f"Creating temporary variable {temp}")
            self._emit(instruction)
            return temp
        return "0"

    def _emit(self, instruction: str) -> None:
        self.trace.append(f"Generating: {instruction}")
        self.instructions.append(instruction)

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self) -> str:
        self.label_counter += 1
        label = f"L{self.label_counter}"
        self.trace.append(f"Creating label {label}")
        return label

    @staticmethod
    def _format_literal(expression: Literal) -> str:
        if expression.literal_type == "text":
            escaped = expression.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return str(expression.value)
