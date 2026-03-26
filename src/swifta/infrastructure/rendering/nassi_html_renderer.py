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
    def _depth_badge(self, i: int) -> str:
        if i == 0:
            return ""
        if i <= 20:
            return f" {chr(0x2460 + i - 1)}"
        if i <= 35:
            return f" {chr(0x3251 + i - 21)}"
        return f" {chr(0x32B1 + i - 36)}"

    def _depth_css(self) -> str:
        colors = ["blue", "green", "purple", "teal", "amber"]
        rules = []
        for i in range(51):
            c = colors[i % 5]
            rules.append(f"      .ns-if-depth-{i}-triangle {{ fill: var(--{c}-dim); stroke: var(--{c}); }}")
            rules.append(f"      .ns-if-depth-{i}-diagonal {{ stroke: var(--{c}); }}")
        return "\n".join(rules)

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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      :root {{
        /* Palette — Tokyo Night-inspired dark */
        --bg:          #13141f;
        --surface:     #1a1b2e;
        --surface-2:   #1f2335;
        --surface-3:   #24283b;
        --border:      #2e3354;
        --border-soft: #1e2240;
        --text:        #c0caf5;
        --text-bright: #e2e8ff;
        --muted:       #565f89;
        --shadow:      0 8px 32px rgba(0, 0, 0, 0.55);

        /* Accent colours */
        --blue:        #7aa2f7;
        --blue-dim:    #3d59a1;
        --green:       #9ece6a;
        --green-dim:   #1a3320;
        --red:         #f7768e;
        --red-dim:     #2d1420;
        --orange:      #ff9e64;
        --orange-dim:  #2d1e10;
        --teal:        #2ac3de;
        --teal-dim:    #0e2830;
        --purple:      #bb9af7;
        --purple-dim:  #201830;
        --amber:       #e0af68;
        --amber-dim:   #2a1e08;

        /* Block fills */
        --loop-fill:   #141d2e;
        --switch-fill: #0f1e20;
        --guard-fill:  #1e1508;
        --do-fill:     #16141e;
        --defer-fill:  #1e1a0a;
        --yes-fill:    #0f1e12;
        --no-fill:     #1e0f14;
        --action-fill: var(--surface-2);
        --note-fill:   #141622;

        /* Code font */
        --mono: "JetBrains Mono", "Fira Code", "Cascadia Code", "SF Mono", "Menlo", monospace;
        --ui:   "Inter", -apple-system, "Segoe UI", system-ui, sans-serif;
      }}
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{
        font-family: var(--ui);
        font-size: 14px;
        color: var(--text);
        background: var(--bg);
        padding: 24px;
        min-height: 100vh;
      }}
      /* ── Viewer shell ── */
      .viewer {{
        max-width: 1200px;
        margin: 0 auto;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--surface);
        box-shadow: var(--shadow);
        overflow: hidden;
      }}
      .titlebar {{
        padding: 10px 16px;
        background: var(--surface-3);
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 10px;
      }}
      .titlebar-icon {{
        width: 14px; height: 14px;
        border-radius: 50%;
        background: var(--blue-dim);
        border: 1px solid var(--blue);
        flex-shrink: 0;
      }}
      .titlebar-text {{
        font-size: 13px;
        font-weight: 600;
        color: var(--text-bright);
        letter-spacing: 0.02em;
      }}
      .toolbar {{
        padding: 8px 16px;
        border-bottom: 1px solid var(--border-soft);
        background: var(--surface);
        display: flex;
        flex-wrap: wrap;
        gap: 8px 14px;
        align-items: baseline;
      }}
      .toolbar-label {{
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--blue);
        background: rgba(122, 162, 247, 0.1);
        border: 1px solid rgba(122, 162, 247, 0.25);
        border-radius: 3px;
        padding: 2px 7px;
        white-space: nowrap;
      }}
      .toolbar-path {{
        font-family: var(--mono);
        font-size: 11.5px;
        color: var(--muted);
        overflow-wrap: anywhere;
      }}
      /* ── Viewer body ── */
      .viewer-body {{
        padding: 16px;
        background: var(--bg);
      }}
      /* ── Function panel ── */
      .function-panel {{
        margin-bottom: 16px;
        border: 1px solid var(--border);
        border-radius: 6px;
        overflow: hidden;
      }}
      .function-panel:last-child {{ margin-bottom: 0; }}
      .function-head {{
        padding: 10px 14px;
        background: var(--surface-3);
        border-bottom: 1px solid var(--border);
      }}
      .function-title {{
        font-size: 14px;
        font-weight: 600;
        color: var(--text-bright);
        line-height: 1.3;
      }}
      .function-signature {{
        margin-top: 3px;
        font-family: var(--mono);
        font-size: 11.5px;
        line-height: 1.5;
        color: var(--muted);
        overflow-wrap: anywhere;
        word-break: break-word;
      }}
      .function-body {{
        padding: 10px;
        background: var(--bg);
        overflow-x: auto;
      }}
      /* ── Node sequence ── */
      .ns-sequence {{
        display: flex;
        flex-direction: column;
      }}
      .ns-sequence > .ns-node + .ns-node,
      .ns-cases > .case + .case,
      .ns-catches > .ns-node + .ns-node {{
        margin-top: -1px;
      }}
      .ns-node {{
        min-width: 580px;
        border: 1px solid var(--border);
        border-radius: 3px;
        background: var(--action-fill);
      }}
      /* ── Block headers/footers ── */
      .ns-header,
      .ns-footer,
      .case-title {{
        padding: 6px 10px;
        background: var(--blue-dim);
        color: var(--blue);
        font-family: var(--mono);
        font-size: 12px;
        font-weight: 500;
        line-height: 1.4;
        border-bottom: 1px solid var(--border);
        overflow-wrap: anywhere;
        word-break: break-word;
      }}
      .ns-footer {{
        border-top: 1px solid var(--border);
        border-bottom: 0;
      }}
      /* ── Action label ── */
      .ns-label,
      .empty,
      .ns-note {{
        padding: 5px 10px;
        background: var(--action-fill);
      }}
      .action-text {{
        display: block;
        font-family: var(--mono);
        font-size: 12.5px;
        line-height: 1.6;
        color: var(--text);
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }}
      /* ── Block type colours ── */
      .ns-guard   {{ background: var(--guard-fill); }}
      .ns-loop,
      .ns-repeat  {{ background: var(--loop-fill); }}
      .ns-switch  {{ background: var(--switch-fill); }}
      .ns-do-catch {{ background: var(--do-fill); }}
      .ns-defer   {{ background: var(--defer-fill); }}

      .ns-guard   > .ns-header {{ background: var(--orange-dim); color: var(--orange); }}
      .ns-switch  > .ns-header,
      .case-title              {{ background: var(--teal-dim);   color: var(--teal);   }}
      .ns-do-catch > .ns-header {{ background: var(--purple-dim); color: var(--purple); }}
      .ns-defer   > .ns-header {{ background: var(--amber-dim);  color: var(--amber);  }}

      /* Left accent stripes */
      .ns-node.ns-loop,
      .ns-node.ns-repeat  {{ border-left: 3px solid var(--blue); }}
      .ns-node.ns-guard   {{ border-left: 3px solid var(--orange); }}
      .ns-node.ns-switch  {{ border-left: 3px solid var(--teal); }}
      .ns-node.ns-do-catch {{ border-left: 3px solid var(--purple); }}
      .ns-node.ns-defer   {{ border-left: 3px solid var(--amber); }}

      /* Depth tinting */
      .ns-depth-1 > .ns-node {{ background-color: rgba(255,255,255,0.012); }}
      .ns-depth-2 > .ns-node {{ background-color: rgba(255,255,255,0.020); }}
      .ns-depth-3 > .ns-node {{ background-color: rgba(255,255,255,0.028); }}

      /* ── If/else branches (classic NS diagram with SVG) ── */
      .ns-if-cap {{
        border-bottom: 1px solid var(--border);
        line-height: 0;
      }}
      .ns-if-svg {{
        display: block;
        width: 100%;
        height: auto;
        max-height: 80px;
      }}
      .ns-if-triangle {{
        fill: var(--blue-dim);
        stroke: var(--border);
        stroke-width: 1;
      }}
      .ns-if-diagonal {{
        stroke: var(--border);
        stroke-width: 1;
      }}
      .ns-if-condition-fo {{
        overflow: hidden;
      }}
      .ns-if-condition-text {{
        font-family: var(--mono);
        font-size: 12px;
        font-weight: 500;
        color: var(--text-bright);
        text-align: center;
        word-break: break-word;
        overflow-wrap: anywhere;
        line-height: 1.3;
        padding: 4px 8px;
      }}
      .ns-if-label-yes {{
        font-family: var(--mono);
        font-size: 11px;
        font-weight: 700;
        fill: var(--green);
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      .ns-if-label-no {{
        font-family: var(--mono);
        font-size: 11px;
        font-weight: 700;
        fill: var(--red);
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}

      /* Depth-coded if-cap triangles and diagonals (0-50, cycling blue→green→purple→teal→amber) */
{self._depth_css()}

      .ns-branches {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        background: var(--surface-2);
      }}
      .ns-branches-single {{ grid-template-columns: 1fr; }}
      .ns-branch {{
        min-width: 200px;
        border-left: 2px solid var(--border);
        background: var(--surface-2);
      }}
      .ns-branch:first-child {{ border-left: 0; }}
      .ns-branch-title {{
        padding: 5px 10px;
        border-bottom: 1px solid var(--border);
        background: var(--surface-3);
        color: var(--muted);
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      .ns-cases {{ background: var(--surface-2); }}
      .case {{ border-top: 1px solid var(--border); }}
      .case:first-child {{ border-top: 0; }}
      .ns-catches {{ border-top: 1px solid var(--border); }}

      .empty {{
        color: var(--muted);
        font-style: italic;
        font-size: 12px;
        background: var(--surface-3);
      }}
      .ns-note {{
        color: var(--muted);
        font-family: var(--mono);
        font-size: 11px;
        font-style: italic;
        background: var(--note-fill);
        border-top: 1px solid var(--border);
        padding: 5px 10px;
      }}
      .empty-file {{
        padding: 24px;
        color: var(--muted);
      }}

      @media (max-width: 800px) {{
        body {{ padding: 12px; }}
        .viewer-body {{ padding: 8px; }}
        .function-body {{ padding: 6px; }}
        .ns-node {{ min-width: 0; }}
        .ns-branches {{ grid-template-columns: 1fr; }}
        .ns-branch {{
          border-left: 0;
          border-top: 1px solid var(--border);
        }}
        .ns-branch:first-child {{ border-top: 0; }}
      }}
    </style>
  </head>
  <body>
    <div class="viewer">
      <div class="titlebar">
        <div class="titlebar-icon"></div>
        <span class="titlebar-text">Swifta · NSD Viewer</span>
      </div>
      <div class="toolbar">
        <span class="toolbar-label">Nassi-Shneiderman</span>
        <code class="toolbar-path">{escape(diagram.source_location)}</code>
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
                f"{self._render_if_cap(step.condition, depth=depth)}"
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

    def _render_if_cap(self, condition: str, *, depth: int = 0) -> str:
        escaped = escape(condition)
        d = min(depth, 50)
        badge = self._depth_badge(d)
        # SVG with foreignObject for proper text wrapping
        return (
            f'<div class="ns-if-cap ns-if-depth-{d}" aria-label="If {escaped}">'
            '<svg class="ns-if-svg" viewBox="0 0 400 80" preserveAspectRatio="xMidYMid meet">'
            f'<polygon points="0,0 400,0 200,50" class="ns-if-triangle ns-if-depth-{d}-triangle"/>'
            f'<foreignObject x="20" y="5" width="360" height="45" class="ns-if-condition-fo">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="ns-if-condition-text">{badge} {escaped}</div>'
            '</foreignObject>'
            f'<line x1="0" y1="50" x2="200" y2="80" class="ns-if-diagonal ns-if-depth-{d}-diagonal"/>'
            f'<line x1="400" y1="50" x2="200" y2="80" class="ns-if-diagonal ns-if-depth-{d}-diagonal"/>'
            f'<text x="100" y="72" text-anchor="middle" class="ns-if-label-yes">Yes</text>'
            f'<text x="300" y="72" text-anchor="middle" class="ns-if-label-no">No</text>'
            '</svg>'
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
