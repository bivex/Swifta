import json
import subprocess
import sys
from pathlib import Path

from swifta.application.dto import ParseDirectoryCommand, ParseFileCommand
from swifta.application.use_cases import ParsingJobService
from swifta.infrastructure.antlr.parser_adapter import AntlrSwiftSyntaxParser
from swifta.infrastructure.filesystem.source_repository import FileSystemSourceRepository
from swifta.infrastructure.system import (
    InMemoryParsingJobRepository,
    StructuredLoggingEventPublisher,
    SystemClock,
)


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


def _build_service() -> ParsingJobService:
    _ensure_generated_parser()
    return ParsingJobService(
        source_repository=FileSystemSourceRepository(),
        parser=AntlrSwiftSyntaxParser(),
        event_publisher=StructuredLoggingEventPublisher(),
        clock=SystemClock(),
        job_repository=InMemoryParsingJobRepository(),
    )


def test_parse_file_extracts_structure() -> None:
    service = _build_service()
    report = service.parse_file(ParseFileCommand(path=str(ROOT / "tests" / "fixtures" / "valid.swift")))

    assert report.summary.source_count == 1
    assert report.summary.technical_failure_count == 0
    assert report.sources[0].status in {"succeeded", "succeeded_with_diagnostics"}
    assert {element.kind for element in report.sources[0].structural_elements} >= {
        "import",
        "struct",
        "function",
        "extension",
    }


def test_parse_directory_returns_report_for_all_files() -> None:
    service = _build_service()
    report = service.parse_directory(ParseDirectoryCommand(root_path=str(ROOT / "tests" / "fixtures")))

    assert report.summary.source_count == 3
    assert len(report.sources) == 3


def test_parse_file_handles_enum_declaration(tmp_path: Path) -> None:
    service = _build_service()
    source_path = tmp_path / "enum_parse.swift"
    source_path.write_text(
        """
enum Mode {
    case active

    func title() -> String {
        return "active"
    }
}
""".strip(),
        encoding="utf-8",
    )

    report = service.parse_file(ParseFileCommand(path=str(source_path)))

    assert report.summary.source_count == 1
    assert report.summary.technical_failure_count == 0
    assert {element.kind for element in report.sources[0].structural_elements} >= {"enum", "function"}


def test_cli_outputs_json() -> None:
    _ensure_generated_parser()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swifta.presentation.cli.main",
            "parse-file",
            str(ROOT / "tests" / "fixtures" / "valid.swift"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["source_count"] == 1


def test_parse_file_times_out_gracefully(tmp_path: Path, monkeypatch) -> None:
    import time
    from swifta.domain.model import SourceUnit, SourceUnitId
    from swifta.infrastructure.antlr import parser_adapter

    parser = AntlrSwiftSyntaxParser(default_timeout_seconds=0.05)
    source_unit = SourceUnit(
        identifier=SourceUnitId("slow.swift"),
        location=str(tmp_path / "slow.swift"),
        content="""
actor Manager {
    init() {}
    deinit {}
    subscript(i: Int) -> String { "a" }
}
""".strip(),
    )

    # Mock parse_source_text to simulate a hanging parser execution
    def _mock_slow_parse(*args, **kwargs):
        time.sleep(0.2)
        raise RuntimeError("Should have timed out")

    monkeypatch.setattr(parser_adapter, "parse_source_text", _mock_slow_parse)

    outcome = parser.parse(source_unit, timeout_seconds=0.05)
    assert outcome.status.value == "succeeded_with_diagnostics"
    assert len(outcome.structural_elements) == 4
    names = [e.name for e in outcome.structural_elements]
    assert names == ["Manager", "init", "deinit", "subscript"]
    assert outcome.structural_elements[1].signature == "init()"
    assert outcome.structural_elements[3].signature == "subscript(i: Int) -> String"
    assert outcome.statistics.token_count > 0
    assert "lightweight" in outcome.diagnostics[0].message.lower()


def test_signature_collection_does_not_runaway_on_closing_brace(tmp_path: Path, monkeypatch) -> None:
    from swifta.domain.model import SourceUnit, SourceUnitId
    from swifta.infrastructure.antlr import parser_adapter

    parser = AntlrSwiftSyntaxParser(default_timeout_seconds=0.05)
    source_unit = SourceUnit(
        identifier=SourceUnitId("runaway.swift"),
        location=str(tmp_path / "runaway.swift"),
        content="""
struct Model {
    init?(rawValue: String) }
    var focusedPanel: String?
    let tour = "test"
}
""".strip(),
    )

    def _mock_slow_parse(*args, **kwargs):
        raise RuntimeError("Force fallback")

    monkeypatch.setattr(parser_adapter, "parse_source_text", _mock_slow_parse)

    outcome = parser.parse(source_unit, timeout_seconds=0.05)
    init_elem = next(e for e in outcome.structural_elements if e.name == "init")
    assert init_elem.signature == "init?(rawValue: String)"
    assert "focusedPanel" not in init_elem.signature


def test_cli_supports_timeout_flag() -> None:
    _ensure_generated_parser()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swifta.presentation.cli.main",
            "parse-file",
            "--timeout",
            "5.0",
            str(ROOT / "tests" / "fixtures" / "valid.swift"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["source_count"] == 1


def test_symlink_directory_loops_and_escaping_are_ignored(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    valid_file = repo_dir / "valid.swift"
    valid_file.write_text("struct Valid {}", encoding="utf-8")

    # Directory symlink loop
    loop_symlink = repo_dir / "loop_link"
    loop_symlink.symlink_to(repo_dir, target_is_directory=True)

    # Outside file symlink
    outside_file = tmp_path / "outside.swift"
    outside_file.write_text("struct Outside {}", encoding="utf-8")
    outside_link = repo_dir / "outside_link.swift"
    outside_link.symlink_to(outside_file)

    repo = FileSystemSourceRepository()
    sources = repo.list_swift_sources(str(repo_dir))

    assert len(sources) == 1
    assert sources[0].location == str(valid_file.resolve())


def test_nassi_extractor_handles_deep_recursion_without_crashing(tmp_path: Path) -> None:
    from swifta.application.control_flow import BuildNassiDiagramCommand, NassiDiagramService
    from swifta.infrastructure.antlr.control_flow_extractor import AntlrSwiftControlFlowExtractor
    from swifta.infrastructure.rendering.nassi_html_renderer import HtmlNassiDiagramRenderer

    # Generate deeply nested code
    nested_code = "func deep() {\n" + "autoreleasepool {\n" * 50 + "print(1)\n" + "}\n" * 50 + "}\n"
    file_path = tmp_path / "deep.swift"
    file_path.write_text(nested_code, encoding="utf-8")

    service = NassiDiagramService(
        source_repository=FileSystemSourceRepository(),
        extractor=AntlrSwiftControlFlowExtractor(),
        renderer=HtmlNassiDiagramRenderer(),
    )
    document = service.build_file_diagram(BuildNassiDiagramCommand(path=str(file_path)))
    assert document.source_location == str(file_path.resolve())


def test_cli_handles_os_error_without_traceback(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.swift"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swifta.presentation.cli.main",
            "parse-file",
            str(non_existent),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert "error" in payload
    assert "Traceback" not in result.stderr


