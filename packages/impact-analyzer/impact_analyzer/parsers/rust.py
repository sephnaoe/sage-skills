"""Rust language parser for Impact Analyzer.

STUB: Not yet implemented. Will use tree-sitter for parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sage.audit.parsers.base import LanguageParser
from sage.audit.schema import ParseResult


class RustParser(LanguageParser):
    """Rust language parser (stub)."""

    def language_name(self) -> str:
        return "rust"

    def supported_extensions(self) -> list[str]:
        return [".rs"]

    def grammar_version(self) -> str:
        return "tree-sitter-rust-0.0.0 (not implemented)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        raise NotImplementedError("Rust parser not yet implemented. See implementation plan Phase 1.7.")