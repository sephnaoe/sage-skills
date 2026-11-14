"""JavaScript/TypeScript language parser using tree-sitter.

Supports: .js, .jsx, .ts, .tsx, .mjs, .cjs
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import tree_sitter
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tstypescript

from impact_analyzer.parsers.base import LanguageParser
from impact_analyzer.schema import ParseResult, Symbol, Edge, Diagnostic, FileInfo

JS_QUERY = """
(import_statement) @import

(call_expression) @require

(function_declaration) @func

(class_declaration) @class
"""


class JavaScriptParser(LanguageParser):
    """JavaScript/TypeScript language parser using tree-sitter."""

    def __init__(self, is_typescript: bool = False):
        self._is_typescript = is_typescript
        if is_typescript:
            self._language = tree_sitter.Language(tstypescript.language_typescript())
        else:
            self._language = tree_sitter.Language(tsjs.language())
        self._parser = tree_sitter.Parser(self._language)
        self._query = tree_sitter.Query(self._language, JS_QUERY)
        self._cursor = tree_sitter.QueryCursor(self._query)

    def language_name(self) -> str:
        return "typescript" if self._is_typescript else "javascript"

    def supported_extensions(self) -> list[str]:
        if self._is_typescript:
            return [".ts", ".tsx"]
        return [".js", ".jsx", ".mjs", ".cjs"]

    def grammar_version(self) -> str:
        if self._is_typescript:
            return "tree-sitter-typescript@0.23.2 (ABI 14)"
        return "tree-sitter-javascript@0.25.0 (ABI 15)"

    def _get_name(self, node, kind):
        """Extract name from a function/class declaration node."""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf-8", errors="replace")
        return None

    def parse(self, file_path: Path, content: str) -> ParseResult:
        start_time = time.time()
        source_bytes = content.encode("utf-8")
        symbols: list[Symbol] = []
        edges: list[Edge] = []
        diagnostics: list[Diagnostic] = []

        module_id = str(file_path).replace("\\", "/")

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

        completeness = "complete"
        if tree.root_node.has_error:
            diagnostics.append(Diagnostic(
                severity="warning",
                code="PARSE_ERROR",
                message="Syntax error detected in file",
                file=str(file_path).replace("\\", "/"),
            ))
            completeness = "partial"

        symbols.append(Symbol(
            id=module_id,
            kind="module",
            name=file_path.stem,
            file=str(file_path).replace("\\", "/"),
            line=1,
            exported=True,
        ))

        captures = self._cursor.captures(tree.root_node)

        # Process ES module imports
        import_nodes = captures.get("import", [])
        for node in import_nodes:
            text = node.text.decode("utf-8", errors="replace")
            m = re.search(r'from\s+["\x27`]([^"\x27`]+)["\x27`]', text)
            if m:
                src_text = m.group(1)
                target_path = src_text if src_text.startswith(".") else src_text
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

        # Process require() calls
        require_nodes = captures.get("require", [])
        for node in require_nodes:
            text = node.text.decode("utf-8", errors="replace")
            m = re.search(r'require\s*\(\s*["\x27`]([^"\x27`]+)["\x27`]\s*\)', text)
            if m:
                req_path = m.group(1)
                edges.append(Edge(
                    source_id=module_id,
                    target_id=req_path,
                    kind="imports",
                    confidence=0.95,
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
            func_name = self._get_name(node, "function")
            if func_name:
                line_num = source_bytes[:node.start_byte].count(b"\n") + 1
                symbols.append(Symbol(
                    id=f"{module_id}.{func_name}",
                    kind="function",
                    name=func_name,
                    file=str(file_path).replace("\\", "/"),
                    line=line_num,
                    exported=False,
                ))

        # Process classes
        class_nodes = captures.get("class", [])
        for node in class_nodes:
            class_name = self._get_name(node, "class")
            if class_name:
                line_num = source_bytes[:node.start_byte].count(b"\n") + 1
                symbols.append(Symbol(
                    id=f"{module_id}.{class_name}",
                    kind="class",
                    name=class_name,
                    file=str(file_path).replace("\\", "/"),
                    line=line_num,
                    exported=False,
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