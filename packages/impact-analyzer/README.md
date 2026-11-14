# Sage Impact Analyzer

A fast, deterministic tool for change-impact analysis in Python codebases.

## What It Does

Maps changed source files to the test files that exercise them, using a cached import graph. Answers the question: **"If I change file X, which tests should I run?"**

## Features

- **Sub-second analysis** (0.5s with cached import graph)
- **Direct + transitive impact** (one level of transitivity)
- **Coverage gap detection** (source modules with no corresponding test)
- **Confidence scoring** (high/medium/low based on test discovery)
- **Python codebases** (with plans for JS/TS, Go, Rust)

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