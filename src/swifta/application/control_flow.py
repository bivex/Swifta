"""Use cases for structured control flow diagrams."""

from __future__ import annotations

from dataclasses import dataclass

from swifta.domain.ports import NassiDiagramRenderer, SourceRepository, SwiftControlFlowExtractor


@dataclass(frozen=True, slots=True)
class BuildNassiDiagramCommand:
    path: str


@dataclass(frozen=True, slots=True)
class NassiDiagramDocumentDTO:
    source_location: str
    function_count: int
    function_names: tuple[str, ...]
    html: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_location": self.source_location,
            "function_count": self.function_count,
            "function_names": list(self.function_names),
        }


@dataclass(slots=True)
class NassiDiagramService:
    source_repository: SourceRepository
    extractor: SwiftControlFlowExtractor
    renderer: NassiDiagramRenderer

    def build_file_diagram(self, command: BuildNassiDiagramCommand) -> NassiDiagramDocumentDTO:
        source_unit = self.source_repository.load_file(command.path)
        diagram = self.extractor.extract(source_unit)
        return NassiDiagramDocumentDTO(
            source_location=diagram.source_location,
            function_count=len(diagram.functions),
            function_names=tuple(function.qualified_name for function in diagram.functions),
            html=self.renderer.render(diagram),
        )

