"""Go language parser for Impact Analyzer.

STUB: Not yet implemented. Will use tree-sitter for parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sage.audit.parsers.base import LanguageParser
from sage.audit.schema import ParseResult


class GoParser(LanguageParser):
    """Go language parser (stub)."""

    def language_name(self) -> str:
        return "go"

    def supported_extensions(self) -> list[str]:
        return [".go"]

    def grammar_version(self) -> str:
        return "tree-sitter-go-0.0.0 (not implemented)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        raise NotImplementedError("Go parser not yet implemented. See implementation plan Phase 1.6.")