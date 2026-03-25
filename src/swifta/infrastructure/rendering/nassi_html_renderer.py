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
            sections = '<section class="function-panel"><p class="empty-file">No functions found.</p></section>'

        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Nassi-Shneiderman Control Flow</title>
    <style>
      :root {{
        --line: #20354d;
        --line-soft: #58718f;
        --page: #b5bec8;
        --window: #ece7d7;
        --panel: #f7f2e4;
        --panel-2: #fffdf8;
        --text: #0f1825;
        --muted: #536273;
        --shadow: 0 20px 46px rgba(19, 34, 52, 0.24);
        --banner: #1778df;
        --banner-dark: #0b58b0;
        --banner-light: #dcecff;
        --loop-fill: #edf5ff;
        --switch-fill: #eef8f3;
        --guard-fill: #fff1e7;
        --do-fill: #efeff2;
        --defer-fill: #f6efdf;
        --yes-fill: #d8f1c9;
        --no-fill: #ffd7dc;
        --action-fill: #ffffff;
        --note-fill: #eef3f8;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        padding: 24px;
        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(255, 255, 255, 0.7), transparent 24%),
          linear-gradient(180deg, #d8dfe6 0%, var(--page) 100%);
      }}
      .viewer {{
        max-width: 1180px;
        margin: 0 auto;
        border: 2px solid var(--line);
        background: var(--window);
        box-shadow: var(--shadow);
      }}
      .titlebar {{
        padding: 8px 14px;
        color: #ffffff;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.01em;
        background: linear-gradient(180deg, #3394ff 0%, var(--banner) 48%, var(--banner-dark) 100%);
        text-shadow: 0 1px 0 rgba(0, 0, 0, 0.28);
      }}
      .toolbar {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px 16px;
        align-items: center;
        padding: 8px 14px;
        border-top: 1px solid rgba(255, 255, 255, 0.35);
        border-bottom: 2px solid var(--line-soft);
        background: linear-gradient(180deg, #f9f4e7 0%, #eadfc4 100%);
      }}
      .toolbar-label {{
        padding: 3px 8px;
        border: 1px solid #94adc9;
        background: var(--banner-light);
        color: #234464;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      .toolbar-path {{
        margin: 0;
        color: var(--muted);
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 12px;
        overflow-wrap: anywhere;
      }}
      .viewer-body {{
        padding: 16px;
        background:
          linear-gradient(180deg, #dce3ea 0%, #e7ebf0 100%);
      }}
      .function-panel {{
        margin-bottom: 18px;
        border: 2px solid var(--line);
        background: var(--panel-2);
      }}
      .function-panel:last-child {{
        margin-bottom: 0;
      }}
      .function-head {{
        padding: 8px 12px;
        border-bottom: 2px solid var(--line);
        background: linear-gradient(180deg, #fcf8ee 0%, #ece2ca 100%);
      }}
      .function-title {{
        margin: 0;
        font-size: 17px;
        line-height: 1.2;
      }}
      .function-signature {{
        margin-top: 4px;
        color: var(--muted);
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 12px;
      }}
      .function-body {{
        padding: 10px;
        background: linear-gradient(180deg, #f9f5ea 0%, var(--panel) 100%);
        overflow-x: auto;
      }}
      .ns-sequence {{
        display: flex;
        flex-direction: column;
        gap: 0;
      }}
      .ns-sequence > .ns-node + .ns-node,
      .ns-cases > .case + .case,
      .ns-catches > .ns-node + .ns-node {{
        margin-top: -1px;
      }}
      .ns-node {{
        min-width: 620px;
        overflow: hidden;
        border: 1px solid var(--line);
        background: var(--action-fill);
      }}
      .ns-header,
      .ns-footer,
      .case-title {{
        padding: 7px 10px;
        background: linear-gradient(180deg, var(--banner) 0%, var(--banner-dark) 100%);
        color: #ffffff;
        font-size: 13px;
        font-weight: 700;
        line-height: 1.3;
        border-bottom: 1px solid var(--line);
        overflow-wrap: anywhere;
      }}
      .ns-footer {{
        border-top: 1px solid var(--line);
        border-bottom: 0;
      }}
      .ns-label,
      .empty,
      .ns-note {{
        padding: 6px 10px;
        border-top: 0;
        background: var(--action-fill);
      }}
      .action-text {{
        display: block;
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 12px;
        line-height: 1.45;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }}
      .ns-action {{
        background: var(--action-fill);
      }}
      .ns-if {{
        background: var(--action-fill);
      }}
      .ns-guard {{
        background: var(--guard-fill);
      }}
      .ns-loop {{
        background: var(--loop-fill);
      }}
      .ns-repeat {{
        background: var(--loop-fill);
      }}
      .ns-switch {{
        background: var(--switch-fill);
      }}
      .ns-do-catch {{
        background: var(--do-fill);
      }}
      .ns-defer {{
        background: var(--defer-fill);
      }}
      .ns-guard > .ns-header {{
        background: linear-gradient(180deg, #e58b52 0%, #c95d27 100%);
      }}
      .ns-switch > .ns-header,
      .case-title {{
        background: linear-gradient(180deg, #3f8f7d 0%, #266452 100%);
      }}
      .ns-do-catch > .ns-header {{
        background: linear-gradient(180deg, #8f98a6 0%, #5f6874 100%);
      }}
      .ns-defer > .ns-header {{
        background: linear-gradient(180deg, #bc9a5b 0%, #8a6b35 100%);
      }}
      .ns-branches {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        background: #ffffff;
      }}
      .ns-branches-single {{
        grid-template-columns: 1fr;
      }}
      .ns-branch {{
        min-width: 0;
        border-left: 1px solid var(--line);
        background: #ffffff;
      }}
      .ns-branch:first-child {{
        border-left: 0;
      }}
      .ns-branch-title {{
        padding: 6px 10px;
        border-bottom: 1px solid var(--line);
        background: #edf2f7;
        color: #37506b;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      .ns-cases {{
        background: #ffffff;
      }}
      .case {{
        border-top: 1px solid var(--line);
      }}
      .case:first-child {{
        border-top: 0;
      }}
      .ns-catches {{
        border-top: 1px solid var(--line);
      }}
      .empty {{
        color: var(--muted);
        font-style: italic;
        background: #f9fbfd;
      }}
      .ns-note {{
        color: #45607a;
        font-size: 12px;
        font-style: italic;
        background: var(--note-fill);
        border-top: 1px solid var(--line);
      }}
      .ns-if-cap {{
        position: relative;
        min-height: 66px;
        border-bottom: 1px solid var(--line);
        background:
          linear-gradient(
            168deg,
            var(--yes-fill) 0%,
            var(--yes-fill) 48.8%,
            var(--line) 49%,
            var(--line) 50%,
            var(--no-fill) 50.2%,
            var(--no-fill) 100%
          );
      }}
      .ns-if-cap::before {{
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        left: 0;
        height: 24px;
        background: linear-gradient(180deg, var(--banner) 0%, var(--banner-dark) 100%);
        border-bottom: 1px solid rgba(255, 255, 255, 0.25);
      }}
      .ns-if-condition {{
        position: absolute;
        top: 28px;
        right: 14px;
        left: 14px;
        color: var(--text);
        text-align: center;
        font-size: 13px;
        font-weight: 700;
        line-height: 1.25;
      }}
      .ns-if-yes,
      .ns-if-no {{
        position: absolute;
        bottom: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }}
      .ns-if-yes {{
        left: 10px;
        color: #2c6a1c;
      }}
      .ns-if-no {{
        right: 10px;
        color: #a53a4b;
      }}
      .empty-file {{
        margin: 0;
        padding: 24px;
      }}
      @media (max-width: 800px) {{
        body {{ padding: 16px; }}
        .viewer-body {{ padding: 10px; }}
        .function-body {{ padding: 8px; }}
        .ns-node {{ min-width: 0; }}
        .ns-branches {{ grid-template-columns: 1fr; }}
        .ns-branch {{
          border-left: 0;
          border-top: 1px solid var(--line);
        }}
        .ns-branch:first-child {{
          border-top: 0;
        }}
        .ns-if-cap {{
          min-height: 72px;
        }}
        .ns-if-condition {{
          right: 10px;
          left: 10px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="viewer">
      <div class="titlebar">Swifta NSD Viewer</div>
      <div class="toolbar">
        <div class="toolbar-label">Nassi-Shneiderman Control Flow</div>
        <div class="toolbar-path">{escape(diagram.source_location)}</div>
      </div>
      <main class="viewer-body">{sections}</main>
    </div>
  </body>
</html>
"""

    def _render_function(self, function) -> str:
        return (
            '<section class="function-panel">'
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
                    '<div class="ns-branch" aria-label="Else branch">'
                    f"{self._render_sequence(step.else_steps, depth=depth + 1)}"
                    "</div>"
                )
                branches_class = "ns-branches"
                trailing_note = ""
            else:
                else_markup = ""
                branches_class = "ns-branches ns-branches-single"
                trailing_note = '<div class="ns-note">No branch continues after the decision.</div>'

            return (
                '<div class="ns-node ns-if">'
                f"{self._render_if_cap(step.condition)}"
                f'<div class="{branches_class}">'
                '<div class="ns-branch" aria-label="Then branch">'
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

    def _render_if_cap(self, condition: str) -> str:
        escaped = escape(condition)
        return (
            f'<div class="ns-if-cap" aria-label="If {escaped}">'
            f'<div class="ns-if-condition">{escaped}</div>'
            '<div class="ns-if-yes">Yes</div>'
            '<div class="ns-if-no">No</div>'
            "</div>"
        )

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
