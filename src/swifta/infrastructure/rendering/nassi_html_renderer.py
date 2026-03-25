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
    <title>Nassi-Shneiderman Control Flow</title>
    <style>
      :root {{
        --line: #17344a;
        --ink: #112233;
        --muted: #6a5f53;
        --canvas: #f4eee1;
        --paper: #fffdf8;
        --card: rgba(255, 255, 255, 0.9);
        --soft: #efe3cf;
        --soft-2: #fbf6ec;
        --shadow: 0 18px 44px rgba(23, 52, 74, 0.12);
        --action-bg: #ffffff;
        --action-line: #baa98d;
        --if-bg: #fff0d5;
        --if-line: #d38717;
        --loop-bg: #dff3fb;
        --loop-line: #1f7898;
        --switch-bg: #dff4ec;
        --switch-line: #187a63;
        --guard-bg: #fde3dd;
        --guard-line: #c94e43;
        --do-bg: #ece8df;
        --do-line: #6d665a;
        --defer-bg: #efe7d4;
        --defer-line: #86693f;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        padding: 32px;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, #fff5dc 0, transparent 30%),
          linear-gradient(180deg, #fffaf1 0%, var(--canvas) 100%);
      }}
      .page {{
        max-width: 1180px;
        margin: 0 auto;
      }}
      .hero {{
        margin-bottom: 28px;
        padding: 24px 28px;
        border: 3px solid var(--line);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(250, 243, 229, 0.9));
        box-shadow: var(--shadow);
      }}
      .eyebrow {{
        margin: 0 0 8px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 12px;
        font-weight: 700;
      }}
      .hero h1 {{
        margin: 0 0 8px;
        font-size: 30px;
        line-height: 1.05;
      }}
      .hero-path {{
        margin: 0;
        color: var(--muted);
        overflow-wrap: anywhere;
      }}
      .function-card {{
        margin-bottom: 32px;
        border: 3px solid var(--line);
        background: var(--card);
        box-shadow: var(--shadow);
      }}
      .function-head {{
        padding: 18px 20px 14px;
        border-bottom: 3px solid var(--line);
        background: linear-gradient(180deg, var(--soft) 0%, #f6efe2 100%);
      }}
      .function-title {{
        margin: 0;
        font-size: 24px;
      }}
      .function-signature {{
        margin-top: 8px;
        color: var(--muted);
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 13px;
      }}
      .function-body {{
        padding: 18px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(249, 244, 235, 0.78));
      }}
      .ns-sequence {{
        display: flex;
        flex-direction: column;
      }}
      .ns-depth-0 {{
        gap: 16px;
      }}
      .ns-depth-1,
      .ns-depth-2,
      .ns-depth-3,
      .ns-depth-4 {{
        gap: 0;
      }}
      .ns-node {{
        overflow: hidden;
        border: 2px solid var(--line);
        background: var(--paper);
      }}
      .ns-depth-0 > .ns-node {{
        border-width: 3px;
        box-shadow: 0 10px 24px rgba(23, 52, 74, 0.08);
      }}
      .ns-header,
      .ns-footer,
      .ns-label,
      .case-title {{
        padding: 10px 14px;
        border-bottom: 2px solid var(--line);
        background: var(--soft-2);
        font-weight: 700;
        line-height: 1.35;
        overflow-wrap: anywhere;
      }}
      .ns-footer {{
        border-top: 2px solid var(--line);
        border-bottom: 0;
      }}
      .ns-label {{
        border-bottom: 0;
        background: var(--action-bg);
      }}
      .action-text {{
        display: block;
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 13px;
        line-height: 1.45;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }}
      .ns-action {{
        border-color: var(--action-line);
        background: var(--action-bg);
      }}
      .ns-if {{
        border-color: var(--if-line);
        background: var(--if-bg);
      }}
      .ns-if > .ns-header {{
        background: var(--if-bg);
        color: #8d5f11;
      }}
      .ns-guard {{
        border-color: var(--guard-line);
        background: var(--guard-bg);
      }}
      .ns-guard > .ns-header {{
        background: var(--guard-bg);
        color: #8d352d;
      }}
      .ns-loop {{
        border-color: var(--loop-line);
        background: var(--loop-bg);
      }}
      .ns-loop > .ns-header,
      .ns-repeat > .ns-header,
      .ns-repeat > .ns-footer {{
        background: var(--loop-bg);
        color: #165d76;
      }}
      .ns-repeat {{
        border-color: var(--loop-line);
        background: var(--loop-bg);
      }}
      .ns-switch {{
        border-color: var(--switch-line);
        background: var(--switch-bg);
      }}
      .ns-switch > .ns-header {{
        background: var(--switch-bg);
        color: #145f4e;
      }}
      .ns-do-catch {{
        border-color: var(--do-line);
        background: var(--do-bg);
      }}
      .ns-do-catch > .ns-header {{
        background: var(--do-bg);
        color: #565044;
      }}
      .ns-defer {{
        border-color: var(--defer-line);
        background: var(--defer-bg);
      }}
      .ns-defer > .ns-header {{
        background: var(--defer-bg);
        color: #6e552f;
      }}
      .ns-branches {{
        display: grid;
        grid-template-columns: 1fr 1fr;
      }}
      .ns-branch {{
        min-width: 0;
        border-left: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.6);
      }}
      .ns-branch:first-child {{
        border-left: 0;
      }}
      .ns-branch-title {{
        padding: 9px 12px;
        border-bottom: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.74);
        color: var(--muted);
        font-size: 12px;
        font-weight: 700;
      }}
      .ns-cases {{
        background: rgba(255, 255, 255, 0.58);
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
      .case-title {{
        background: rgba(255, 255, 255, 0.74);
      }}
      .empty {{
        padding: 12px 14px;
        color: var(--muted);
        font-style: italic;
        background: rgba(255, 255, 255, 0.6);
      }}
      .ns-note {{
        padding: 10px 14px;
        border-top: 2px dashed rgba(23, 52, 74, 0.25);
        color: var(--muted);
        background: rgba(255, 255, 255, 0.48);
        font-size: 13px;
        font-style: italic;
      }}
      .empty-file {{
        margin: 0;
        padding: 24px;
      }}
      @media (max-width: 800px) {{
        body {{ padding: 16px; }}
        .hero {{ padding: 20px; }}
        .function-body {{ padding: 12px; }}
        .ns-branches {{ grid-template-columns: 1fr; }}
        .ns-branch {{
          border-left: 0;
          border-top: 2px solid var(--line);
        }}
        .ns-branch:first-child {{
          border-top: 0;
        }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <p class="eyebrow">Structured Control Flow</p>
        <h1>Nassi-Shneiderman Control Flow</h1>
        <p class="hero-path">{escape(diagram.source_location)}</p>
      </section>
      {sections}
    </main>
  </body>
</html>
"""

    def _render_function(self, function) -> str:
        return (
            '<section class="function-card">'
            '<div class="function-head">'
            f'<h2 class="function-title">{escape(function.qualified_name)}</h2>'
            f'<div class="function-signature">{escape(function.signature)}</div>'
            "</div>"
            '<div class="function-body">'
            f"{self._render_sequence(function.steps, depth=0)}"
            "</div>"
            "</section>"
        )

    def _render_sequence(self, steps: tuple[ControlFlowStep, ...], *, depth: int) -> str:
        if not steps:
            return '<div class="empty">No structured steps.</div>'
        rendered = "".join(self._render_step(step, depth=depth) for step in steps)
        return f'<div class="ns-sequence ns-depth-{depth}">{rendered}</div>'

    def _render_step(self, step: ControlFlowStep, *, depth: int) -> str:
        if isinstance(step, ActionFlowStep):
            return (
                '<div class="ns-node ns-action">'
                f'<div class="ns-label" aria-label="Action {escape(step.label)}">'
                f'<code class="action-text">{escape(step.label)}</code>'
                "</div>"
                "</div>"
            )
        if isinstance(step, IfFlowStep):
            if step.else_steps:
                else_markup = (
                    '<div class="ns-branch"><div class="ns-branch-title">Else</div>'
                    f"{self._render_sequence(step.else_steps, depth=depth + 1)}"
                    "</div>"
                )
                trailing_note = ""
            else:
                else_markup = ""
                trailing_note = '<div class="ns-note">Otherwise the flow continues.</div>'

            return (
                '<div class="ns-node ns-if">'
                f"{self._render_header(f'If {step.condition}')}"
                '<div class="ns-branches">'
                '<div class="ns-branch"><div class="ns-branch-title">Then</div>'
                f"{self._render_sequence(step.then_steps, depth=depth + 1)}"
                "</div>"
                f"{else_markup}"
                "</div>"
                f"{trailing_note}"
                "</div>"
            )
        if isinstance(step, GuardFlowStep):
            return (
                '<div class="ns-node ns-guard">'
                f"{self._render_header(f'Guard {step.condition}')}"
                '<div class="ns-branch"><div class="ns-branch-title">Failure / exit</div>'
                f"{self._render_sequence(step.else_steps, depth=depth + 1)}"
                "</div>"
                "</div>"
            )
        if isinstance(step, WhileFlowStep):
            return self._render_single_body(f"While {step.condition}", step.body_steps, depth=depth)
        if isinstance(step, ForInFlowStep):
            return self._render_single_body(f"For {step.header}", step.body_steps, depth=depth)
        if isinstance(step, RepeatWhileFlowStep):
            return (
                '<div class="ns-node ns-repeat">'
                f"{self._render_header('Repeat')}"
                f"{self._render_sequence(step.body_steps, depth=depth + 1)}"
                f"{self._render_footer(f'While {step.condition}')}"
                "</div>"
            )
        if isinstance(step, SwitchFlowStep):
            cases = "".join(self._render_case(case) for case in step.cases)
            cases_markup = cases or '<div class="empty">No cases.</div>'
            return (
                '<div class="ns-node ns-switch">'
                f"{self._render_header(f'Switch {step.expression}')}"
                f'<div class="ns-cases">{cases_markup}</div>'
                "</div>"
            )
        if isinstance(step, DoCatchFlowStep):
            catches = "".join(
                self._render_single_body(
                    f"Catch {catch.pattern}",
                    catch.steps,
                    depth=depth + 1,
                    css_class="ns-do-catch",
                )
                for catch in step.catches
            )
            return (
                '<div class="ns-node ns-do-catch">'
                f"{self._render_header('Do')}"
                f"{self._render_sequence(step.body_steps, depth=depth + 1)}"
                f'<div class="ns-catches">{catches}</div>'
                "</div>"
            )
        if isinstance(step, DeferFlowStep):
            return self._render_single_body("Defer", step.body_steps, depth=depth, css_class="ns-defer")
        raise TypeError(f"unsupported step type: {type(step)!r}")

    def _render_case(self, case: SwitchCaseFlow) -> str:
        return (
            '<div class="case">'
            f"{self._render_case_title(case.label)}"
            f"{self._render_sequence(case.steps, depth=2)}"
            "</div>"
        )

    def _render_single_body(
        self,
        title: str,
        steps: tuple[ControlFlowStep, ...],
        *,
        depth: int,
        css_class: str = "ns-loop",
    ) -> str:
        return (
            f'<div class="ns-node {css_class}">'
            f"{self._render_header(title)}"
            f"{self._render_sequence(steps, depth=depth + 1)}"
            "</div>"
        )

    def _render_header(self, title: str) -> str:
        escaped = escape(title)
        return f'<div class="ns-header" aria-label="{escaped}">{escaped}</div>'

    def _render_footer(self, title: str) -> str:
        escaped = escape(title)
        return f'<div class="ns-footer" aria-label="{escaped}">{escaped}</div>'

    def _render_case_title(self, label: str) -> str:
        text = self._normalize_case_label(label.strip())
        escaped = escape(text)
        return f'<div class="case-title" aria-label="{escaped}">{escaped}</div>'

    def _normalize_case_label(self, label: str) -> str:
        compact = label.removesuffix(":").strip()
        if compact.startswith("default"):
            return "default"
        if compact.startswith("case "):
            return compact
        return compact
