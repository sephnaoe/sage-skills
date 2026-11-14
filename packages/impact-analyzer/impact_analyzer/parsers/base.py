"""LanguageParser interface — abstract base for all language parsers.

All parsers produce the same normalized output schema (schema.py).
This ensures downstream consumers don't need language-specific code.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from impact_analyzer.schema import ParseResult, FileInfo


class LanguageParser(ABC):
    """Abstract base class for language-specific parsers."""

    @abstractmethod
    def parse(self, file_path: Path, content: str) -> ParseResult:
        """Parse a single file into normalized symbols and edges."""
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of file extensions this parser handles (e.g., ['.py', '.pyi'])."""
        ...

    @abstractmethod
    def language_name(self) -> str:
        """Return the language name (e.g., 'python', 'javascript')."""
        ...

    @abstractmethod
    def grammar_version(self) -> str:
        """Return the pinned grammar/parser version."""
        ...

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions()

    def file_hash(self, content: str) -> str:
        """Compute content hash for cache invalidation."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def make_file_info(self, file_path: Path, content: str, parse_time_ms: float = 0.0) -> FileInfo:
        """Create FileInfo from file path and content."""
        return FileInfo(
            path=str(file_path).replace("\\", "/"),
            language=self.language_name(),
            hash=self.file_hash(content),
            size_bytes=len(content.encode("utf-8")),
            parse_time_ms=parse_time_ms,
        )