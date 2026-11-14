"""Language parser package for Impact Analyzer.

All parsers implement the LanguageParser interface and produce
the same normalized output schema (impact_analyzer.schema).
"""

from __future__ import annotations

from impact_analyzer.parsers.base import LanguageParser
from impact_analyzer.parsers.python import PythonParser
from impact_analyzer.parsers.python_ts import PythonTreeSitterParser
from impact_analyzer.parsers.javascript import JavaScriptParser
from impact_analyzer.parsers.go import GoParser
from impact_analyzer.parsers.rust import RustParser

__all__ = [
    "LanguageParser",
    "PythonParser",
    "PythonTreeSitterParser",
    "JavaScriptParser",
    "GoParser",
    "RustParser",
]