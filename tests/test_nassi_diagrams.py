import json
import subprocess
import sys
from pathlib import Path

from swifta.application.control_flow import BuildNassiDiagramCommand, NassiDiagramService
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
    assert "WHILE total &gt; 100" in document.html
    assert "SWITCH total" in document.html


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
