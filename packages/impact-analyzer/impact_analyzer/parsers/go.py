"""Go language parser for Impact Analyzer.

Status: Planned — will use tree-sitter for parsing.
See: docs/implementation-plan.md Phase 1.6
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sage.audit.parsers.base import LanguageParser
from sage.audit.schema import ParseResult


class GoParser(LanguageParser):
    """Go language parser.

    Currently a placeholder. Implementation planned for Phase 1.6
    using tree-sitter-go grammar.
    """

    def language_name(self) -> str:
        return "go"

    def supported_extensions(self) -> list[str]:
        return [".go"]

    def grammar_version(self) -> str:
        return "tree-sitter-go (planned)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        raise NotImplementedError(
            "Go parser is planned for Phase 1.6. "
            "See docs/implementation-plan.md for details."
        )