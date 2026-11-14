"""Semantic analysis package for Impact Analyzer.

Deterministic graph analysis is the source of truth.
AI enrichment is optional, cached, and never gates critical path.
"""

from __future__ import annotations

from impact_analyzer.semantic.graph import CodeGraph, GraphNode, GraphEdge, PatternMatch
from impact_analyzer.semantic.patterns import detect_all_patterns
from impact_analyzer.semantic.cache import SemanticCache
from impact_analyzer.semantic.enrichment import AIEnrichment

__all__ = [
    "CodeGraph", "GraphNode", "GraphEdge", "PatternMatch",
    "detect_all_patterns",
    "SemanticCache",
    "AIEnrichment",
]

__version__ = "1.0.0"