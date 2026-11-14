"""Semantic analysis package for Impact Analyzer.

Deterministic graph analysis is the source of truth.
AI enrichment is optional, cached, and never gates critical path.
"""

from __future__ import annotations

from sage.audit.semantic.graph import CodeGraph, GraphNode, GraphEdge, PatternMatch
from sage.audit.semantic.patterns import detect_all_patterns
from sage.audit.semantic.cache import SemanticCache
from sage.audit.semantic.enrichment import AIEnrichment

__all__ = [
    "CodeGraph", "GraphNode", "GraphEdge", "PatternMatch",
    "detect_all_patterns",
    "SemanticCache",
    "AIEnrichment",
]

__version__ = "1.0.0"