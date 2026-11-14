"""Tests for Sage audit schema and parsers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sage.audit.schema import Symbol, Edge, Diagnostic, ParseResult, AnalysisResult, FileInfo
from sage.audit.parsers import LanguageParser
from sage.audit.python_parser import PythonParser


class TestSchema:
    def test_symbol_creation(self):
        s = Symbol(id="foo.Bar", kind="class", name="Bar", file="foo.py", line=10)
        assert s.id == "foo.Bar"
        assert s.kind == "class"
        assert s.exported is False

    def test_edge_creation(self):
        e = Edge(source_id="a", target_id="b", kind="imports", confidence=0.95)
        assert e.source_id == "a"
        assert e.target_id == "b"
        assert e.confidence == 0.95

    def test_parse_result_validation(self):
        fi = FileInfo(path="test.py", language="python", hash="abc123")
        pr = ParseResult(file_info=fi, completeness="complete")
        assert pr.is_valid() is True

    def test_parse_result_invalid_completeness(self):
        fi = FileInfo(path="test.py", language="python", hash="abc123")
        pr = ParseResult(file_info=fi, completeness="invalid")
        assert pr.is_valid() is False

    def test_edge_invalid_confidence(self):
        fi = FileInfo(path="test.py", language="python", hash="abc123")
        e = Edge(source_id="a", target_id="b", kind="imports", confidence=1.5)
        pr = ParseResult(file_info=fi, edges=[e])
        assert pr.is_valid() is False

    def test_analysis_result_validation(self):
        ar = AnalysisResult(confidence="high", completeness="complete")
        assert ar.is_valid() is True

    def test_analysis_result_invalid_confidence(self):
        ar = AnalysisResult(confidence="invalid", completeness="complete")
        assert ar.is_valid() is False

    def test_parse_result_to_dict(self):
        fi = FileInfo(path="test.py", language="python", hash="abc123")
        s = Symbol(id="test.foo", kind="function", name="foo", file="test.py", line=5)
        pr = ParseResult(file_info=fi, symbols=[s])
        d = pr.to_dict()
        assert "symbols" in d
        assert d["symbols"][0]["name"] == "foo"

    def test_analysis_result_to_dict(self):
        ar = AnalysisResult(changed_files=["a.py"], affected_tests=["test_a.py"])
        d = ar.to_dict()
        assert d["changed_files"] == ["a.py"]
        assert d["affected_tests"] == ["test_a.py"]


class TestPythonParser:
    def test_parse_simple_file(self):
        parser = PythonParser()
        content = "import os\nimport sys\n\ndef foo():\n    pass\n\nclass Bar:\n    pass\n"
        result = parser.parse(Path("test.py"), content)
        assert result.file_info.language == "python"
        assert result.completeness == "complete"
        assert result.is_valid() is True
        # Should have module + function + class symbols
        symbol_names = [s.name for s in result.symbols]
        assert "foo" in symbol_names
        assert "Bar" in symbol_names

    def test_parse_imports(self):
        parser = PythonParser()
        content = "import os\nfrom pathlib import Path\nfrom sage.audit import schema\n"
        result = parser.parse(Path("test.py"), content)
        assert len(result.edges) >= 2
        edge_targets = [e.target_id for e in result.edges]
        assert "os.py" in edge_targets or any("os" in t for t in edge_targets)

    def test_supported_extensions(self):
        parser = PythonParser()
        assert ".py" in parser.supported_extensions()
        assert ".pyi" in parser.supported_extensions()
        assert ".js" not in parser.supported_extensions()

    def test_can_parse(self):
        parser = PythonParser()
        assert parser.can_parse(Path("test.py")) is True
        assert parser.can_parse(Path("test.js")) is False

    def test_grammar_version(self):
        parser = PythonParser()
        assert parser.grammar_version() == "regex-1.0"

    def test_file_hash(self):
        parser = PythonParser()
        h1 = parser.file_hash("hello")
        h2 = parser.file_hash("hello")
        h3 = parser.file_hash("world")
        assert h1 == h2
        assert h1 != h3

    def test_parse_empty_file(self):
        parser = PythonParser()
        result = parser.parse(Path("empty.py"), "")
        assert result.completeness == "complete"
        assert result.is_valid() is True
        # Should still have module symbol
        assert len(result.symbols) >= 1

    def test_parse_file_with_syntax_error(self):
        parser = PythonParser()
        content = "def foo(\n  # unclosed paren"
        result = parser.parse(Path("bad.py"), content)
        # Regex parser doesn't fail on syntax errors
        assert result.completeness == "complete"

    def test_exported_symbols(self):
        parser = PythonParser()
        content = "def public_func():\n    pass\n\ndef _private_func():\n    pass\n"
        result = parser.parse(Path("test.py"), content)
        public = [s for s in result.symbols if s.name == "public_func"]
        private = [s for s in result.symbols if s.name == "_private_func"]
        assert public[0].exported is True
        assert private[0].exported is False


class TestLanguageParserInterface:
    def test_abstract_methods(self):
        # LanguageParser should not be instantiable
        with pytest.raises(TypeError):
            LanguageParser()

    def test_python_parser_is_language_parser(self):
        parser = PythonParser()
        assert isinstance(parser, LanguageParser)