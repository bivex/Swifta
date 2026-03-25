"""Render structured control flow as Nassi-Shneiderman HTML."""

from __future__ import annotations

from html import escape

from swifta.domain.control_flow import (
    ActionFlowStep,
    ControlFlowDiagram,
    ControlFlowStep,
    DeferFlowStep,
    DoCatchFlowStep,
    ForInFlowStep,
    GuardFlowStep,
    IfFlowStep,
    RepeatWhileFlowStep,
    SwitchCaseFlow,
    SwitchFlowStep,
    WhileFlowStep,
)
from swifta.domain.ports import NassiDiagramRenderer


class HtmlNassiDiagramRenderer(NassiDiagramRenderer):
    def render(self, diagram: ControlFlowDiagram) -> str:
        sections = "".join(self._render_function(function) for function in diagram.functions)
        if not sections:
            sections = '<section class="function-card"><p class="empty-file">No functions found.</p></section>'

        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Nassi-Shneiderman Diagram</title>
    <style>
      :root {{
        --line: #183153;
        --ink: #132238;
        --paper: #f7f4ed;
        --accent: #c34a36;
        --soft: #efe6d8;
        --branch: #fffdf8;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        padding: 32px;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, #fff5dc 0, transparent 32%),
          linear-gradient(180deg, #fffdfa 0%, #f1ede4 100%);
      }}
      .page {{
        max-width: 1200px;
        margin: 0 auto;
      }}
      .hero {{
        margin-bottom: 24px;
        padding: 24px 28px;
        border: 3px solid var(--line);
        background: rgba(255, 255, 255, 0.72);
      }}
      .hero h1 {{
        margin: 0 0 8px;
        font-size: 28px;
      }}
      .hero p {{
        margin: 0;
        overflow-wrap: anywhere;
      }}
      .function-card {{
        margin-bottom: 32px;
        border: 3px solid var(--line);
        background: rgba(255, 255, 255, 0.84);
      }}
      .function-title {{
        margin: 0;
        padding: 16px 20px;
        border-bottom: 3px solid var(--line);
        background: var(--soft);
        font-size: 20px;
      }}
      .function-signature {{
        padding: 0 20px 16px;
        color: #5e4d3d;
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      }}
      .ns-sequence {{
        display: flex;
        flex-direction: column;
      }}
      .ns-node {{
        border-top: 2px solid var(--line);
        background: var(--paper);
      }}
      .ns-node:first-child {{
        border-top: 0;
      }}
      .ns-header, .ns-label, .case-title {{
        padding: 10px 14px;
        border-bottom: 2px solid var(--line);
        background: var(--soft);
        font-weight: 700;
      }}
      .ns-label {{
        background: #fff;
        font-weight: 500;
      }}
      .ns-body {{
        border-left: 0;
      }}
      .ns-branches {{
        display: grid;
        grid-template-columns: 1fr 1fr;
      }}
      .ns-branch {{
        min-width: 0;
        border-left: 2px solid var(--line);
        background: var(--branch);
      }}
      .ns-branch:first-child {{
        border-left: 0;
      }}
      .ns-branch-title {{
        padding: 8px 12px;
        border-bottom: 2px solid var(--line);
        background: #f3ecdf;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 12px;
        font-weight: 700;
      }}
      .case {{
        border-top: 2px solid var(--line);
      }}
      .case:first-child {{
        border-top: 0;
      }}
      .ns-catches {{
        border-top: 2px solid var(--line);
      }}
      .empty {{
        padding: 12px 14px;
        color: #6e6154;
        font-style: italic;
      }}
      .empty-file {{
        margin: 0;
        padding: 20px;
      }}
      @media (max-width: 800px) {{
        body {{ padding: 16px; }}
        .ns-branches {{ grid-template-columns: 1fr; }}
        .ns-branch {{ border-left: 0; border-top: 2px solid var(--line); }}
        .ns-branch:first-child {{ border-top: 0; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <h1>Nassi-Shneiderman Control Flow</h1>
        <p>{escape(diagram.source_location)}</p>
      </section>
      {sections}
    </main>
  </body>
</html>
"""

    def _render_function(self, function) -> str:
        return (
            '<section class="function-card">'
            f'<h2 class="function-title">{escape(function.qualified_name)}</h2>'
            f'<div class="function-signature">{escape(function.signature)}</div>'
            f"{self._render_sequence(function.steps)}"
            "</section>"
        )

    def _render_sequence(self, steps: tuple[ControlFlowStep, ...]) -> str:
        if not steps:
            return '<div class="empty">No structured steps.</div>'
        rendered = "".join(self._render_step(step) for step in steps)
        return f'<div class="ns-sequence">{rendered}</div>'

    def _render_step(self, step: ControlFlowStep) -> str:
        if isinstance(step, ActionFlowStep):
            return f'<div class="ns-node ns-action"><div class="ns-label">{escape(step.label)}</div></div>'
        if isinstance(step, IfFlowStep):
            return (
                '<div class="ns-node ns-if">'
                f'<div class="ns-header">IF {escape(step.condition)}</div>'
                '<div class="ns-branches">'
                '<div class="ns-branch"><div class="ns-branch-title">Then</div>'
                f"{self._render_sequence(step.then_steps)}"
                "</div>"
                '<div class="ns-branch"><div class="ns-branch-title">Else</div>'
                f"{self._render_sequence(step.else_steps)}"
                "</div>"
                "</div>"
                "</div>"
            )
        if isinstance(step, GuardFlowStep):
            return (
                '<div class="ns-node ns-guard">'
                f'<div class="ns-header">GUARD {escape(step.condition)}</div>'
                '<div class="ns-branch"><div class="ns-branch-title">Else</div>'
                f"{self._render_sequence(step.else_steps)}"
                "</div>"
                "</div>"
            )
        if isinstance(step, WhileFlowStep):
            return self._render_single_body("WHILE", step.condition, step.body_steps)
        if isinstance(step, ForInFlowStep):
            return self._render_single_body("FOR", step.header, step.body_steps)
        if isinstance(step, RepeatWhileFlowStep):
            return (
                '<div class="ns-node ns-repeat">'
                '<div class="ns-header">REPEAT</div>'
                f"{self._render_sequence(step.body_steps)}"
                f'<div class="ns-header">WHILE {escape(step.condition)}</div>'
                "</div>"
            )
        if isinstance(step, SwitchFlowStep):
            cases = "".join(self._render_case(case) for case in step.cases)
            cases_markup = cases or '<div class="empty">No cases.</div>'
            return (
                '<div class="ns-node ns-switch">'
                f'<div class="ns-header">SWITCH {escape(step.expression)}</div>'
                f'<div class="ns-cases">{cases_markup}</div>'
                "</div>"
            )
        if isinstance(step, DoCatchFlowStep):
            catches = "".join(
                self._render_single_body("CATCH", catch.pattern, catch.steps)
                for catch in step.catches
            )
            return (
                '<div class="ns-node ns-do-catch">'
                '<div class="ns-header">DO</div>'
                f"{self._render_sequence(step.body_steps)}"
                f'<div class="ns-catches">{catches}</div>'
                "</div>"
            )
        if isinstance(step, DeferFlowStep):
            return self._render_single_body("DEFER", "", step.body_steps)
        raise TypeError(f"unsupported step type: {type(step)!r}")

    def _render_case(self, case: SwitchCaseFlow) -> str:
        return (
            '<div class="case">'
            f'<div class="case-title">{escape(case.label)}</div>'
            f"{self._render_sequence(case.steps)}"
            "</div>"
        )

    def _render_single_body(
        self,
        keyword: str,
        label: str,
        steps: tuple[ControlFlowStep, ...],
    ) -> str:
        title = keyword if not label else f"{keyword} {label}"
        return (
            '<div class="ns-node">'
            f'<div class="ns-header">{escape(title)}</div>'
            f"{self._render_sequence(steps)}"
            "</div>"
        )
