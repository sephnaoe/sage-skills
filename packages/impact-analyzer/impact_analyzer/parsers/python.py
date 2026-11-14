"""Python language parser for Impact Analyzer.

Uses regex-based import extraction (fast, deterministic).
Future: tree-sitter for more accurate parsing.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from impact_analyzer.parsers.base import LanguageParser
from impact_analyzer.schema import ParseResult, Symbol, Edge, Diagnostic, FileInfo

# Regex for import statements
_IMPORT_RE = re.compile(r"^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))", re.MULTILINE)


class PythonParser(LanguageParser):
    """Python language parser using regex-based import extraction."""

    def language_name(self) -> str:
        return "python"

    def supported_extensions(self) -> list[str]:
        return [".py", ".pyi"]

    def grammar_version(self) -> str:
        return "regex-1.0"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        start_time = time.time()
        symbols: list[Symbol] = []
        edges: list[Edge] = []
        diagnostics: list[Diagnostic] = []

        # Extract module-level symbol (the file itself is a module)
        module_id = str(file_path).replace("\\", "/").replace(".py", "").replace(".pyi", "")
        symbols.append(Symbol(
            id=module_id,
            kind="module",
            name=file_path.stem,
            file=str(file_path).replace("\\", "/"),
            line=1,
            exported=True,
        ))

        # Extract imports
        for match in _IMPORT_RE.finditer(content):
            mod = match.group(1) or match.group(2)
            if not mod:
                continue
            mod = mod.split(",")[0].strip().rstrip(".")
            # Convert module path to file path
            target_path = mod.replace(".", "/") + ".py"
            edges.append(Edge(
                source_id=module_id,
                target_id=target_path,
                kind="imports",
                confidence=0.95,
                evidence={
                    "file": str(file_path).replace("\\", "/"),
                    "start_byte": match.start(),
                    "end_byte": match.end(),
                    "matched_text": match.group(0).strip(),
                },
            ))

        # Extract function and class definitions
        for match in re.finditer(r"^(?:async\s+)?def\s+(\w+)", content, re.MULTILINE):
            func_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            symbols.append(Symbol(
                id=f"{module_id}.{func_name}",
                kind="function",
                name=func_name,
                file=str(file_path).replace("\\", "/"),
                line=line_num,
                exported=not func_name.startswith("_"),
            ))

        for match in re.finditer(r"^class\s+(\w+)", content, re.MULTILINE):
            class_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            symbols.append(Symbol(
                id=f"{module_id}.{class_name}",
                kind="class",
                name=class_name,
                file=str(file_path).replace("\\", "/"),
                line=line_num,
                exported=not class_name.startswith("_"),
            ))

        parse_time_ms = (time.time() - start_time) * 1000
        file_info = self.make_file_info(file_path, content, parse_time_ms)

        return ParseResult(
            file_info=file_info,
            symbols=symbols,
            edges=edges,
            diagnostics=diagnostics,
            completeness="complete",
        )