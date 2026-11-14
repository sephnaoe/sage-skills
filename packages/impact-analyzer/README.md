# Sage Impact Analyzer

A fast, deterministic tool for change-impact analysis across multiple languages.

## What It Does

Maps changed source files to the test files that exercise them, using a cached import graph built with tree-sitter parsers. Answers the question: **"If I change file X, which tests should I run?"**

## Supported Languages

| Language | Parser | Status |
|----------|--------|--------|
| Python | tree-sitter-python | ✅ Done |
| JavaScript/TypeScript | tree-sitter-javascript/typescript | ✅ Done |
| Go | tree-sitter-go | ✅ Done |
| Rust | tree-sitter-rust | ✅ Done |

## Features

- **Multi-language support** (Python, JS/TS, Go, Rust) via tree-sitter
- **Sub-second analysis** (0.5s with cached import graph)
- **Direct + transitive impact** (CodeGraph reachability)
- **Coverage gap detection** (source modules with no corresponding test)
- **Confidence scoring** (high/medium/low based on test discovery)
- **Semantic analysis** (code graph, pattern detection, cache, AI enrichment behind feature flag)
- **Normalized schema** (Symbol, Edge, Diagnostic, ParseResult, AnalysisResult)

## Installation

```bash
pip install sage-impact-analyzer
```

## Usage

```python
from pathlib import Path
from impact_analyzer import ImpactAnalyzer

analyzer = ImpactAnalyzer(project_root=Path("."))
result = analyzer.analyze(["src/sage/memory/security.py"])

print(f"Affected tests: {result.affected_tests}")
print(f"Coverage gaps: {result.coverage_gaps}")
print(f"Confidence: {result.confidence}")
```

## License

Apache-2.0 (see LICENSE file)