"""Code graph model — deterministic facts about a codebase.

This is the source of truth for all downstream analysis.
AI never creates or modifies graph facts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GraphNode:
    """A node in the code graph (symbol, module, file)."""
    id: str
    kind: str  # "module", "function", "class", "variable", "interface", "struct", "enum", "trait"
    name: str
    file: str
    line: int
    language: str
    exported: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ast_hash(self) -> str:
        """Content hash for cache invalidation."""
        content = f"{self.id}:{self.kind}:{self.name}:{self.file}:{self.line}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GraphEdge:
    """An edge in the code graph (dependency, call, reference)."""
    source_id: str
    target_id: str
    kind: str  # "imports", "calls", "references", "implements", "extends", "uses"
    confidence: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PatternMatch:
    """Result of a deterministic pattern detection."""
    pattern_name: str
    confidence: float  # 0.0 to 1.0
    evidence: dict[str, Any] = field(default_factory=dict)
    status: str = "candidate"  # "detected", "candidate", "rejected"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CodeGraph:
    """Deterministic code graph — source of truth for all analysis."""

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._adjacency: dict[str, set[str]] | None = None
        self._reverse_adjacency: dict[str, set[str]] | None = None

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        self._invalidate_caches()

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        self._invalidate_caches()

    def _invalidate_caches(self):
        self._adjacency = None
        self._reverse_adjacency = None

    def _build_adjacency(self) -> dict[str, set[str]]:
        if self._adjacency is not None:
            return self._adjacency
        adj: dict[str, set[str]] = {n: set() for n in self.nodes}
        for edge in self.edges:
            if edge.source_id in adj:
                adj[edge.source_id].add(edge.target_id)
        self._adjacency = adj
        return adj

    def _build_reverse_adjacency(self) -> dict[str, set[str]]:
        if self._reverse_adjacency is not None:
            return self._reverse_adjacency
        radj: dict[str, set[str]] = {n: set() for n in self.nodes}
        for edge in self.edges:
            if edge.target_id in radj:
                radj[edge.target_id].add(edge.source_id)
        self._reverse_adjacency = radj
        return radj

    def forward_reachability(self, start_id: str) -> set[str]:
        """All nodes reachable from start_id (forward)."""
        adj = self._build_adjacency()
        visited: set[str] = set()
        stack = [start_id]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        return visited

    def reverse_reachability(self, start_id: str) -> set[str]:
        """All nodes that can reach start_id (reverse)."""
        radj = self._build_reverse_adjacency()
        visited: set[str] = set()
        stack = [start_id]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in radj.get(node, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        return visited

    def fan_in(self, node_id: str) -> int:
        """Number of incoming edges."""
        return len(self._build_reverse_adjacency().get(node_id, set()))

    def fan_out(self, node_id: str) -> int:
        """Number of outgoing edges."""
        return len(self._build_adjacency().get(node_id, set()))

    def strongly_connected_components(self) -> list[set[str]]:
        """Find strongly connected components (Tarjan's algorithm)."""
        adj = self._build_adjacency()
        index_counter = [0]
        stack: list[str] = []
        lowlink: dict[str, int] = {}
        index: dict[str, int] = {}
        on_stack: dict[str, bool] = {}
        result: list[set[str]] = []

        def strongconnect(v: str):
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True

            for w in adj.get(v, set()):
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif on_stack.get(w, False):
                    lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                component: set[str] = set()
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.add(w)
                    if w == v:
                        break
                result.append(component)

        for v in list(self.nodes.keys()):
            if v not in index:
                strongconnect(v)

        return result

    def boundary_crossings(self) -> list[tuple[str, str, str]]:
        """Find edges that cross module boundaries."""
        crossings = []
        for edge in self.edges:
            src_module = edge.source_id.split(".")[0] if "." in edge.source_id else edge.source_id
            tgt_module = edge.target_id.split(".")[0] if "." in edge.target_id else edge.target_id
            if src_module != tgt_module:
                crossings.append((edge.source_id, edge.target_id, edge.kind))
        return crossings

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "scc_count": len(self.strongly_connected_components()),
                "boundary_crossings": len(self.boundary_crossings()),
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_parse_results(cls, results: list) -> "CodeGraph":
        """Build a CodeGraph from a list of ParseResults."""
        graph = cls()
        for result in results:
            for symbol in result.symbols:
                node = GraphNode(
                    id=symbol.id,
                    kind=symbol.kind,
                    name=symbol.name,
                    file=symbol.file,
                    line=symbol.line,
                    language=result.file_info.language,
                    exported=symbol.exported,
                )
                graph.add_node(node)
            for edge in result.edges:
                graph.add_edge(GraphEdge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    kind=edge.kind,
                    confidence=edge.confidence,
                    evidence=edge.evidence,
                ))
        graph.resolve_imports()
        return graph

    def merge_parse_result(self, result) -> None:
        for symbol in result.symbols:
            node = GraphNode(
                id=symbol.id,
                kind=symbol.kind,
                name=symbol.name,
                file=symbol.file,
                line=symbol.line,
                language=result.file_info.language,
                exported=symbol.exported,
            )
            self.add_node(node)
        for edge in result.edges:
            self.add_edge(GraphEdge(
                source_id=edge.source_id,
                target_id=edge.target_id,
                kind=edge.kind,
                confidence=edge.confidence,
                evidence=edge.evidence,
            ))

    def resolve_imports(self) -> None:
        """Resolve import edges to actual node IDs.

        Import edges have target IDs like 'sage/audit/impact.py imports'.
        This method matches them to actual node IDs in the graph.
        """
        # Build file → node ID mapping
        file_to_node: dict[str, str] = {}
        for node_id, node in self.nodes.items():
            if node.kind == "module":
                file_to_node[node.file] = node_id
            # Also map by relative path
            for prefix in ("src/", "tests/"):
                if node.file.startswith(prefix):
                    rel = node.file[len(prefix):]
                    file_to_node[rel] = node_id

        resolved_edges = []
        for edge in self.edges:
            if "imports" not in edge.kind and not edge.target_id.endswith(" imports"):
                resolved_edges.append(edge)
                continue
            # Extract import path from target_id like 'sage/audit/impact.py imports'
            import_path = edge.target_id.replace(" imports", "").strip()
            # Try to find matching node
            target_node_id = None
            # Direct match
            if import_path in file_to_node:
                target_node_id = file_to_node[import_path]
            else:
                # Try with src/ prefix
                for prefix in ("src/", ""):
                    candidate = prefix + import_path
                    if candidate in file_to_node:
                        target_node_id = file_to_node[candidate]
                        break
                # Try matching by filename (handle relative imports and extensions)
                if target_node_id is None:
                    basename = import_path.split("/")[-1].lstrip("./")
                    for fpath, nid in file_to_node.items():
                        fname = fpath.split("/")[-1].split(".")[0]
                        if fname == basename or fpath.endswith(basename) or fpath.endswith(import_path):
                            target_node_id = nid
                            break
                    # Try with common extensions
                    if target_node_id is None:
                        for ext in (".js", ".ts", ".py", ".go", ".rs"):
                            candidate = basename + ext
                            for fpath, nid in file_to_node.items():
                                if fpath.endswith(candidate):
                                    target_node_id = nid
                                    break
                            if target_node_id is not None:
                                break
            if target_node_id is not None:
                resolved_edges.append(GraphEdge(
                    source_id=edge.source_id,
                    target_id=target_node_id,
                    kind="imports",
                    confidence=edge.confidence,
                    evidence=edge.evidence,
                ))
            else:
                # Keep unresolved edges (stdlib, third-party) as-is
                resolved_edges.append(edge)
        self.edges = resolved_edges

    def reachable_from(self, start_id: str, max_depth: int = 100) -> set:
        visited = set()
        queue = [start_id]
        depth = 0
        while queue and depth < max_depth:
            next_level = []
            for node_id in queue:
                if node_id in visited:
                    continue
                visited.add(node_id)
                for edge in self.edges:
                    if edge.source_id == node_id and edge.target_id not in visited:
                        next_level.append(edge.target_id)
            queue = next_level
            depth += 1
        return visited