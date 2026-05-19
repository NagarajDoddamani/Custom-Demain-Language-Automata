"""Beginner-friendly wrapper package for the compiler stages."""

from compiler_dsl.core.compiler import CompilerSession
from compiler_dsl.core.lexer import Lexer, LexerError, Token
from compiler_dsl.core.parser import Parser, ParserError
from compiler_dsl.core.semantic import SemanticAnalyzer, SemanticError, SymbolInfo, SymbolTable
from compiler_dsl.core.tac import TACGenerator

