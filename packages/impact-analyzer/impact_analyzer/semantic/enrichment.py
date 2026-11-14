"""AI enrichment layer for semantic analysis.

This layer is OPTIONAL and sits behind a feature flag.
It produces descriptions, labels, and explanations — never facts.
All AI output is cached and versioned.

The deterministic graph layer is the source of truth.
AI never creates or modifies graph facts.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sage.audit.semantic.cache import SemanticCache
from sage.audit.semantic.graph import CodeGraph
from sage.audit.semantic.patterns import PatternMatch


class AIEnrichment:
    """AI-assisted enrichment layer. Optional, cached, behind feature flag."""

    def __init__(self, cache: SemanticCache | None = None, enabled: bool = False):
        self.cache = cache or SemanticCache()
        self.enabled = enabled or os.environ.get("SAGE_AI_ENRICHMENT", "0") == "1"

    def describe_module(self, module_id: str, source_code: str) -> str | None:
        """Generate a human-readable description of a module.

        Returns cached description if available, otherwise None (AI not called).
        AI descriptions are generated asynchronously, not on the critical path.
        """
        if not self.enabled:
            return None

        cache_key = self.cache.make_key(source_code, "describe_module:v1")
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # AI call would go here (behind feature flag)
        # For now, return None — AI integration is a future enhancement
        return None

    def classify_pattern(self, pattern: PatternMatch, evidence: dict[str, Any]) -> str:
        """Classify a detected pattern (confirm/reject/refine).

        Returns: "confirmed", "rejected", or "refined"
        """
        if not self.enabled:
            # Without AI, accept all detected patterns
            return "confirmed" if pattern.status == "detected" else "candidate"

        cache_key = self.cache.make_key(
            f"{pattern.pattern_name}:{json.dumps(evidence, sort_keys=True)}",
            "classify_pattern:v1",
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # AI call would go here
        return "confirmed" if pattern.status == "detected" else "candidate"

    def explain_impact(self, changed_file: str, affected_tests: list[str],
                       graph_stats: dict[str, Any]) -> str | None:
        """Generate a human-readable explanation of impact analysis results.

        Returns None if AI is not enabled or not available.
        """
        if not self.enabled:
            return None

        cache_key = self.cache.make_key(
            f"{changed_file}:{sorted(affected_tests)}",
            "explain_impact:v1",
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # AI call would go here
        return None

    def enrich_graph(self, graph: "CodeGraph") -> dict[str, Any]:
        """Enrich a code graph with AI-generated metadata.

        Returns a dict of enrichments (descriptions, labels, explanations).
        Never modifies the graph itself.
        """
        if not self.enabled:
            return {}

        enrichments = {}
        for node_id, node in graph.nodes.items():
            # Only enrich exported symbols
            if node.exported:
                desc = self.describe_module(node_id, "")
                if desc:
                    enrichments[node_id] = {"description": desc}

        return enrichments