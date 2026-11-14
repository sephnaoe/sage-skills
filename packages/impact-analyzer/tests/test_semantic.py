"""Tests for semantic analysis package."""

from __future__ import annotations

from pathlib import Path

import pytest

from sage.audit.semantic import (
    CodeGraph, GraphNode, GraphEdge, PatternMatch,
    detect_all_patterns,
    SemanticCache,
    AIEnrichment,
)


class TestCodeGraph:
    def test_add_node(self):
        graph = CodeGraph()
        node = GraphNode(id="a", kind="module", name="a", file="a.py", line=1, language="python")
        graph.add_node(node)
        assert "a" in graph.nodes
        assert graph.nodes["a"].name == "a"

    def test_add_edge(self):
        graph = CodeGraph()
        node_a = GraphNode(id="a", kind="module", name="a", file="a.py", line=1, language="python")
        node_b = GraphNode(id="b", kind="module", name="b", file="b.py", line=1, language="python")
        graph.add_node(node_a)
        graph.add_node(node_b)
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        assert len(graph.edges) == 1

    def test_forward_reachability(self):
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="b", target_id="c", kind="imports"))
        reachable = graph.forward_reachability("a")
        assert "a" in reachable
        assert "b" in reachable
        assert "c" in reachable

    def test_reverse_reachability(self):
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="b", target_id="c", kind="imports"))
        reverse = graph.reverse_reachability("c")
        assert "c" in reverse
        assert "b" in reverse
        assert "a" in reverse

    def test_fan_in_fan_out(self):
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="c", target_id="b", kind="imports"))
        assert graph.fan_in("b") == 2
        assert graph.fan_out("a") == 1

    def test_strongly_connected_components(self):
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        # Create cycle: a -> b -> c -> a
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="b", target_id="c", kind="imports"))
        graph.add_edge(GraphEdge(source_id="c", target_id="a", kind="imports"))
        sccs = graph.strongly_connected_components()
        assert len(sccs) == 1
        assert sccs[0] == {"a", "b", "c"}

    def test_boundary_crossings(self):
        graph = CodeGraph()
        graph.add_node(GraphNode(id="mod_a.func", kind="function", name="func", file="a.py", line=1, language="python"))
        graph.add_node(GraphNode(id="mod_b.util", kind="function", name="util", file="b.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="mod_a.func", target_id="mod_b.util", kind="calls"))
        crossings = graph.boundary_crossings()
        assert len(crossings) == 1

    def test_to_dict(self):
        graph = CodeGraph()
        graph.add_node(GraphNode(id="a", kind="module", name="a", file="a.py", line=1, language="python"))
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d
        assert d["stats"]["node_count"] == 1

    def test_from_parse_results(self):
        from sage.audit.schema import ParseResult, Symbol, Edge, FileInfo
        fi = FileInfo(path="test.py", language="python", hash="abc")
        pr = ParseResult(
            file_info=fi,
            symbols=[Symbol(id="test.foo", kind="function", name="foo", file="test.py", line=1)],
            edges=[Edge(source_id="test", target_id="os.py", kind="imports", confidence=0.99)],
        )
        graph = CodeGraph.from_parse_results([pr])
        assert "test.foo" in graph.nodes
        assert len(graph.edges) == 1


class TestPatternDetection:
    def test_detect_circular_dependencies(self):
        from sage.audit.semantic.patterns import detect_circular_dependencies
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="b", target_id="c", kind="imports"))
        graph.add_edge(GraphEdge(source_id="c", target_id="a", kind="imports"))
        result = detect_circular_dependencies(graph)
        assert result.pattern_name == "circular_dependencies"
        assert result.confidence == 1.0
        assert result.status == "detected"

    def test_detect_no_circular(self):
        from sage.audit.semantic.patterns import detect_circular_dependencies
        graph = CodeGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(GraphNode(id=nid, kind="module", name=nid, file=f"{nid}.py", line=1, language="python"))
        graph.add_edge(GraphEdge(source_id="a", target_id="b", kind="imports"))
        graph.add_edge(GraphEdge(source_id="b", target_id="c", kind="imports"))
        result = detect_circular_dependencies(graph)
        assert result.confidence == 0.0
        assert result.status == "rejected"

    def test_detect_all_patterns(self):
        from sage.audit.semantic.patterns import detect_all_patterns
        graph = CodeGraph()
        graph.add_node(GraphNode(id="a", kind="module", name="a", file="a.py", line=1, language="python"))
        results = detect_all_patterns(graph)
        assert len(results) == 5
        assert all(isinstance(r, PatternMatch) for r in results)

    def test_detect_god_class(self):
        from sage.audit.semantic.patterns import detect_god_class
        graph = CodeGraph()
        # Create a class with 15 methods
        for i in range(15):
            graph.add_node(GraphNode(id=f"bigclass.method{i}", kind="function", name=f"method{i}", file="big.py", line=i+1, language="python"))
        result = detect_god_class(graph)
        assert result.pattern_name == "god_class"
        assert result.confidence == 0.9
        assert result.status == "detected"

    def test_detect_dead_code(self):
        from sage.audit.semantic.patterns import detect_dead_code
        graph = CodeGraph()
        graph.add_node(GraphNode(id="unused_func", kind="function", name="unused_func", file="a.py", line=1, language="python", exported=True))
        result = detect_dead_code(graph)
        assert result.pattern_name == "dead_code"
        assert "unused_func" in result.evidence["dead_candidates"]


class TestSemanticCache:
    def test_set_and_get(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SemanticCache(cache_dir=Path(tmpdir))
            cache.set("key1", {"description": "test"})
            result = cache.get("key1")
            assert result == {"description": "test"}

    def test_get_missing(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SemanticCache(cache_dir=Path(tmpdir))
            result = cache.get("nonexistent")
            assert result is None

    def test_invalidate(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SemanticCache(cache_dir=Path(tmpdir))
            cache.set("key1", {"description": "test"})
            cache.invalidate("key1")
            result = cache.get("key1")
            assert result is None

    def test_make_key(self):
        key1 = SemanticCache.make_key("hello", "v1")
        key2 = SemanticCache.make_key("hello", "v1")
        key3 = SemanticCache.make_key("world", "v1")
        assert key1 == key2
        assert key1 != key3

    def test_clear(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SemanticCache(cache_dir=Path(tmpdir))
            cache.set("key1", {"description": "test"})
            cache.clear()
            result = cache.get("key1")
            assert result is None


class TestAIEnrichment:
    def test_disabled_by_default(self):
        enrichment = AIEnrichment(enabled=False)
        assert enrichment.enabled is False
        result = enrichment.describe_module("test", "code")
        assert result is None

    def test_classify_pattern_without_ai(self):
        enrichment = AIEnrichment(enabled=False)
        pattern = PatternMatch(pattern_name="test", confidence=0.9, status="detected")
        result = enrichment.classify_pattern(pattern, {})
        assert result == "confirmed"

    def test_enrich_graph_without_ai(self):
        enrichment = AIEnrichment(enabled=False)
        graph = CodeGraph()
        graph.add_node(GraphNode(id="a", kind="module", name="a", file="a.py", line=1, language="python", exported=True))
        result = enrichment.enrich_graph(graph)
        assert result == {}

    def test_explain_impact_without_ai(self):
        enrichment = AIEnrichment(enabled=False)
        result = enrichment.explain_impact("test.py", ["test_a.py"], {})
        assert result is None