import json
import subprocess
import sys
from pathlib import Path

from swifta.application.control_flow import (
    BuildNassiDiagramCommand,
    BuildNassiDirectoryCommand,
    NassiDiagramService,
)
from swifta.domain.control_flow import (
    ActionFlowStep,
    ForInFlowStep,
    GuardFlowStep,
    IfFlowStep,
)
from swifta.domain.model import SourceUnit, SourceUnitId
from swifta.infrastructure.antlr import control_flow_extractor as control_flow_module
from swifta.infrastructure.antlr.control_flow_extractor import AntlrSwiftControlFlowExtractor
from swifta.infrastructure.filesystem.source_repository import FileSystemSourceRepository
from swifta.infrastructure.rendering.nassi_html_renderer import HtmlNassiDiagramRenderer


ROOT = Path(__file__).resolve().parent.parent


def _ensure_generated_parser() -> None:
    generated_parser = (
        ROOT / "src" / "swifta" / "infrastructure" / "antlr" / "generated" / "swift5" / "Swift5Parser.py"
    )
    if generated_parser.exists():
        return
    subprocess.run(
        [sys.executable, "scripts/generate_swift_parser.py"],
        cwd=ROOT,
        check=True,
    )


def _build_service() -> NassiDiagramService:
    _ensure_generated_parser()
    return NassiDiagramService(
        source_repository=FileSystemSourceRepository(),
        extractor=AntlrSwiftControlFlowExtractor(),
        renderer=HtmlNassiDiagramRenderer(),
    )


def test_nassi_service_builds_html_document() -> None:
    service = _build_service()
    document = service.build_file_diagram(
        BuildNassiDiagramCommand(path=str(ROOT / "tests" / "fixtures" / "control_flow.swift"))
    )

    assert document.function_count == 2
    assert "score" in document.function_names
    assert "MathBox.normalize" in document.function_names
    assert "While total &gt; 100" in document.html
    assert "Switch total" in document.html
    assert "Swifta" in document.html


def test_nassi_service_builds_directory_bundle() -> None:
    service = _build_service()
    bundle = service.build_directory_diagrams(
        BuildNassiDirectoryCommand(root_path=str(ROOT / "tests" / "fixtures"))
    )

    assert bundle.document_count == 3
    assert bundle.root_path == str((ROOT / "tests" / "fixtures").resolve())
    assert any(document.source_location.endswith("control_flow.swift") for document in bundle.documents)
    assert any(document.function_count == 2 for document in bundle.documents)


def test_nassi_service_handles_enum_container(tmp_path: Path) -> None:
    service = _build_service()
    source_path = tmp_path / "enum_fixture.swift"
    source_path.write_text(
        """
enum Direction {
    case north

    func score() -> Int {
        return 1
    }
}
""".strip(),
        encoding="utf-8",
    )

    document = service.build_file_diagram(BuildNassiDiagramCommand(path=str(source_path)))

    assert document.function_count == 1
    assert document.function_names == ("Direction.score",)
    assert "Direction" in document.html


def test_control_flow_extractor_uses_function_body_fast_path(monkeypatch) -> None:
    _ensure_generated_parser()
    extractor = AntlrSwiftControlFlowExtractor()

    def _unexpected_full_parse(*args, **kwargs):
        raise AssertionError("unexpected full-file parse fallback")

    monkeypatch.setattr(control_flow_module, "parse_source_text", _unexpected_full_parse)

    source = SourceUnit(
        identifier=SourceUnitId("fast-path"),
        location="fast-path.swift",
        content="""
class AccessibilityHelper {
    private static var cachedWindows: (windows: [Int], timestamp: Date)?

    static func check(_ value: Int) -> Int {
        if value > 0 {
            return value
        }
        return 0
    }
}
""".strip(),
    )

    diagram = extractor.extract(source)

    assert len(diagram.functions) == 1
    assert diagram.functions[0].qualified_name == "AccessibilityHelper.check"
    assert len(diagram.functions[0].steps) == 2


def test_control_flow_extractor_shortcuts_action_only_bodies(monkeypatch) -> None:
    _ensure_generated_parser()
    extractor = AntlrSwiftControlFlowExtractor()

    def _unexpected_full_parse(*args, **kwargs):
        raise AssertionError("unexpected full-file parse fallback")

    def _unexpected_code_block_parse(*args, **kwargs):
        raise AssertionError("unexpected code-block parse for action-only function")

    monkeypatch.setattr(control_flow_module, "parse_source_text", _unexpected_full_parse)
    monkeypatch.setattr(control_flow_module, "parse_code_block_text", _unexpected_code_block_parse)

    source = SourceUnit(
        identifier=SourceUnitId("action-only"),
        location="action-only.swift",
        content="""
class MathBox {
    static func normalize(_ input: Int) -> Int {
        let clamped = max(input, 0)
        return clamped
    }
}
""".strip(),
    )

    diagram = extractor.extract(source)

    assert len(diagram.functions) == 1
    assert diagram.functions[0].qualified_name == "MathBox.normalize"
    assert [step.label for step in diagram.functions[0].steps] == [
        "let clamped = max(input, 0)",
        "return clamped",
    ]


def test_control_flow_extractor_unwraps_autoreleasepool_wrapper(monkeypatch) -> None:
    _ensure_generated_parser()
    extractor = AntlrSwiftControlFlowExtractor()

    def _unexpected_full_parse(*args, **kwargs):
        raise AssertionError("unexpected full-file parse fallback")

    monkeypatch.setattr(control_flow_module, "parse_source_text", _unexpected_full_parse)

    source = SourceUnit(
        identifier=SourceUnitId("autoreleasepool"),
        location="autoreleasepool.swift",
        content="""
class Worker {
    static func run(_ value: Int) -> Int {
        return autoreleasepool {
            if value > 0 {
                return value
            }
            return 0
        }
    }
}
""".strip(),
    )

    diagram = extractor.extract(source)

    assert len(diagram.functions) == 1
    assert diagram.functions[0].qualified_name == "Worker.run"
    assert diagram.functions[0].steps[0].__class__.__name__ == "IfFlowStep"


def test_nassi_cli_writes_html_file(tmp_path: Path) -> None:
    _ensure_generated_parser()
    output_path = tmp_path / "control_flow.html"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swifta.presentation.cli.main",
            "nassi-file",
            str(ROOT / "tests" / "fixtures" / "control_flow.swift"),
            "--out",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["function_count"] == 2
    assert payload["output_path"] == str(output_path.resolve())
    assert output_path.exists()
    assert "Nassi-Shneiderman Control Flow" in output_path.read_text(encoding="utf-8")


def test_nassi_dir_cli_writes_html_bundle(tmp_path: Path) -> None:
    _ensure_generated_parser()
    output_dir = tmp_path / "nassi-bundle"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swifta.presentation.cli.main",
            "nassi-dir",
            str(ROOT / "tests" / "fixtures"),
            "--out",
            str(output_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["document_count"] == 3
    assert payload["output_dir"] == str(output_dir.resolve())
    assert payload["index_path"] == str((output_dir / "index.html").resolve())
    assert len(payload["documents"]) == 3
    assert (output_dir / "index.html").exists()
    assert (output_dir / "control_flow.nassi.html").exists()
    assert (output_dir / "invalid.nassi.html").exists()
    assert "Swifta NSD Index" in (output_dir / "index.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Trailing closure expansion
# ---------------------------------------------------------------------------


def _extract_steps(swift_code: str):
    """Build a diagram from a Swift snippet and return the first function's steps."""
    _ensure_generated_parser()
    extractor = AntlrSwiftControlFlowExtractor()
    source = SourceUnit(
        identifier=SourceUnitId("trailing-closure"),
        location="trailing-closure.swift",
        content=swift_code.strip(),
    )
    diagram = extractor.extract(source)
    assert len(diagram.functions) >= 1, "expected at least one function"
    return diagram.functions[0].steps


class TestTrailingClosureExpansion:
    """Trailing closures should have their bodies expanded inline."""

    def test_map_with_if_and_return(self) -> None:
        steps = _extract_steps("""
class C {
    func f(windowFrames: [(Int, CGRect)]) {
        let corrections = windowFrames.map { (window, currentFrame) -> (Int, CGRect, Bool) in
            var corrected = currentFrame
            if corrected.minX < 0 { corrected.origin.x = 0 }
            return (window, corrected, true)
        }
    }
}
""")
        step_types = [type(s) for s in steps]
        assert ActionFlowStep not in step_types or len(steps) > 1, (
            "map trailing closure collapsed to a single action"
        )
        assert any(isinstance(s, IfFlowStep) for s in steps), (
            "expected an IfFlowStep from the closure body"
        )

    def test_foreach_with_if_and_for(self) -> None:
        steps = _extract_steps("""
class C {
    func f(items: [Int]) {
        items.forEach { item in
            if item > 0 { print(item) }
            for i in 0..<item { print(i) }
        }
    }
}
""")
        step_types = [type(s) for s in steps]
        assert any(isinstance(s, IfFlowStep) for s in steps), (
            "expected an IfFlowStep from forEach closure body"
        )
        assert any(isinstance(s, ForInFlowStep) for s in steps), (
            "expected a ForInFlowStep from forEach closure body"
        )

    def test_reduce_with_guard(self) -> None:
        steps = _extract_steps("""
class C {
    func f(values: [Double]) {
        let total = values.reduce(0.0) { sum, val in
            guard val > 0 else { return sum }
            return sum + val
        }
    }
}
""")
        assert any(isinstance(s, GuardFlowStep) for s in steps), (
            "expected a GuardFlowStep from reduce closure body"
        )

    def test_chained_filter_map_expands_last_closure(self) -> None:
        steps = _extract_steps("""
class C {
    func f(items: [Int]) {
        let result = items.filter { $0 > 0 }.map { item in
            if item > 10 { return item * 2 }
            return item
        }
    }
}
""")
        assert any(isinstance(s, IfFlowStep) for s in steps), (
            "expected an IfFlowStep from chained .map trailing closure"
        )

    def test_return_before_trailing_closure(self) -> None:
        steps = _extract_steps("""
class C {
    func f(items: [Int]) {
        return items.map { item in
            if item > 0 { return item }
            return 0
        }
    }
}
""")
        assert any(isinstance(s, IfFlowStep) for s in steps), (
            "expected an IfFlowStep when return precedes trailing closure"
        )
