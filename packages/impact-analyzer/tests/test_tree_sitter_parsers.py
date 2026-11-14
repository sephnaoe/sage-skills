"""Tests for tree-sitter-based parsers."""

from __future__ import annotations

from pathlib import Path

from sage.audit.parsers import PythonTreeSitterParser, JavaScriptParser, GoParser, RustParser


class TestPythonTreeSitterParser:
    def test_parse_simple_file(self):
        parser = PythonTreeSitterParser()
        content = "import os\nfrom pathlib import Path\ndef foo(): pass\nclass Bar: pass"
        result = parser.parse(Path("test.py"), content)
        assert result.file_info.language == "python"
        assert result.completeness == "complete"
        assert result.is_valid() is True
        symbol_names = [s.name for s in result.symbols]
        assert "foo" in symbol_names
        assert "Bar" in symbol_names

    def test_parse_imports(self):
        parser = PythonTreeSitterParser()
        content = "import os\nfrom pathlib import Path"
        result = parser.parse(Path("test.py"), content)
        assert len(result.edges) >= 2
        edge_targets = [e.target_id for e in result.edges]
        assert any("os" in t for t in edge_targets)

    def test_grammar_version(self):
        parser = PythonTreeSitterParser()
        assert "tree-sitter-python" in parser.grammar_version()

    def test_parse_empty_file(self):
        parser = PythonTreeSitterParser()
        result = parser.parse(Path("empty.py"), "")
        assert result.completeness == "complete"
        assert result.is_valid() is True

    def test_parse_syntax_error(self):
        parser = PythonTreeSitterParser()
        content = "def foo(\n  # unclosed"
        result = parser.parse(Path("bad.py"), content)
        assert result.completeness in ("complete", "partial")
        assert result.is_valid() is True

    def test_byte_offsets(self):
        parser = PythonTreeSitterParser()
        content = "import os"
        result = parser.parse(Path("test.py"), content)
        for edge in result.edges:
            assert "start_byte" in edge.evidence
            assert "end_byte" in edge.evidence
            assert edge.evidence["start_byte"] >= 0
            assert edge.evidence["end_byte"] > edge.evidence["start_byte"]


class TestJavaScriptParser:
    def test_parse_simple_file(self):
        parser = JavaScriptParser()
        content = "import { foo } from './foo';\nfunction bar() { return 1; }\nclass Baz { method() {} }"
        result = parser.parse(Path("test.js"), content)
        assert result.file_info.language == "javascript"
        assert result.completeness == "complete"
        assert result.is_valid() is True
        symbol_names = [s.name for s in result.symbols]
        assert "bar" in symbol_names
        assert "Baz" in symbol_names

    def test_parse_imports(self):
        parser = JavaScriptParser()
        content = "import { foo } from './foo';\nconst bar = require('./bar');"
        result = parser.parse(Path("test.js"), content)
        assert len(result.edges) >= 1
        edge_targets = [e.target_id for e in result.edges]
        assert any("./foo" in t or "./bar" in t for t in edge_targets)

    def test_supported_extensions(self):
        parser = JavaScriptParser()
        assert ".js" in parser.supported_extensions()
        assert ".jsx" in parser.supported_extensions()
        assert ".py" not in parser.supported_extensions()

    def test_typescript_parser(self):
        parser = JavaScriptParser(is_typescript=True)
        assert parser.language_name() == "typescript"
        assert ".ts" in parser.supported_extensions()

    def test_grammar_version(self):
        parser = JavaScriptParser()
        assert "tree-sitter-javascript" in parser.grammar_version()


class TestGoParser:
    def test_parse_simple_file(self):
        parser = GoParser()
        content = 'package main\nimport "fmt"\nfunc main() { fmt.Println("hello") }\ntype Foo struct { Bar int }'
        result = parser.parse(Path("test.go"), content)
        assert result.file_info.language == "go"
        assert result.completeness in ("complete", "partial")
        assert result.is_valid() is True
        symbol_names = [s.name for s in result.symbols]
        assert "main" in symbol_names
        assert "Foo" in symbol_names

    def test_parse_imports(self):
        parser = GoParser()
        content = 'package main\nimport "fmt"'
        result = parser.parse(Path("test.go"), content)
        assert len(result.edges) >= 1
        edge_targets = [e.target_id for e in result.edges]
        assert "fmt" in edge_targets

    def test_supported_extensions(self):
        parser = GoParser()
        assert ".go" in parser.supported_extensions()
        assert ".py" not in parser.supported_extensions()

    def test_exported_symbols(self):
        parser = GoParser()
        content = 'package main\nfunc PublicFunc() {}\nfunc privateFunc() {}'
        result = parser.parse(Path("test.go"), content)
        public = [s for s in result.symbols if s.name == "PublicFunc"]
        private = [s for s in result.symbols if s.name == "privateFunc"]
        assert public[0].exported is True
        assert private[0].exported is False

    def test_grammar_version(self):
        parser = GoParser()
        assert "tree-sitter-go" in parser.grammar_version()


class TestRustParser:
    def test_parse_simple_file(self):
        parser = RustParser()
        content = 'use std::io;\nfn main() { println!("hello"); }\nstruct Foo { bar: i32 }\nenum Color { Red, Green }'
        result = parser.parse(Path("test.rs"), content)
        assert result.file_info.language == "rust"
        assert result.completeness == "complete"
        assert result.is_valid() is True
        symbol_names = [s.name for s in result.symbols]
        assert "main" in symbol_names
        assert "Foo" in symbol_names
        assert "Color" in symbol_names

    def test_parse_imports(self):
        parser = RustParser()
        content = 'use std::io;'
        result = parser.parse(Path("test.rs"), content)
        assert len(result.edges) >= 1
        edge_targets = [e.target_id for e in result.edges]
        assert any("std" in t for t in edge_targets)

    def test_supported_extensions(self):
        parser = RustParser()
        assert ".rs" in parser.supported_extensions()
        assert ".py" not in parser.supported_extensions()

    def test_grammar_version(self):
        parser = RustParser()
        assert "tree-sitter-rust" in parser.grammar_version()

    def test_parse_traits(self):
        parser = RustParser()
        content = 'trait Drawable { fn draw(&self); }'
        result = parser.parse(Path("test.rs"), content)
        symbol_names = [s.name for s in result.symbols]
        assert "Drawable" in symbol_names


class TestLanguageParserInterface:
    def test_abstract_methods(self):
        from sage.audit.parsers.base import LanguageParser
        with __import__('pytest').raises(TypeError):
            LanguageParser()

    def test_all_parsers_are_language_parsers(self):
        from sage.audit.parsers.base import LanguageParser
        for parser_cls in [PythonTreeSitterParser, JavaScriptParser, GoParser, RustParser]:
            assert issubclass(parser_cls, LanguageParser)