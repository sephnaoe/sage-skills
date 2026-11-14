"""ImpactAnalyzer — map changed files to affected tests via import analysis.

Optimized: uses regex-based import extraction and caches graph to disk.
Zero egress — pure local file reads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# Regex for import statements
_IMPORT_RE = re.compile(r"^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))", re.MULTILINE)


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
        self._graph_cache: dict[str, set[str]] | None = None
        self._cache_path = self.root / "var" / "state" / "import-graph.json"

    def _build_import_graph(self) -> dict[str, set[str]]:
        """Build and cache the import graph."""
        if self._graph_cache is not None:
            return self._graph_cache

        # Try loading from cache
        if self._cache_path.exists():
            try:
                data = json.loads(self._cache_path.read_text(encoding="utf-8"))
                # Convert lists back to sets
                self._graph_cache = {k: set(v) for k, v in data.items()}
                return self._graph_cache
            except (json.JSONDecodeError, Exception) as e:
                logger.error("Error loading cache: %s", e, exc_info=True)

        graph: dict[str, set[str]] = {}
        # Only scan src/ and tests/
        for subdir in ("src", "tests"):
            base = self.root / subdir
            if not base.exists():
                continue
            for py_file in base.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                rel_path = str(py_file.relative_to(self.root)).replace("\\", "/")

                for match in _IMPORT_RE.finditer(content):
                    mod = match.group(1) or match.group(2)
                    if not mod:
                        continue
                    # Clean up (remove trailing dots, split on comma)
                    mod = mod.split(",")[0].strip().rstrip(".")
                    mod_path = self._module_to_path(mod)
                    if mod_path:
                        graph.setdefault(mod_path, set()).add(rel_path)

        self._graph_cache = graph
        # Save cache
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(
                json.dumps({k: sorted(v) for k, v in graph.items()}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        return graph

    def _module_to_path(self, module_name: str) -> str | None:
        """Convert module name to file path."""
        parts = module_name.split(".")
        if parts and parts[0] == "sage":
            rel = "src/" + "/".join(parts) + ".py"
            if (self.root / rel).exists():
                return rel
            rel = "src/" + "/".join(parts) + "/__init__.py"
            if (self.root / rel).exists():
                return rel
        rel = "/".join(parts) + ".py"
        if (self.root / rel).exists():
            return rel
        return None

    def analyze(self, changed_files: list[str]) -> ImpactResult:
        """Analyze impact of changed files on tests."""
        graph = self._build_import_graph()
        logger.info("Analyzing impact of %d changed files", len(changed_files))
        affected_tests: set[str] = set()

        for changed in changed_files:
            changed_norm = changed.replace("\\", "/")
            # Direct importers
            for importer in graph.get(changed_norm, set()):
                if importer.startswith("tests/"):
                    affected_tests.add(importer)
            # Transitive (one level)
            for importer in list(graph.get(changed_norm, set())):
                for transitive in graph.get(importer, set()):
                    if transitive.startswith("tests/"):
                        affected_tests.add(transitive)

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

        return ImpactResult(
            changed_files=changed_files,
            affected_tests=sorted(affected_tests),
            import_graph={k: sorted(v) for k, v in graph.items() if k in changed_files},
            coverage_gaps=coverage_gaps,
            confidence=confidence,
        )

    def get_all_tests(self) -> list[str]:
        """List all test files."""
        tests = []
        for py_file in (self.root / "tests").rglob("test_*.py"):
            tests.append(str(py_file.relative_to(self.root)).replace("\\", "/"))
        return sorted(tests)