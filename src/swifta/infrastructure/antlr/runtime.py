"""Shared ANTLR runtime helpers."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from antlr4 import CommonTokenStream, InputStream
from antlr4.atn.PredictionMode import PredictionMode
from antlr4.error.ErrorStrategy import BailErrorStrategy
from antlr4.error.Errors import ParseCancellationException

from swifta.domain.errors import GeneratedParserNotAvailableError
from swifta.domain.model import GrammarVersion, SyntaxDiagnostic
from swifta.infrastructure.antlr.error_listener import CollectingErrorListener


ANTLR_GRAMMAR_VERSION = GrammarVersion(
    "antlr4@4.13.2+python-compat:antlr/grammars-v4/swift/swift5 (targets Swift 5.4)"
)


@dataclass(frozen=True, slots=True)
class GeneratedParserTypes:
    lexer_type: type
    parser_type: type
    visitor_type: type


@dataclass(frozen=True, slots=True)
class ParseTreeResult:
    token_stream: CommonTokenStream
    parser: object
    tree: object
    diagnostics: tuple[SyntaxDiagnostic, ...]


def load_generated_types() -> GeneratedParserTypes:
    try:
        lexer_module = importlib.import_module(
            "swifta.infrastructure.antlr.generated.swift5.Swift5Lexer"
        )
        parser_module = importlib.import_module(
            "swifta.infrastructure.antlr.generated.swift5.Swift5Parser"
        )
        visitor_module = importlib.import_module(
            "swifta.infrastructure.antlr.generated.swift5.Swift5ParserVisitor"
        )
    except ModuleNotFoundError as error:
        raise GeneratedParserNotAvailableError(
            "generated Swift parser artifacts are missing; run "
            "`uv run python scripts/generate_swift_parser.py` first"
        ) from error

    return GeneratedParserTypes(
        lexer_type=lexer_module.Swift5Lexer,
        parser_type=parser_module.Swift5Parser,
        visitor_type=visitor_module.Swift5ParserVisitor,
    )


def parse_source_text(
    source_text: str,
    generated_types: GeneratedParserTypes | None = None,
) -> ParseTreeResult:
    generated = generated_types or load_generated_types()

    try:
        return _parse_source_text_fast(source_text, generated)
    except ParseCancellationException:
        return _parse_source_text_full(source_text, generated)


def _parse_source_text_fast(
    source_text: str,
    generated: GeneratedParserTypes,
) -> ParseTreeResult:
    lexer = generated.lexer_type(InputStream(source_text))
    lexer_errors = CollectingErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(lexer_errors)

    token_stream = CommonTokenStream(lexer)
    parser = generated.parser_type(token_stream)
    parser._interp.predictionMode = PredictionMode.SLL
    parser._errHandler = BailErrorStrategy()
    parser.removeErrorListeners()

    tree = parser.top_level()
    token_stream.fill()

    return ParseTreeResult(
        token_stream=token_stream,
        parser=parser,
        tree=tree,
        diagnostics=tuple(lexer_errors.diagnostics),
    )


def _parse_source_text_full(
    source_text: str,
    generated: GeneratedParserTypes,
) -> ParseTreeResult:
    lexer = generated.lexer_type(InputStream(source_text))
    lexer_errors = CollectingErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(lexer_errors)

    token_stream = CommonTokenStream(lexer)
    parser = generated.parser_type(token_stream)
    parser_errors = CollectingErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(parser_errors)

    tree = parser.top_level()
    token_stream.fill()

    return ParseTreeResult(
        token_stream=token_stream,
        parser=parser,
        tree=tree,
        diagnostics=tuple(lexer_errors.diagnostics + parser_errors.diagnostics),
    )
