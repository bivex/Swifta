"""ANTLR-backed Swift parser adapter."""

from __future__ import annotations

from time import perf_counter

import signal
import threading
from typing import Any

from swifta.domain.model import (
    DiagnosticSeverity,
    GrammarVersion,
    ParseOutcome,
    ParseStatistics,
    SourceUnit,
    StructuralElement,
    StructuralElementKind,
    SyntaxDiagnostic,
)
from swifta.domain.ports import SwiftSyntaxParser
from swifta.infrastructure.antlr.runtime import (
    ANTLR_GRAMMAR_VERSION,
    GeneratedParserTypes,
    load_generated_types,
    parse_source_text,
)


class ParseTimeoutError(TimeoutError):
    pass


class _timeout_context:
    def __init__(self, seconds: float | None) -> None:
        self.seconds = seconds
        self._old_handler: Any = None
        self._armed: bool = False

    def __enter__(self) -> None:
        if (
            self.seconds is not None
            and self.seconds > 0
            and hasattr(signal, "SIGALRM")
            and hasattr(signal, "setitimer")
            and threading.current_thread() is threading.main_thread()
        ):
            def _handler(signum: int, frame: Any) -> None:
                raise ParseTimeoutError(f"parsing timeout exceeded ({self.seconds}s)")

            self._old_handler = signal.signal(signal.SIGALRM, _handler)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
            self._armed = True

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        if self._armed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)
        return False


class AntlrSwiftSyntaxParser(SwiftSyntaxParser):
    def __init__(self, default_timeout_seconds: float | None = 1.5) -> None:
        self._generated = load_generated_types()
        self.default_timeout_seconds = default_timeout_seconds

    @property
    def grammar_version(self) -> GrammarVersion:
        return ANTLR_GRAMMAR_VERSION

    def parse(
        self,
        source_unit: SourceUnit,
        timeout_seconds: float | None = None,
    ) -> ParseOutcome:
        effective_timeout = (
            self.default_timeout_seconds if timeout_seconds is None else timeout_seconds
        )
        started_at = perf_counter()
        try:
            with _timeout_context(effective_timeout):
                parse_result = parse_source_text(source_unit.content, self._generated)
                structure_visitor = _build_structure_visitor(self._generated.visitor_type)()
                structure_visitor.visit(parse_result.tree)

            elements = tuple(structure_visitor.elements)
            elapsed_ms = round((perf_counter() - started_at) * 1000, 3)

            return ParseOutcome.success(
                source_unit=source_unit,
                grammar_version=self.grammar_version,
                diagnostics=parse_result.diagnostics,
                structural_elements=elements,
                statistics=ParseStatistics(
                    token_count=len(parse_result.token_stream.tokens),
                    structural_element_count=len(elements),
                    diagnostic_count=len(parse_result.diagnostics),
                    elapsed_ms=elapsed_ms,
                ),
            )
        except Exception:
            # Fallback to lightweight token scanner when ANTLR AST parse fails or times out
            try:
                fallback_elements = _scan_lightweight_structure(source_unit.content, self._generated)
                elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
                diagnostics = (
                    SyntaxDiagnostic(
                        severity=DiagnosticSeverity.WARNING,
                        message="parsed via lightweight declaration scanner fallback",
                        line=0,
                        column=0,
                    ),
                )
                return ParseOutcome.success(
                    source_unit=source_unit,
                    grammar_version=self.grammar_version,
                    diagnostics=diagnostics,
                    structural_elements=fallback_elements,
                    statistics=ParseStatistics(
                        token_count=0,
                        structural_element_count=len(fallback_elements),
                        diagnostic_count=1,
                        elapsed_ms=elapsed_ms,
                    ),
                )
            except Exception as fallback_error:
                elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
                return ParseOutcome.technical_failure(
                    source_unit=source_unit,
                    grammar_version=self.grammar_version,
                    message=str(fallback_error),
                    elapsed_ms=elapsed_ms,
                )


def _scan_lightweight_structure(
    content: str,
    generated_types: GeneratedParserTypes,
) -> tuple[StructuralElement, ...]:
    from antlr4 import CommonTokenStream, InputStream

    lexer = generated_types.lexer_type(InputStream(content))
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()
    tokens = [t for t in token_stream.tokens if t.type != -1 and t.text.strip()]

    elements: list[StructuralElement] = []
    containers: list[str] = []
    brace_depths: list[int] = []
    pending_container: str | None = None

    i = 0
    n = len(tokens)

    while i < n:
        t = tokens[i]
        txt = t.text

        if txt == "{":
            if pending_container is not None:
                containers.append(pending_container)
                pending_container = None
            brace_depths.append(len(containers))
            i += 1
            continue
        elif txt == "}":
            if brace_depths:
                target_depth = brace_depths.pop()
                while len(containers) > target_depth:
                    containers.pop()
            i += 1
            continue

        kind = None
        if txt == "import":
            kind = StructuralElementKind.IMPORT
        elif txt == "typealias":
            kind = StructuralElementKind.TYPE_ALIAS
        elif txt == "struct":
            kind = StructuralElementKind.STRUCT
        elif txt in ("class", "actor"):
            kind = StructuralElementKind.CLASS
        elif txt == "enum":
            kind = StructuralElementKind.ENUM
        elif txt == "protocol":
            kind = StructuralElementKind.PROTOCOL
        elif txt == "extension":
            kind = StructuralElementKind.EXTENSION
        elif txt == "func":
            kind = StructuralElementKind.FUNCTION
        elif txt == "var":
            kind = StructuralElementKind.VARIABLE
        elif txt == "let":
            kind = StructuralElementKind.CONSTANT

        if kind is not None:
            j = i + 1
            while j < n and (
                tokens[j].text.startswith("@")
                or tokens[j].text in (
                    "public", "private", "fileprivate", "internal", "open",
                    "final", "static", "override", "mutating", "nonmutating",
                    "async", "optional", "required", "lazy", "indirect",
                )
            ):
                j += 1
            if j < n and tokens[j].text not in ("{", "}", ";", "("):
                name = tokens[j].text
                line = t.line
                column = t.column
                container = ".".join(containers) if containers else None

                sig = f"{kind.value} {name}"
                if kind == StructuralElementKind.FUNCTION:
                    sig_tokens = []
                    k = j
                    while k < n and tokens[k].text not in ("{", ";"):
                        sig_tokens.append(tokens[k].text)
                        k += 1
                    sig = "func " + " ".join(sig_tokens)

                elements.append(
                    StructuralElement(
                        kind=kind,
                        name=name,
                        line=line,
                        column=column,
                        container=container,
                        signature=sig,
                    )
                )

                if kind in (
                    StructuralElementKind.STRUCT,
                    StructuralElementKind.CLASS,
                    StructuralElementKind.ENUM,
                    StructuralElementKind.PROTOCOL,
                    StructuralElementKind.EXTENSION,
                ):
                    pending_container = name
                i = j
        i += 1

    return tuple(elements)


def _build_structure_visitor(visitor_base: type) -> type:
    class SwiftStructureVisitor(visitor_base):
        def __init__(self) -> None:
            super().__init__()
            self.elements: list[StructuralElement] = []
            self._containers: list[str] = []

        def visitImport_declaration(self, ctx):
            import_path = ctx.import_path().getText()
            self._append(
                StructuralElementKind.IMPORT,
                import_path,
                ctx,
                signature=f"import {import_path}",
            )
            return None

        def visitTypealias_declaration(self, ctx):
            name = ctx.typealias_name().getText()
            self._append(
                StructuralElementKind.TYPE_ALIAS,
                name,
                ctx,
                signature=f"typealias {name}",
            )
            return None

        def visitConstant_declaration(self, ctx):
            for name in self._extract_pattern_names(ctx.pattern_initializer_list()):
                self._append(
                    StructuralElementKind.CONSTANT,
                    name,
                    ctx,
                    signature=f"let {name}",
                )
            return None

        def visitVariable_declaration(self, ctx):
            if ctx.variable_name() is not None:
                variable_name = ctx.variable_name().getText()
                self._append(
                    StructuralElementKind.VARIABLE,
                    variable_name,
                    ctx,
                    signature=f"var {variable_name}",
                )
                return None

            for name in self._extract_pattern_names(ctx.pattern_initializer_list()):
                self._append(
                    StructuralElementKind.VARIABLE,
                    name,
                    ctx,
                    signature=f"var {name}",
                )
            return None

        def visitFunction_declaration(self, ctx):
            name = ctx.function_name().getText()
            signature = ctx.function_signature().getText()
            self._append(
                StructuralElementKind.FUNCTION,
                name,
                ctx,
                signature=f"func {name}{signature}",
            )
            return None

        def visitEnum_declaration(self, ctx):
            name = self._extract_enum_name(ctx)
            self._append(StructuralElementKind.ENUM, name, ctx, signature=f"enum {name}")
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitStruct_declaration(self, ctx):
            name = ctx.struct_name().getText()
            self._append(StructuralElementKind.STRUCT, name, ctx, signature=f"struct {name}")
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitClass_declaration(self, ctx):
            name = ctx.class_name().getText()
            self._append(StructuralElementKind.CLASS, name, ctx, signature=f"class {name}")
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitProtocol_declaration(self, ctx):
            name = ctx.protocol_name().getText()
            self._append(
                StructuralElementKind.PROTOCOL,
                name,
                ctx,
                signature=f"protocol {name}",
            )
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitExtension_declaration(self, ctx):
            name = ctx.type_identifier().getText()
            self._append(
                StructuralElementKind.EXTENSION,
                name,
                ctx,
                signature=f"extension {name}",
            )
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def _append(self, kind, name: str, ctx, signature: str | None = None) -> None:
            container = ".".join(self._containers) if self._containers else None
            self.elements.append(
                StructuralElement(
                    kind=kind,
                    name=name,
                    line=ctx.start.line,
                    column=ctx.start.column,
                    container=container,
                    signature=signature,
                )
            )

        def _with_container(self, name: str, callback):
            self._containers.append(name)
            try:
                return callback()
            finally:
                self._containers.pop()

        def _extract_enum_name(self, enum_ctx) -> str:
            if enum_ctx.union_style_enum() is not None:
                return enum_ctx.union_style_enum().enum_name().getText()
            if enum_ctx.raw_value_style_enum() is not None:
                return enum_ctx.raw_value_style_enum().enum_name().getText()
            return "enum"

        def _extract_pattern_names(self, pattern_initializer_list_ctx) -> tuple[str, ...]:
            names: list[str] = []
            for pattern_initializer_ctx in pattern_initializer_list_ctx.pattern_initializer():
                names.extend(self._extract_names_from_pattern(pattern_initializer_ctx.pattern()))
            return tuple(names)

        def _extract_names_from_pattern(self, pattern_ctx) -> list[str]:
            if pattern_ctx is None:
                return []

            names: list[str] = []
            identifier_pattern_ctx = getattr(pattern_ctx, "identifier_pattern", None)
            if callable(identifier_pattern_ctx):
                identifier = pattern_ctx.identifier_pattern()
                if identifier is not None:
                    names.append(identifier.getText())

            tuple_pattern_ctx = getattr(pattern_ctx, "tuple_pattern", None)
            if callable(tuple_pattern_ctx):
                tuple_pattern = pattern_ctx.tuple_pattern()
                if tuple_pattern is not None and tuple_pattern.tuple_pattern_element_list() is not None:
                    for element in tuple_pattern.tuple_pattern_element_list().tuple_pattern_element():
                        names.extend(self._extract_names_from_pattern(element.pattern()))

            nested_pattern_accessor = getattr(pattern_ctx, "pattern", None)
            if callable(nested_pattern_accessor):
                nested_pattern = pattern_ctx.pattern()
                if nested_pattern is not None and nested_pattern is not pattern_ctx:
                    names.extend(self._extract_names_from_pattern(nested_pattern))

            if not names:
                names.append(pattern_ctx.getText())

            return names

    return SwiftStructureVisitor
