"""Deterministic pattern detectors for code analysis.

These are rule-based detectors that produce candidates.
AI may classify/refine candidates but never creates them.
"""

from __future__ import annotations

from typing import Any

from sage.audit.semantic.graph import CodeGraph, PatternMatch


def detect_layered_architecture(graph: CodeGraph) -> PatternMatch:
    """Detect layered architecture (controller → service → repository)."""
    # Look for nodes with names suggesting layers
    layer_keywords = {
        "controller": ["controller", "handler", "endpoint", "route"],
        "service": ["service", "manager", "processor", "usecase"],
        "repository": ["repository", "repo", "dao", "store", "db"],
    }

    layer_nodes: dict[str, list[str]] = {k: [] for k in layer_keywords}
    for node_id, node in graph.nodes.items():
        name_lower = node.name.lower()
        for layer, keywords in layer_keywords.items():
            if any(kw in name_lower for kw in keywords):
                layer_nodes[layer].append(node_id)

    # Check if there are edges from controller → service → repository
    has_layers = all(len(v) > 0 for v in layer_nodes.values())
    crossings = graph.boundary_crossings()

    confidence = 0.0
    if has_layers:
        confidence = 0.7
        # Boost if boundary crossings exist between layers
        if len(crossings) > 0:
            confidence = 0.85

    return PatternMatch(
        pattern_name="layered_architecture",
        confidence=confidence,
        evidence={
            "layer_counts": {k: len(v) for k, v in layer_nodes.items()},
            "boundary_crossings": len(crossings),
            "has_all_layers": has_layers,
        },
        status="detected" if confidence >= 0.7 else "candidate",
    )


def detect_circular_dependencies(graph: CodeGraph) -> PatternMatch:
    """Detect circular dependencies (strongly connected components with >1 node)."""
    sccs = graph.strongly_connected_components()
    circular = [scc for scc in sccs if len(scc) > 1]

    confidence = 1.0 if circular else 0.0
    return PatternMatch(
        pattern_name="circular_dependencies",
        confidence=confidence,
        evidence={
            "circular_components": [sorted(scc) for scc in circular],
            "total_sccs": len(sccs),
            "circular_count": len(circular),
        },
        status="detected" if circular else "rejected",
    )


def detect_god_class(graph: CodeGraph) -> PatternMatch:
    """Detect god classes (classes with too many methods)."""
    # Group symbols by file/module
    class_methods: dict[str, list[str]] = {}
    for node_id, node in graph.nodes.items():
        if node.kind == "function" and "." in node_id:
            class_id = node_id.rsplit(".", 1)[0]
            class_methods.setdefault(class_id, []).append(node_id)

    # Find classes with >10 methods
    god_classes = {k: v for k, v in class_methods.items() if len(v) > 10}

    confidence = 0.9 if god_classes else 0.0
    return PatternMatch(
        pattern_name="god_class",
        confidence=confidence,
        evidence={
            "god_classes": {k: len(v) for k, v in god_classes.items()},
            "threshold": 10,
        },
        status="detected" if god_classes else "rejected",
    )


def detect_high_coupling(graph: CodeGraph) -> PatternMatch:
    """Detect high coupling (nodes with high fan-in or fan-out)."""
    threshold = 10
    high_fan_in = []
    high_fan_out = []

    for node_id in graph.nodes:
        fi = graph.fan_in(node_id)
        fo = graph.fan_out(node_id)
        if fi > threshold:
            high_fan_in.append((node_id, fi))
        if fo > threshold:
            high_fan_out.append((node_id, fo))

    has_high_coupling = len(high_fan_in) > 0 or len(high_fan_out) > 0
    confidence = 0.8 if has_high_coupling else 0.0

    return PatternMatch(
        pattern_name="high_coupling",
        confidence=confidence,
        evidence={
            "high_fan_in": high_fan_in[:10],
            "high_fan_out": high_fan_out[:10],
            "threshold": threshold,
        },
        status="detected" if has_high_coupling else "rejected",
    )


def detect_dead_code(graph: CodeGraph) -> PatternMatch:
    """Detect potentially dead code (nodes with zero fan-in that aren't entry points)."""
    entry_point_keywords = {"main", "test", "handler", "endpoint", "route", "controller"}
    dead_candidates = []

    for node_id, node in graph.nodes.items():
        if node.kind == "function" and node.exported:
            fi = graph.fan_in(node_id)
            if fi == 0:
                # Check if it's an entry point
                is_entry = any(kw in node.name.lower() for kw in entry_point_keywords)
                if not is_entry:
                    dead_candidates.append(node_id)

    confidence = 0.6 if dead_candidates else 0.0
    return PatternMatch(
        pattern_name="dead_code",
        confidence=confidence,
        evidence={
            "dead_candidates": dead_candidates[:20],
            "count": len(dead_candidates),
        },
        status="candidate" if dead_candidates else "rejected",
    )


def detect_all_patterns(graph: CodeGraph) -> list[PatternMatch]:
    """Run all deterministic pattern detectors."""
    return [
        detect_layered_architecture(graph),
        detect_circular_dependencies(graph),
        detect_god_class(graph),
        detect_high_coupling(graph),
        detect_dead_code(graph),
    ]