"""Sage Impact Analyzer — maps changed source files to affected test files.

A fast, deterministic tool for change-impact analysis in Python codebases.
Uses cached import graph for sub-second analysis.

License: Apache-2.0
"""

from .impact import ImpactAnalyzer, ImpactResult
from .schema import Symbol, Edge, Diagnostic, ParseResult, AnalysisResult, FileInfo
from .parsers import LanguageParser, PythonParser, JavaScriptParser, GoParser, RustParser
from .parsers.python_ts import PythonTreeSitterParser

__version__ = "1.0.0"
__all__ = [
    "ImpactAnalyzer", "ImpactResult",
    "Symbol", "Edge", "Diagnostic", "ParseResult", "AnalysisResult", "FileInfo",
    "LanguageParser", "PythonParser", "PythonTreeSitterParser",
    "JavaScriptParser", "GoParser", "RustParser",
]