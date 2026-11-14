"""ImpactAnalyzer — map changed files to affected tests via import analysis.

Uses tree-sitter parsers for multi-language support and CodeGraph
for deterministic semantic analysis. Zero egress — pure local file reads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import logging

from impact_analyzer.parsers import PythonTreeSitterParser, LanguageParser
from impact_analyzer.parsers.base import LanguageParser as BaseParser
from impact_analyzer.parsers.javascript import JavaScriptParser
from impact_analyzer.parsers.go import GoParser
from impact_analyzer.parsers.rust import RustParser
from impact_analyzer.semantic.graph import CodeGraph

logger = logging.getLogger(__name__)

# Extension → parser mapping
_EXT_TO_PARSER: dict[str, type] = {
    ".py": PythonTreeSitterParser,
    ".js": JavaScriptParser,
    ".ts": JavaScriptParser,
    ".jsx": JavaScriptParser,
    ".tsx": JavaScriptParser,
    ".go": GoParser,
    ".rs": RustParser,
}


def _get_parser(path: Path) -> BaseParser | None:
    """Get the appropriate parser for a file path."""
    cls = _EXT_TO_PARSER.get(path.suffix.lower())
    if cls is None:
        return None
    return cls()


@dataclass
class ImpactResult:
    changed_files: list[str]
    affected_tests: list[str]
    import_graph: dict[str, list[str]]
    coverage_gaps: list[str]
    confidence: str


class ImpactAnalyzer:
    def __init__(self, project_root: Path | None = None):
        self.root = project_root or Path(__file__).resolve().parents[3]
        self._graph_cache: CodeGraph | None = None
        self._cache_path = self.root / "var" / "state" / "import-graph.json"

    def _build_import_graph(self) -> CodeGraph:
        """Build and cache the import graph using tree-sitter parsers."""
        if self._graph_cache is not None:
            return self._graph_cache

        # Try loading from cache
        if self._cache_path.exists():
            try:
                data = json.loads(self._cache_path.read_text(encoding="utf-8"))
                # Rebuild graph from cached parse results not possible;
                # fall through to rebuild
            except (json.JSONDecodeError, Exception):
                pass

        graph = CodeGraph()
        # Scan src/ and tests/
        for subdir in ("src", "tests"):
            base = self.root / subdir
            if not base.exists():
                continue
            for file_path in base.rglob("*"):
                if not file_path.is_file():
                    continue
                if "__pycache__" in str(file_path):
                    continue
                if file_path.suffix.lower() not in _EXT_TO_PARSER:
                    continue
                parser = _get_parser(file_path)
                if parser is None:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                try:
                    rel_path = str(file_path.relative_to(self.root)).replace("\\", "/")
                    result = parser.parse(Path(rel_path), content)
                    graph.merge_parse_result(result)
                except Exception as e:
                    logger.debug("Parse failed for %s: %s", file_path, e)

        self._graph_cache = graph
        graph.resolve_imports()
        # Save cache metadata
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(
                json.dumps({"node_count": len(graph.nodes), "edge_count": len(graph.edges)}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        return graph

    def analyze(self, changed_files: list[str]) -> ImpactResult:
        """Analyze impact of changed files on tests."""
        graph = self._build_import_graph()
        logger.info("Analyzing impact of %d changed files", len(changed_files))
        affected_tests: set[str] = set()

        for changed in changed_files:
            changed_norm = changed.replace("\\", "/")
            # Find node IDs matching this file
            file_nodes = [n.id for n in graph.nodes.values() if n.file == changed_norm or n.file.endswith(changed_norm)]
            for node_id in file_nodes:
                reachable = graph.reachable_from(node_id)
                for rid in reachable:
                    rnode = graph.nodes.get(rid)
                    if rnode and rnode.file.startswith("tests/"):
                        affected_tests.add(rnode.file)

            # Also check reverse: who imports this file
            for edge in graph.edges:
                if edge.target_id in file_nodes or any(edge.target_id.endswith(changed_norm) for _ in [None]):
                    src_node = graph.nodes.get(edge.source_id)
                    if src_node and src_node.file.startswith("tests/"):
                        affected_tests.add(src_node.file)

        # Coverage gaps
        coverage_gaps = []
        for changed in changed_files:
            changed_norm = changed.replace("\\", "/")
            if changed_norm.startswith("src/"):
                stem = Path(changed_norm).stem
                test_candidates = [
                    f"tests/unit/test_{stem}.py",
                    f"tests/test_{stem}.py",
                ]
                has_test = any((self.root / c).exists() for c in test_candidates)
                if not has_test and not any(stem in t for t in affected_tests):
                    coverage_gaps.append(f"No direct test found for {changed_norm}")

        confidence = "high" if affected_tests else "low"
        if len(changed_files) > 5:
            confidence = "medium"

        import_graph = {}
        for changed in changed_files:
            changed_norm = changed.replace("\\", "/")
            import_graph[changed_norm] = sorted(
                n.file for n in graph.nodes.values()
                if any(e.source_id == n.id and e.target_id in [x.id for x in graph.nodes.values() if x.file == changed_norm]
                       for e in graph.edges)
            )

        return ImpactResult(
            changed_files=changed_files,
            affected_tests=sorted(affected_tests),
            import_graph=import_graph,
            coverage_gaps=coverage_gaps,
            confidence=confidence,
        )

    def get_all_tests(self) -> list[str]:
        """List all test files."""
        tests = []
        for py_file in (self.root / "tests").rglob("test_*.py"):
            tests.append(str(py_file.relative_to(self.root)).replace("\\", "/"))
        return sorted(tests)