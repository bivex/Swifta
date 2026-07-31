"""Filesystem implementation of source discovery and loading."""

from __future__ import annotations

import os
from pathlib import Path

from swifta.domain.errors import InputValidationError, SourceAccessError
from swifta.domain.model import SourceUnit, SourceUnitId
from swifta.domain.ports import SourceRepository

class FileSystemSourceRepository(SourceRepository):
    def load_file(self, path: str) -> SourceUnit:
        source_path = Path(path).expanduser().resolve()
        if not source_path.exists():
            raise InputValidationError(f"source file does not exist: {source_path}")
        if not source_path.is_file():
            raise InputValidationError(f"path is not a file: {source_path}")
        if source_path.suffix != ".swift":
            raise InputValidationError(f"expected a .swift file, got: {source_path}")

        return self._load_source_unit(source_path)

    def list_swift_sources(self, root_path: str) -> tuple[SourceUnit, ...]:
        root = Path(root_path).expanduser().resolve()
        if not root.exists():
            raise InputValidationError(f"source directory does not exist: {root}")
        if not root.is_dir():
            raise InputValidationError(f"path is not a directory: {root}")

        source_paths: list[Path] = []
        seen_resolved: set[Path] = set()

        for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
            for filename in filenames:
                if filename.endswith(".swift"):
                    file_path = Path(dirpath) / filename
                    if file_path.is_symlink():
                        try:
                            resolved = file_path.resolve(strict=True)
                        except (OSError, RuntimeError):
                            continue
                        if not resolved.is_file() or not resolved.is_relative_to(root):
                            continue
                    else:
                        resolved = file_path.resolve()

                    if resolved not in seen_resolved:
                        seen_resolved.add(resolved)
                        source_paths.append(file_path)

        source_paths.sort()
        if not source_paths:
            raise InputValidationError(f"no .swift files found under: {root}")

        return tuple(self._load_source_unit(path) for path in source_paths)

    def _load_source_unit(self, path: Path) -> SourceUnit:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            raise SourceAccessError(f"unable to read source file {path}: {error}") from error
        except UnicodeDecodeError as error:
            raise SourceAccessError(f"source file is not valid UTF-8 {path}: {error}") from error

        normalized = str(path)
        return SourceUnit(
            identifier=SourceUnitId(normalized),
            location=normalized,
            content=content,
        )

