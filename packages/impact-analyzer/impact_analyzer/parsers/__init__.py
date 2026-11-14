"""Language parser package for Impact Analyzer.

All parsers implement the LanguageParser interface and produce
the same normalized output schema (sage.audit.schema).
"""

from __future__ import annotations

from sage.audit.parsers.base import LanguageParser
from sage.audit.parsers.python import PythonParser
from sage.audit.parsers.javascript import JavaScriptParser
from sage.audit.parsers.go import GoParser
from sage.audit.parsers.rust import RustParser

__all__ = [
    "LanguageParser",
    "PythonParser",
    "JavaScriptParser",
    "GoParser",
    "RustParser",
]