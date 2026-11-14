"""Normalized output schema for Impact Analyzer.

All parsers produce this schema. Downstream consumers rely on this contract.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Symbol:
    """A code symbol (function, class, variable, etc.)."""
    id: str  # Repository-relative, deterministic
    kind: str  # "function", "class", "variable", "module", "interface", "trait", "struct"
    name: str
    file: str  # Repository-relative path
    line: int
    column: int = 0
    exported: bool = False


@dataclass
class Edge:
    """A dependency edge between two symbols/modules."""
    source_id: str
    target_id: str
    kind: str  # "imports", "references", "implements", "reexports", "calls", "unknown"
    confidence: float  # 0.0 to 1.0
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Diagnostic:
    """A parse or analysis diagnostic."""
    severity: str  # "error", "warning", "info"
    code: str  # Diagnostic code (e.g., "PARSE_ERROR", "UNSUPPORTED_SYNTAX")
    message: str
    file: str
    line: int = 0
    column: int = 0


@dataclass
class FileInfo:
    """Metadata about a parsed file."""
    path: str  # Repository-relative
    language: str
    hash: str  # Content hash (sha256)
    size_bytes: int = 0
    parse_time_ms: float = 0.0


@dataclass
class ParseResult:
    """Result of parsing a single file."""
    file_info: FileInfo
    symbols: list[Symbol] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    completeness: str = "complete"  # "complete", "partial", "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_info": asdict(self.file_info),
            "symbols": [asdict(s) for s in self.symbols],
            "edges": [asdict(e) for e in self.edges],
            "diagnostics": [asdict(d) for d in self.diagnostics],
            "completeness": self.completeness,
        }

    def is_valid(self) -> bool:
        """Validate the parse result before downstream use."""
        # Check completeness is valid
        if self.completeness not in ("complete", "partial", "failed"):
            return False
        # Check all edges have valid endpoints
        symbol_ids = {s.id for s in self.symbols}
        for edge in self.edges:
            if edge.confidence < 0.0 or edge.confidence > 1.0:
                return False
            if not edge.source_id or not edge.target_id:
                return False
        # Check diagnostics have valid severity
        for diag in self.diagnostics:
            if diag.severity not in ("error", "warning", "info"):
                return False
        return True


@dataclass
class AnalysisResult:
    """Result of analyzing a set of changed files."""
    schema_version: str = "1"
    analysis_version: str = "1.0.0"
    changed_files: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    completeness: str = "complete"
    confidence: str = "low"  # "high", "medium", "low"
    parse_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "analysis_version": self.analysis_version,
            "changed_files": self.changed_files,
            "affected_files": self.affected_files,
            "affected_tests": self.affected_tests,
            "symbols": [asdict(s) for s in self.symbols],
            "edges": [asdict(e) for e in self.edges],
            "diagnostics": [asdict(d) for d in self.diagnostics],
            "coverage_gaps": self.coverage_gaps,
            "completeness": self.completeness,
            "confidence": self.confidence,
            "parse_time_ms": self.parse_time_ms,
        }

    def is_valid(self) -> bool:
        """Validate the analysis result before downstream use."""
        if self.completeness not in ("complete", "partial", "failed"):
            return False
        if self.confidence not in ("high", "medium", "low"):
            return False
        for edge in self.edges:
            if edge.confidence < 0.0 or edge.confidence > 1.0:
                return False
        return True