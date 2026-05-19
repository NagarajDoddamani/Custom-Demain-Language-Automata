"""Recursive descent parser for the custom DSL."""

from __future__ import annotations

from typing import List, Optional

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
from compiler_dsl.lexer.lexer import Token


class ParserError(Exception):
    """Raised when the source program violates the grammar."""


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.trace: List[str] = []

    def parse(self) -> Program:
        self.trace = ["[INFO] Starting syntax analysis trace"]
        statements: List[Statement] = []
        while not self._is_at_end():
            statements.append(self._parse_statement())
        self.trace.append("[SUCCESS] Syntax analysis completed")
        return Program(statements)

    def _parse_statement(self) -> Statement:
        token = self._peek()

        if token.type == "KEYWORD":
            if token.value in {"num", "dec", "text"}:
                return self._parse_declaration()
            if token.value == "show":
                return self._parse_print()
            if token.value == "when":
                return self._parse_if()
            if token.value == "loop":
                return self._parse_while()
            if token.value == "otherwise":
                self._error(token, "Unexpected 'otherwise' without a matching 'when'")

        if token.type == "SEPARATOR" and token.value == "{":
            return self._parse_block()

        if token.type == "IDENTIFIER":
            if self._check_next("SEPARATOR", "("):
                return self._parse_function_call()
            return self._parse_assignment()

        self._error(token, "Expected a valid statement")

    def _parse_block(self) -> Block:
        self._consume("SEPARATOR", "{", "Expected '{' to start a block")
        self.trace.append("Matched Rule: <block> -> { <statement_list> }")
        statements: List[Statement] = []
        while not self._check("SEPARATOR", "}") and not self._is_at_end():
            statements.append(self._parse_statement())
        self._consume("SEPARATOR", "}", "Expected '}' to close the block")
        return Block(statements)

    def _parse_declaration(self) -> Declaration:
        type_token = self._advance()
        name = self._consume("IDENTIFIER", None, "Expected identifier after the type keyword")
        initializer: Optional[Expression] = None

        if self._match("OPERATOR", "="):
            initializer = self._parse_expression()

        self._consume("SEPARATOR", ";", "Expected ';' after declaration")
        if initializer is None:
            self.trace.append(
                f"Matched Rule: <declaration> -> {type_token.value} identifier ;"
            )
        else:
            self.trace.append(
                f"Matched Rule: <declaration> -> {type_token.value} identifier = expression ;"
            )
        return Declaration(type_token.value, name.value, initializer, type_token.line, type_token.column)

    def _parse_assignment(self) -> Assignment:
        name = self._advance()
        self._consume("OPERATOR", "=", "Expected '=' in assignment")
        expression = self._parse_expression()
        self._consume("SEPARATOR", ";", "Expected ';' after assignment")
        self.trace.append("Matched Rule: <assignment> -> identifier = expression ;")
        return Assignment(name.value, expression, name.line, name.column)

    def _parse_print(self) -> PrintStatement:
        keyword = self._advance()
        self._consume("SEPARATOR", "(", "Expected '(' after 'show'")
        expression = self._parse_expression()
        self._consume("SEPARATOR", ")", "Expected ')' after print expression")
        self._consume("SEPARATOR", ";", "Expected ';' after print statement")
        self.trace.append("Matched Rule: <print_statement> -> show ( expression ) ;")
        return PrintStatement(expression, keyword.line, keyword.column)

    def _parse_function_call(self) -> FunctionCall:
        name = self._advance()
        self._consume("SEPARATOR", "(", "Expected '(' after function name")

        arguments: List[Expression] = []
        if not self._check("SEPARATOR", ")"):
            while True:
                arguments.append(self._parse_expression())
                if not self._match("SEPARATOR", ","):
                    break

        self._consume("SEPARATOR", ")", "Expected ')' after function arguments")
        self._consume("SEPARATOR", ";", "Expected ';' after function call")
        self.trace.append("Matched Rule: <function_call> -> identifier ( arguments ) ;")
        return FunctionCall(name.value, arguments, name.line, name.column)

    def _parse_if(self) -> IfStatement:
        keyword = self._advance()
        self._consume("SEPARATOR", "(", "Expected '(' after 'when'")
        condition = self._parse_expression()
        self._consume("SEPARATOR", ")", "Expected ')' after condition")
        then_branch = self._parse_block()
        else_branch: Optional[Block] = None

        if self._match("KEYWORD", "otherwise"):
            else_branch = self._parse_block()

        if else_branch is None:
            self.trace.append("Matched Rule: <if_statement> -> when ( expression ) <block>")
        else:
            self.trace.append(
                "Matched Rule: <if_statement> -> when ( expression ) <block> otherwise <block>"
            )
        return IfStatement(condition, then_branch, else_branch, keyword.line, keyword.column)

    def _parse_while(self) -> WhileStatement:
        keyword = self._advance()
        self._consume("SEPARATOR", "(", "Expected '(' after 'loop'")
        condition = self._parse_expression()
        self._consume("SEPARATOR", ")", "Expected ')' after loop condition")
        body = self._parse_block()
        self.trace.append("Matched Rule: <while_statement> -> loop ( expression ) <block>")
        return WhileStatement(condition, body, keyword.line, keyword.column)

    def _parse_expression(self) -> Expression:
        self.trace.append("Matched Rule: <expression> -> <equality>")
        return self._parse_equality()

    def _parse_equality(self) -> Expression:
        expression = self._parse_comparison()
        while self._match("OPERATOR", "==") or self._match("OPERATOR", "!="):
            operator = self._previous()
            right = self._parse_comparison()
            expression = BinaryOp(expression, operator.value, right, operator.line, operator.column)
            self.trace.append(
                f"Matched Rule: <equality> -> <comparison> {operator.value} <comparison>"
            )
        return expression

    def _parse_comparison(self) -> Expression:
        expression = self._parse_term()
        while self._match("OPERATOR", "<") or self._match("OPERATOR", ">") or self._match("OPERATOR", "<=") or self._match("OPERATOR", ">="):
            operator = self._previous()
            right = self._parse_term()
            expression = BinaryOp(expression, operator.value, right, operator.line, operator.column)
            self.trace.append(
                f"Matched Rule: <comparison> -> <term> {operator.value} <term>"
            )
        return expression

    def _parse_term(self) -> Expression:
        expression = self._parse_factor()
        while self._match("OPERATOR", "+") or self._match("OPERATOR", "-"):
            operator = self._previous()
            right = self._parse_factor()
            expression = BinaryOp(expression, operator.value, right, operator.line, operator.column)
            self.trace.append(f"Matched Rule: <term> -> <term> {operator.value} <factor>")
        return expression

    def _parse_factor(self) -> Expression:
        expression = self._parse_unary()
        while self._match("OPERATOR", "*") or self._match("OPERATOR", "/"):
            operator = self._previous()
            right = self._parse_unary()
            expression = BinaryOp(expression, operator.value, right, operator.line, operator.column)
            self.trace.append(f"Matched Rule: <factor> -> <factor> {operator.value} <unary>")
        return expression

    def _parse_unary(self) -> Expression:
        if self._match("OPERATOR", "-"):
            operator = self._previous()
            operand = self._parse_unary()
            self.trace.append("Matched Rule: <unary> -> - <unary>")
            return UnaryOp(operator.value, operand, operator.line, operator.column)
        self.trace.append("Matched Rule: <unary> -> <primary>")
        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        token = self._peek()

        if token.type == "NUMBER":
            self._advance()
            if "." in token.value:
                value = float(token.value)
                literal_type = "dec"
            else:
                value = int(token.value)
                literal_type = "num"
            self.trace.append("Matched Rule: <primary> -> <number>")
            return Literal(value, literal_type, token.line, token.column)

        if token.type == "STRING":
            self._advance()
            value = bytes(token.value[1:-1], "utf-8").decode("unicode_escape")
            self.trace.append("Matched Rule: <primary> -> <string>")
            return Literal(value, "text", token.line, token.column)

        if token.type == "IDENTIFIER":
            self._advance()
            self.trace.append("Matched Rule: <primary> -> <identifier>")
            return Variable(token.value, token.line, token.column)

        if self._match("SEPARATOR", "("):
            expression = self._parse_expression()
            self._consume("SEPARATOR", ")", "Expected ')' after expression")
            self.trace.append("Matched Rule: <primary> -> ( <expression> )")
            return expression

        self._error(token, "Expected an expression")

    def _match(self, token_type: str, value: Optional[str] = None) -> bool:
        if self._check(token_type, value):
            self._advance()
            return True
        return False

    def _consume(self, token_type: str, value: Optional[str], message: str) -> Token:
        if self._check(token_type, value):
            return self._advance()
        self._error(self._peek(), message)

    def _check(self, token_type: str, value: Optional[str] = None) -> bool:
        if self._is_at_end():
            return False
        token = self._peek()
        if token.type != token_type:
            return False
        if value is not None and token.value != value:
            return False
        return True

    def _check_next(self, token_type: str, value: Optional[str] = None) -> bool:
        index = self.current + 1
        if index >= len(self.tokens):
            return False
        token = self.tokens[index]
        if token.type != token_type:
            return False
        if value is not None and token.value != value:
            return False
        return True

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == "EOF"

    def _error(self, token: Token, message: str) -> None:
        raise ParserError(f"Syntax Error at line {token.line}, column {token.column}: {message}")
