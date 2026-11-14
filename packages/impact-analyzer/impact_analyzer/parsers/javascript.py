"""JavaScript/TypeScript language parser for Impact Analyzer.

STUB: Not yet implemented. Will use tree-sitter for parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sage.audit.parsers.base import LanguageParser
from sage.audit.schema import ParseResult


class JavaScriptParser(LanguageParser):
    """JavaScript/TypeScript language parser (stub)."""

    def language_name(self) -> str:
        return "javascript"

    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    def grammar_version(self) -> str:
        return "tree-sitter-javascript-0.0.0 (not implemented)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        raise NotImplementedError("JavaScript parser not yet implemented. See implementation plan Phase 1.5.")