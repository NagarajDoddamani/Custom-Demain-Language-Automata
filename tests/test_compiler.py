"""Unit tests for the custom DSL compiler project."""

from __future__ import annotations

import textwrap
import unittest

from compiler_dsl.intermediate.tac_generator import TACGenerator
from compiler_dsl.lab_tasks import (
    check_c_statements,
    count_vowels_consonants,
    evaluate_expression,
    recognize_token,
    remove_comments,
    validate_expression,
)
from compiler_dsl.lexer.lexer import Lexer
from compiler_dsl.parser.parser import Parser, ParserError
from compiler_dsl.semantic.semantic import SemanticAnalyzer, SemanticError


VALID_SOURCE = textwrap.dedent(
    """
    num a = 10;
    num b = 20;
    num c;
    c = a + b * 2;
    show(c);
    """
).strip()


CONTROL_FLOW_SOURCE = textwrap.dedent(
    """
    num a = 10;
    num b = 20;
    when (a < b) {
        show(a);
    } otherwise {
        show(b);
    }
    loop (a < 12) {
        a = a + 1;
    }
    """
).strip()


FUNCTION_CALL_SOURCE = textwrap.dedent(
    """
    num b = 20;
    printf("%d", b);
    """
).strip()


TYPE_ERROR_SOURCE = textwrap.dedent(
    """
    num a = 10;
    text b = "hello";
    a = b;
    """
).strip()


SYNTAX_ERROR_SOURCE = textwrap.dedent(
    """
    num a = 10
    show(a);
    """
).strip()


class CompilerProjectTests(unittest.TestCase):
    def test_lexer_tokenizes_keywords_identifiers_and_constants(self) -> None:
        lexer = Lexer(VALID_SOURCE)
        tokens = lexer.tokenize()
        values = [token.value for token in tokens if token.type != "EOF"]
        self.assertIn("num", values)
        self.assertIn("a", values)
        self.assertIn("10", values)

    def test_parser_accepts_valid_program(self) -> None:
        lexer = Lexer(VALID_SOURCE)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        self.assertGreater(len(program.statements), 0)

    def test_parser_reports_syntax_error(self) -> None:
        lexer = Lexer(SYNTAX_ERROR_SOURCE)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        with self.assertRaises(ParserError):
            parser.parse()

    def test_semantic_analysis_accepts_valid_program(self) -> None:
        lexer = Lexer(VALID_SOURCE)
        program = Parser(lexer.tokenize()).parse()
        symbol_table = SemanticAnalyzer().analyze(program)
        self.assertEqual(symbol_table.lookup("a").value, 10)
        self.assertEqual(symbol_table.lookup("b").value, 20)
        self.assertEqual(symbol_table.lookup("c").value, 50)

    def test_semantic_analysis_reports_type_mismatch(self) -> None:
        lexer = Lexer(TYPE_ERROR_SOURCE)
        program = Parser(lexer.tokenize()).parse()
        analyzer = SemanticAnalyzer()
        with self.assertRaises(SemanticError):
            analyzer.analyze(program)

    def test_tac_generation(self) -> None:
        lexer = Lexer(VALID_SOURCE)
        program = Parser(lexer.tokenize()).parse()
        tac = TACGenerator().generate(program)
        self.assertIn("t1 = b * 2", tac)
        self.assertIn("t2 = a + t1", tac)
        self.assertIn("c = t2", tac)

    def test_control_flow_parsing(self) -> None:
        lexer = Lexer(CONTROL_FLOW_SOURCE)
        program = Parser(lexer.tokenize()).parse()
        self.assertGreaterEqual(len(program.statements), 4)

    def test_function_call_statement(self) -> None:
        lexer = Lexer(FUNCTION_CALL_SOURCE)
        program = Parser(lexer.tokenize()).parse()
        self.assertEqual(len(program.statements), 2)
        symbol_table = SemanticAnalyzer().analyze(program)
        self.assertEqual(symbol_table.lookup("b").value, 20)
        tac = TACGenerator().generate(program)
        self.assertIn("call printf, 2", tac)

    def test_lab_tasks(self) -> None:
        self.assertEqual(count_vowels_consonants("Compiler"), (3, 5))
        self.assertEqual(recognize_token("num"), "Keyword")
        self.assertEqual(recognize_token("value"), "Identifier")
        self.assertEqual(recognize_token("123"), "Constant")
        self.assertEqual(remove_comments("a; // comment\nb;").strip(), "a; \nb;".strip())
        self.assertTrue(validate_expression("a+b*5"))
        self.assertFalse(validate_expression("a+*5"))
        self.assertEqual(evaluate_expression("(5+3)*2"), 16)
        self.assertEqual(check_c_statements("#include<stdio.h>\nint a;"), (True, "Valid C statements"))


if __name__ == "__main__":
    unittest.main()
