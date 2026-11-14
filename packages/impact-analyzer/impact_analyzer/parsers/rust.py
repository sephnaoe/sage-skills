"""Rust language parser for Impact Analyzer.

Status: Planned — will use tree-sitter for parsing.
See: docs/implementation-plan.md Phase 1.7
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sage.audit.parsers.base import LanguageParser
from sage.audit.schema import ParseResult


class RustParser(LanguageParser):
    """Rust language parser.

    Currently a placeholder. Implementation planned for Phase 1.7
    using tree-sitter-rust grammar.
    """

    def language_name(self) -> str:
        return "rust"

    def supported_extensions(self) -> list[str]:
        return [".rs"]

    def grammar_version(self) -> str:
        return "tree-sitter-rust (planned)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        raise NotImplementedError(
            "Rust parser is planned for Phase 1.7. "
            "See docs/implementation-plan.md for details."
        )