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
        function_count = len(diagram.functions)

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
        --paper: #fffdf8;
        --canvas: #f4eee1;
        --card: rgba(255, 255, 255, 0.88);
        --soft: #eee1ca;
        --soft-2: #f7f1e5;
        --muted: #6a5f53;
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
        --shadow: 0 18px 44px rgba(23, 52, 74, 0.12);
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
        max-width: 1280px;
        margin: 0 auto;
      }}
      .hero {{
        display: flex;
        justify-content: space-between;
        gap: 20px;
        align-items: flex-end;
        margin-bottom: 28px;
        padding: 28px 30px;
        border: 3px solid var(--line);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(250, 243, 229, 0.88));
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
      .hero p {{
        margin: 0;
        overflow-wrap: anywhere;
      }}
      .hero-path {{
        max-width: 760px;
        color: var(--muted);
      }}
      .hero-stats {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }}
      .hero-pill {{
        min-width: 120px;
        padding: 12px 14px;
        border: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.82);
      }}
      .hero-pill strong {{
        display: block;
        font-size: 22px;
        line-height: 1;
      }}
      .hero-pill span {{
        display: block;
        margin-top: 4px;
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
      }}
      .legend {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 0 0 24px;
      }}
      .legend-pill {{
        padding: 9px 12px;
        border: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.72);
        font-size: 13px;
        font-weight: 700;
      }}
      .legend-pill.if {{ background: var(--if-bg); border-color: var(--if-line); }}
      .legend-pill.loop {{ background: var(--loop-bg); border-color: var(--loop-line); }}
      .legend-pill.switch {{ background: var(--switch-bg); border-color: var(--switch-line); }}
      .legend-pill.guard {{ background: var(--guard-bg); border-color: var(--guard-line); }}
      .legend-pill.flow {{ background: var(--do-bg); border-color: var(--do-line); }}
      .function-card {{
        margin-bottom: 32px;
        border: 3px solid var(--line);
        background: var(--card);
        box-shadow: var(--shadow);
      }}
      .function-head {{
        padding: 18px 20px 12px;
        border-bottom: 3px solid var(--line);
        background: linear-gradient(180deg, var(--soft) 0%, #f6efe2 100%);
      }}
      .function-badge {{
        display: inline-block;
        margin-bottom: 10px;
        padding: 5px 9px;
        border: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.85);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        font-weight: 800;
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
      .ns-header, .ns-footer, .ns-label, .case-title {{
        display: flex;
        gap: 10px;
        align-items: center;
        padding: 10px 14px;
        border-bottom: 2px solid var(--line);
        background: var(--soft-2);
      }}
      .ns-footer {{
        border-top: 2px solid var(--line);
        border-bottom: 0;
      }}
      .node-tag {{
        flex: 0 0 auto;
        padding: 4px 8px;
        border: 2px solid currentColor;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 11px;
        line-height: 1;
        font-weight: 800;
      }}
      .node-text {{
        min-width: 0;
        font-weight: 700;
        overflow-wrap: anywhere;
      }}
      .ns-label {{
        background: var(--action-bg);
        border-bottom: 0;
        align-items: flex-start;
      }}
      .action-text {{
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
      .ns-action .node-tag {{
        color: #7f6a4a;
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
        background: rgba(255, 255, 255, 0.58);
      }}
      .ns-branch:first-child {{
        border-left: 0;
      }}
      .ns-branch-title {{
        padding: 9px 12px;
        border-bottom: 2px solid var(--line);
        background: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 12px;
        font-weight: 700;
      }}
      .ns-cases {{
        background: rgba(255, 255, 255, 0.55);
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
        background: rgba(255, 255, 255, 0.72);
      }}
      .empty {{
        padding: 12px 14px;
        color: var(--muted);
        font-style: italic;
        background: rgba(255, 255, 255, 0.6);
      }}
      .empty-file {{
        margin: 0;
        padding: 24px;
      }}
      @media (max-width: 800px) {{
        body {{ padding: 16px; }}
        .hero {{ padding: 20px; }}
        .hero,
        .hero-stats {{ flex-direction: column; align-items: stretch; }}
        .ns-branches {{ grid-template-columns: 1fr; }}
        .ns-branch {{ border-left: 0; border-top: 2px solid var(--line); }}
        .ns-branch:first-child {{ border-top: 0; }}
        .function-body {{ padding: 12px; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <div>
          <p class="eyebrow">Structured Control Flow</p>
          <h1>Nassi-Shneiderman Control Flow</h1>
          <p class="hero-path">{escape(diagram.source_location)}</p>
        </div>
        <div class="hero-stats">
          <div class="hero-pill">
            <strong>{function_count}</strong>
            <span>Functions</span>
          </div>
          <div class="hero-pill">
            <strong>HTML</strong>
            <span>Diagram Output</span>
          </div>
        </div>
      </section>
      <section class="legend">
        <div class="legend-pill if">Decisions</div>
        <div class="legend-pill loop">Loops</div>
        <div class="legend-pill switch">Switch Cases</div>
        <div class="legend-pill guard">Exit Guards</div>
        <div class="legend-pill flow">Flow Blocks</div>
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
            '<div class="function-badge">Function</div>'
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
                '<div class="ns-label">'
                '<span class="node-tag">Action</span>'
                f'<code class="action-text">{escape(step.label)}</code>'
                "</div>"
                "</div>"
            )
        if isinstance(step, IfFlowStep):
            return (
                '<div class="ns-node ns-if">'
                f"{self._render_header('If', step.condition)}"
                '<div class="ns-branches">'
                '<div class="ns-branch"><div class="ns-branch-title">Then path</div>'
                f"{self._render_sequence(step.then_steps, depth=depth + 1)}"
                "</div>"
                '<div class="ns-branch"><div class="ns-branch-title">Else path</div>'
                f"{self._render_sequence(step.else_steps, depth=depth + 1)}"
                "</div>"
                "</div>"
                "</div>"
            )
        if isinstance(step, GuardFlowStep):
            return (
                '<div class="ns-node ns-guard">'
                f"{self._render_header('Guard', step.condition)}"
                '<div class="ns-branch"><div class="ns-branch-title">Failure / exit</div>'
                f"{self._render_sequence(step.else_steps, depth=depth + 1)}"
                "</div>"
                "</div>"
            )
        if isinstance(step, WhileFlowStep):
            return self._render_single_body("While", step.condition, step.body_steps, depth=depth)
        if isinstance(step, ForInFlowStep):
            return self._render_single_body("For", step.header, step.body_steps, depth=depth)
        if isinstance(step, RepeatWhileFlowStep):
            return (
                '<div class="ns-node ns-repeat">'
                f"{self._render_header('Repeat', '')}"
                f"{self._render_sequence(step.body_steps, depth=depth + 1)}"
                f"{self._render_footer('While', step.condition)}"
                "</div>"
            )
        if isinstance(step, SwitchFlowStep):
            cases = "".join(self._render_case(case) for case in step.cases)
            cases_markup = cases or '<div class="empty">No cases.</div>'
            return (
                '<div class="ns-node ns-switch">'
                f"{self._render_header('Switch', step.expression)}"
                f'<div class="ns-cases">{cases_markup}</div>'
                "</div>"
            )
        if isinstance(step, DoCatchFlowStep):
            catches = "".join(
                self._render_single_body("Catch", catch.pattern, catch.steps, depth=depth + 1)
                for catch in step.catches
            )
            return (
                '<div class="ns-node ns-do-catch">'
                f"{self._render_header('Do', '')}"
                f"{self._render_sequence(step.body_steps, depth=depth + 1)}"
                f'<div class="ns-catches">{catches}</div>'
                "</div>"
            )
        if isinstance(step, DeferFlowStep):
            return self._render_single_body("Defer", "", step.body_steps, depth=depth, css_class="ns-defer")
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
        keyword: str,
        label: str,
        steps: tuple[ControlFlowStep, ...],
        *,
        depth: int,
        css_class: str = "ns-loop",
    ) -> str:
        return (
            f'<div class="ns-node {css_class}">'
            f"{self._render_header(keyword, label)}"
            f"{self._render_sequence(steps, depth=depth + 1)}"
            "</div>"
        )

    def _render_header(self, keyword: str, label: str) -> str:
        text = escape(label) if label else "Structured block"
        aria_label = escape(f"{keyword.upper()} {label}".strip() or keyword.upper())
        return (
            f'<div class="ns-header" aria-label="{aria_label}">'
            f'<span class="node-tag">{escape(keyword)}</span>'
            f'<span class="node-text">{text}</span>'
            "</div>"
        )

    def _render_footer(self, keyword: str, label: str) -> str:
        aria_label = escape(f"{keyword.upper()} {label}".strip() or keyword.upper())
        return (
            f'<div class="ns-footer" aria-label="{aria_label}">'
            f'<span class="node-tag">{escape(keyword)}</span>'
            f'<span class="node-text">{escape(label)}</span>'
            "</div>"
        )

    def _render_case_title(self, label: str) -> str:
        normalized = label.strip()
        if normalized.startswith("default"):
            keyword = "Default"
            text = normalized
        else:
            keyword = "Case"
            text = normalized
        aria_label = escape(f"{keyword.upper()} {text}".strip())
        return (
            f'<div class="case-title" aria-label="{aria_label}">'
            f'<span class="node-tag">{escape(keyword)}</span>'
            f'<span class="node-text">{escape(text)}</span>'
            "</div>"
        )
