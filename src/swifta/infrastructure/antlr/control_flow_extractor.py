"""Extract structured control flow from Swift source through ANTLR."""

from __future__ import annotations

import re
from dataclasses import dataclass

from swifta.domain.control_flow import (
    ActionFlowStep,
    CatchClauseFlow,
    ControlFlowDiagram,
    ControlFlowStep,
    DeferFlowStep,
    DoCatchFlowStep,
    ForInFlowStep,
    FunctionControlFlow,
    GuardFlowStep,
    IfFlowStep,
    RepeatWhileFlowStep,
    SwitchCaseFlow,
    SwitchFlowStep,
    WhileFlowStep,
)
from swifta.domain.model import SourceUnit
from swifta.domain.ports import SwiftControlFlowExtractor
from swifta.infrastructure.antlr.runtime import load_generated_types, parse_source_text


@dataclass(frozen=True, slots=True)
class _ExtractorContext:
    token_stream: object

    def text(self, ctx) -> str:
        if ctx is None:
            return ""
        return self.token_stream.getText(
            start=ctx.start.tokenIndex,
            stop=ctx.stop.tokenIndex,
        )

    def compact(self, ctx, *, limit: int = 96) -> str:
        text = re.sub(r"\s+", " ", self.text(ctx)).strip()
        if len(text) <= limit:
            return text
        return f"{text[: limit - 1]}..."


class AntlrSwiftControlFlowExtractor(SwiftControlFlowExtractor):
    def __init__(self) -> None:
        self._generated = load_generated_types()

    def extract(self, source_unit: SourceUnit) -> ControlFlowDiagram:
        parse_result = parse_source_text(source_unit.content, self._generated)
        visitor = _build_control_flow_visitor(
            self._generated.visitor_type,
            _ExtractorContext(token_stream=parse_result.token_stream),
        )()
        visitor.visit(parse_result.tree)
        return ControlFlowDiagram(
            source_location=source_unit.location,
            functions=tuple(visitor.functions),
        )


def _build_control_flow_visitor(visitor_base: type, context: _ExtractorContext) -> type:
    class SwiftControlFlowVisitor(visitor_base):
        def __init__(self) -> None:
            super().__init__()
            self.functions: list[FunctionControlFlow] = []
            self._containers: list[str] = []

        def visitStruct_declaration(self, ctx):
            name = ctx.struct_name().getText()
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitClass_declaration(self, ctx):
            name = ctx.class_name().getText()
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitEnum_declaration(self, ctx):
            name = ctx.enum_name().getText()
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitProtocol_declaration(self, ctx):
            name = ctx.protocol_name().getText()
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitExtension_declaration(self, ctx):
            name = ctx.type_identifier().getText()
            return self._with_container(name, lambda: self.visitChildren(ctx))

        def visitFunction_declaration(self, ctx):
            if ctx.function_body() is None:
                return None

            name = ctx.function_name().getText()
            signature = context.compact(ctx.function_signature())
            code_block = ctx.function_body().code_block()
            self.functions.append(
                FunctionControlFlow(
                    name=name,
                    signature=f"func {name}{signature}",
                    container=".".join(self._containers) if self._containers else None,
                    steps=self._extract_code_block(code_block),
                )
            )
            return None

        def _with_container(self, name: str, callback):
            self._containers.append(name)
            try:
                return callback()
            finally:
                self._containers.pop()

        def _extract_code_block(self, code_block_ctx) -> tuple[ControlFlowStep, ...]:
            if code_block_ctx is None or code_block_ctx.statements() is None:
                return ()
            return self._extract_statements(code_block_ctx.statements())

        def _extract_statements(self, statements_ctx) -> tuple[ControlFlowStep, ...]:
            steps: list[ControlFlowStep] = []
            for statement_ctx in statements_ctx.statement():
                extracted = self._extract_statement(statement_ctx)
                if extracted is not None:
                    steps.append(extracted)
            return tuple(steps)

        def _extract_statement(self, statement_ctx) -> ControlFlowStep | None:
            if statement_ctx.loop_statement() is not None:
                return self._extract_loop_statement(statement_ctx.loop_statement())
            if statement_ctx.branch_statement() is not None:
                return self._extract_branch_statement(statement_ctx.branch_statement())
            if statement_ctx.labeled_statement() is not None:
                return self._extract_labeled_statement(statement_ctx.labeled_statement())
            if statement_ctx.control_transfer_statement() is not None:
                return ActionFlowStep(context.compact(statement_ctx.control_transfer_statement()))
            if statement_ctx.defer_statement() is not None:
                return DeferFlowStep(
                    body_steps=self._extract_code_block(statement_ctx.defer_statement().code_block())
                )
            if statement_ctx.do_statement() is not None:
                return self._extract_do_statement(statement_ctx.do_statement())
            if statement_ctx.declaration() is not None:
                return ActionFlowStep(context.compact(statement_ctx.declaration()))
            if statement_ctx.expression() is not None:
                return ActionFlowStep(context.compact(statement_ctx.expression()))
            if statement_ctx.compiler_control_statement() is not None:
                return ActionFlowStep(context.compact(statement_ctx.compiler_control_statement()))
            return ActionFlowStep(context.compact(statement_ctx))

        def _extract_labeled_statement(self, labeled_ctx) -> ControlFlowStep:
            label = labeled_ctx.label_name().getText()
            if labeled_ctx.loop_statement() is not None:
                inner = self._extract_loop_statement(labeled_ctx.loop_statement())
                return ActionFlowStep(f"label {label}") if inner is None else inner
            if labeled_ctx.if_statement() is not None:
                return self._extract_if_statement(labeled_ctx.if_statement())
            if labeled_ctx.switch_statement() is not None:
                return self._extract_switch_statement(labeled_ctx.switch_statement())
            if labeled_ctx.do_statement() is not None:
                return self._extract_do_statement(labeled_ctx.do_statement())
            return ActionFlowStep(f"label {label}")

        def _extract_loop_statement(self, loop_ctx) -> ControlFlowStep:
            if loop_ctx.for_in_statement() is not None:
                return self._extract_for_in_statement(loop_ctx.for_in_statement())
            if loop_ctx.while_statement() is not None:
                return self._extract_while_statement(loop_ctx.while_statement())
            return self._extract_repeat_while_statement(loop_ctx.repeat_while_statement())

        def _extract_branch_statement(self, branch_ctx) -> ControlFlowStep:
            if branch_ctx.if_statement() is not None:
                return self._extract_if_statement(branch_ctx.if_statement())
            if branch_ctx.guard_statement() is not None:
                return self._extract_guard_statement(branch_ctx.guard_statement())
            return self._extract_switch_statement(branch_ctx.switch_statement())

        def _extract_if_statement(self, if_ctx) -> IfFlowStep:
            then_steps = self._extract_code_block(if_ctx.code_block())
            else_steps: tuple[ControlFlowStep, ...] = ()
            if if_ctx.else_clause() is not None:
                else_clause = if_ctx.else_clause()
                if else_clause.code_block() is not None:
                    else_steps = self._extract_code_block(else_clause.code_block())
                elif else_clause.if_statement() is not None:
                    else_steps = (self._extract_if_statement(else_clause.if_statement()),)
            return IfFlowStep(
                condition=context.compact(if_ctx.condition_list()),
                then_steps=then_steps,
                else_steps=else_steps,
            )

        def _extract_guard_statement(self, guard_ctx) -> GuardFlowStep:
            return GuardFlowStep(
                condition=context.compact(guard_ctx.condition_list()),
                else_steps=self._extract_code_block(guard_ctx.code_block()),
            )

        def _extract_switch_statement(self, switch_ctx) -> SwitchFlowStep:
            cases: list[SwitchCaseFlow] = []
            for switch_case_ctx in self._flatten_switch_cases(switch_ctx.switch_cases()):
                cases.append(self._extract_switch_case(switch_case_ctx))
            return SwitchFlowStep(
                expression=context.compact(switch_ctx.expression()),
                cases=tuple(cases),
            )

        def _extract_switch_case(self, switch_case_ctx) -> SwitchCaseFlow:
            if switch_case_ctx.conditional_switch_case() is not None:
                return SwitchCaseFlow(
                    label=context.compact(switch_case_ctx.conditional_switch_case()),
                    steps=(),
                )

            label_ctx = switch_case_ctx.case_label() or switch_case_ctx.default_label()
            steps = ()
            if switch_case_ctx.statements() is not None:
                steps = self._extract_statements(switch_case_ctx.statements())
            return SwitchCaseFlow(
                label=context.compact(label_ctx),
                steps=steps,
            )

        def _flatten_switch_cases(self, switch_cases_ctx) -> tuple[object, ...]:
            cases: list[object] = []
            current = switch_cases_ctx
            while current is not None:
                cases.append(current.switch_case())
                current = current.switch_cases()
            return tuple(cases)

        def _extract_for_in_statement(self, for_ctx) -> ForInFlowStep:
            return ForInFlowStep(
                header=f"{context.compact(for_ctx.pattern())} in {context.compact(for_ctx.expression())}",
                body_steps=self._extract_code_block(for_ctx.code_block()),
            )

        def _extract_while_statement(self, while_ctx) -> WhileFlowStep:
            return WhileFlowStep(
                condition=context.compact(while_ctx.condition_list()),
                body_steps=self._extract_code_block(while_ctx.code_block()),
            )

        def _extract_repeat_while_statement(self, repeat_ctx) -> RepeatWhileFlowStep:
            return RepeatWhileFlowStep(
                condition=context.compact(repeat_ctx.expression()),
                body_steps=self._extract_code_block(repeat_ctx.code_block()),
            )

        def _extract_do_statement(self, do_ctx) -> DoCatchFlowStep:
            catches: list[CatchClauseFlow] = []
            if do_ctx.catch_clauses() is not None:
                for catch_clause_ctx in do_ctx.catch_clauses().catch_clause():
                    catches.append(
                        CatchClauseFlow(
                            pattern=context.compact(catch_clause_ctx.catch_pattern_list())
                            if catch_clause_ctx.catch_pattern_list() is not None
                            else "catch",
                            steps=self._extract_code_block(catch_clause_ctx.code_block()),
                        )
                    )

            return DoCatchFlowStep(
                body_steps=self._extract_code_block(do_ctx.code_block()),
                catches=tuple(catches),
            )

    return SwiftControlFlowVisitor
