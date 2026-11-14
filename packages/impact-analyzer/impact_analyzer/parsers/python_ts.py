"""Python language parser using tree-sitter.

Provides more accurate parsing than regex-based approach.
Uses tree-sitter-python grammar for syntax tree extraction.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import tree_sitter
import tree_sitter_python as tspython

from impact_analyzer.parsers.base import LanguageParser
from impact_analyzer.schema import ParseResult, Symbol, Edge, Diagnostic, FileInfo

# Tree-sitter query for extracting imports, functions, classes
PYTHON_QUERY = """
(import_statement
  name: (dotted_name) @import.name) @import

(import_from_statement
  module_name: (dotted_name) @from.module
  name: (dotted_name) @from.name) @from

(function_definition
  name: (identifier) @func.name) @func

(class_definition
  name: (identifier) @class.name) @class
"""


class PythonTreeSitterParser(LanguageParser):
    """Python language parser using tree-sitter."""

    def __init__(self):
        self._language = tree_sitter.Language(tspython.language())
        self._parser = tree_sitter.Parser(self._language)
        self._query = tree_sitter.Query(self._language, PYTHON_QUERY)
        self._cursor = tree_sitter.QueryCursor(self._query)

    def language_name(self) -> str:
        return "python"

    def supported_extensions(self) -> list[str]:
        return [".py", ".pyi"]

    def grammar_version(self) -> str:
        return "tree-sitter-python@0.25.0 (ABI 15)"

    def parse(self, file_path: Path, content: str) -> ParseResult:
        start_time = time.time()
        source_bytes = content.encode("utf-8")
        symbols: list[Symbol] = []
        edges: list[Edge] = []
        diagnostics: list[Diagnostic] = []

        module_id = str(file_path).replace("\\", "/").replace(".py", "").replace(".pyi", "")

        # Parse with tree-sitter
        try:
            tree = self._parser.parse(source_bytes)
        except Exception as e:
            diagnostics.append(Diagnostic(
                severity="error",
                code="PARSE_FAILED",
                message=str(e),
                file=str(file_path).replace("\\", "/"),
            ))
            parse_time_ms = (time.time() - start_time) * 1000
            file_info = self.make_file_info(file_path, content, parse_time_ms)
            return ParseResult(
                file_info=file_info,
                symbols=symbols,
                edges=edges,
                diagnostics=diagnostics,
                completeness="failed",
            )

        # Check for syntax errors
        completeness = "complete"
        if tree.root_node.has_error:
            diagnostics.append(Diagnostic(
                severity="warning",
                code="PARSE_ERROR",
                message="Syntax error detected in file",
                file=str(file_path).replace("\\", "/"),
            ))
            completeness = "partial"

        # Module symbol
        symbols.append(Symbol(
            id=module_id,
            kind="module",
            name=file_path.stem,
            file=str(file_path).replace("\\", "/"),
            line=1,
            exported=True,
        ))

        # Extract using query
        captures = self._cursor.captures(tree.root_node)

        # Process imports
        import_nodes = captures.get("import", [])
        for node in import_nodes:
            text = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            # Extract module name from import statement
            name_nodes = captures.get("import.name", [])
            for name_node in name_nodes:
                if name_node.start_byte >= node.start_byte and name_node.end_byte <= node.end_byte:
                    mod_name = name_node.text.decode("utf-8", errors="replace")
                    target_path = mod_name.replace(".", "/") + ".py"
                    edges.append(Edge(
                        source_id=module_id,
                        target_id=target_path,
                        kind="imports",
                        confidence=0.99,
                        evidence={
                            "file": str(file_path).replace("\\", "/"),
                            "start_byte": node.start_byte,
                            "end_byte": node.end_byte,
                            "matched_text": text,
                        },
                    ))

        # Process from imports
        from_nodes = captures.get("from", [])
        for node in from_nodes:
            text = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            mod_nodes = captures.get("from.module", [])
            for mod_node in mod_nodes:
                if mod_node.start_byte >= node.start_byte and mod_node.end_byte <= node.end_byte:
                    mod_name = mod_node.text.decode("utf-8", errors="replace")
                    target_path = mod_name.replace(".", "/") + ".py"
                    edges.append(Edge(
                        source_id=module_id,
                        target_id=target_path,
                        kind="imports",
                        confidence=0.99,
                        evidence={
                            "file": str(file_path).replace("\\", "/"),
                            "start_byte": node.start_byte,
                            "end_byte": node.end_byte,
                            "matched_text": text,
                        },
                    ))

        # Process functions
        func_nodes = captures.get("func", [])
        for node in func_nodes:
            name_nodes = captures.get("func.name", [])
            for name_node in name_nodes:
                if name_node.start_byte >= node.start_byte and name_node.end_byte <= node.end_byte:
                    func_name = name_node.text.decode("utf-8", errors="replace")
                    line_num = source_bytes[:node.start_byte].count(b"\n") + 1
                    symbols.append(Symbol(
                        id=f"{module_id}.{func_name}",
                        kind="function",
                        name=func_name,
                        file=str(file_path).replace("\\", "/"),
                        line=line_num,
                        exported=not func_name.startswith("_"),
                    ))

        # Process classes
        class_nodes = captures.get("class", [])
        for node in class_nodes:
            name_nodes = captures.get("class.name", [])
            for name_node in name_nodes:
                if name_node.start_byte >= node.start_byte and name_node.end_byte <= node.end_byte:
                    class_name = name_node.text.decode("utf-8", errors="replace")
                    line_num = source_bytes[:node.start_byte].count(b"\n") + 1
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
            completeness=completeness,
        )