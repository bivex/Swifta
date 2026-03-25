"""CLI application."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from swifta.application.control_flow import BuildNassiDiagramCommand, NassiDiagramService
from swifta.application.dto import ParseDirectoryCommand, ParseFileCommand, ParsingJobReportDTO
from swifta.application.use_cases import ParsingJobService
from swifta.domain.errors import SwiftaError
from swifta.infrastructure.antlr.control_flow_extractor import AntlrSwiftControlFlowExtractor
from swifta.infrastructure.antlr.parser_adapter import AntlrSwiftSyntaxParser
from swifta.infrastructure.filesystem.source_repository import FileSystemSourceRepository
from swifta.infrastructure.rendering.nassi_html_renderer import HtmlNassiDiagramRenderer
from swifta.infrastructure.system import (
    InMemoryParsingJobRepository,
    StructuredLoggingEventPublisher,
    SystemClock,
    configure_logging,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    configure_logging(verbose=getattr(args, "verbose", False))

    try:
        if args.command == "parse-file":
            report = _build_parse_service().parse_file(ParseFileCommand(path=args.path))
        elif args.command == "parse-dir":
            report = _build_parse_service().parse_directory(ParseDirectoryCommand(root_path=args.path))
        elif args.command == "nassi-file":
            document = _build_nassi_service().build_file_diagram(
                BuildNassiDiagramCommand(path=args.path)
            )
            output_path = _resolve_output_path(args.path, args.out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(document.html, encoding="utf-8")

            payload = document.to_dict()
            payload["output_path"] = str(output_path)
            print(json.dumps(payload, indent=2))
            return 0
        else:
            parser.error(f"unsupported command: {args.command}")
    except SwiftaError as error:
        print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(report.to_dict(), indent=2))
    return _exit_code_for(report)


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse Swift source code with ANTLR.")
    parser.add_argument("--verbose", action="store_true", help="Enable lifecycle logging.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_file = subparsers.add_parser("parse-file", help="Parse one Swift file.")
    parse_file.add_argument("path", help="Path to a .swift file.")

    parse_dir = subparsers.add_parser("parse-dir", help="Parse all Swift files in a directory.")
    parse_dir.add_argument("path", help="Path to a directory.")

    nassi_file = subparsers.add_parser(
        "nassi-file",
        help="Build a Nassi-Shneiderman HTML diagram for one Swift file.",
    )
    nassi_file.add_argument("path", help="Path to a .swift file.")
    nassi_file.add_argument(
        "--out",
        help="Output HTML path. Defaults to <input>.nassi.html.",
    )
    return parser


def _build_parse_service() -> ParsingJobService:
    return ParsingJobService(
        source_repository=FileSystemSourceRepository(),
        parser=AntlrSwiftSyntaxParser(),
        event_publisher=StructuredLoggingEventPublisher(),
        clock=SystemClock(),
        job_repository=InMemoryParsingJobRepository(),
    )


def _build_nassi_service() -> NassiDiagramService:
    return NassiDiagramService(
        source_repository=FileSystemSourceRepository(),
        extractor=AntlrSwiftControlFlowExtractor(),
        renderer=HtmlNassiDiagramRenderer(),
    )


def _exit_code_for(report: ParsingJobReportDTO) -> int:
    if report.summary.technical_failure_count > 0:
        return 1
    return 0


def _resolve_output_path(input_path: str, explicit_output_path: str | None) -> Path:
    if explicit_output_path:
        return Path(explicit_output_path).expanduser().resolve()

    resolved_input = Path(input_path).expanduser().resolve()
    return resolved_input.with_suffix(".nassi.html")


if __name__ == "__main__":
    raise SystemExit(main())
