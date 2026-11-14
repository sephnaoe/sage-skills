"""CLI for Sage Impact Analyzer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from impact_analyzer import ImpactAnalyzer


def main():
    parser = argparse.ArgumentParser(
        prog="impact-analyzer",
        description="Fast, deterministic change-impact analysis for multi-language codebases.",
    )
    parser.add_argument(
        "files", nargs="*", help="Changed files (optional — auto-detects from git if omitted)"
    )
    parser.add_argument("--auto", action="store_true", help="Auto-detect changed files from git")
    parser.add_argument("--staged", action="store_true", help="Analyze staged changes")
    parser.add_argument("--commit", type=str, help="Analyze changes in a specific commit (e.g., HEAD~1)")
    parser.add_argument("--root", type=str, default=".", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown report")
    parser.add_argument("--output", type=str, help="Write output to file")
    args = parser.parse_args()

    analyzer = ImpactAnalyzer(project_root=Path(args.root))

    if args.auto or args.staged or args.commit or not args.files:
        result = analyzer.analyze_git_changes(
            staged=args.staged, commit=args.commit
        )
    else:
        result = analyzer.analyze(args.files)

    if args.json:
        output = result.to_json()
    elif args.markdown:
        output = result.to_markdown()
    else:
        lines = [f"Confidence: {result.confidence}"]
        lines.append(f"Affected tests ({len(result.affected_tests)}):")
        for t in result.affected_tests:
            lines.append(f"  {t}")
        if result.coverage_gaps:
            lines.append(f"Coverage gaps ({len(result.coverage_gaps)}):")
            for g in result.coverage_gaps:
                lines.append(f"  {g}")
        output = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()