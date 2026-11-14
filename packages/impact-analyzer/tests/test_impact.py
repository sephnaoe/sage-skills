"""Tests for impact_analyzer — including edge cases."""

import tempfile
from pathlib import Path

from impact_analyzer import ImpactAnalyzer


def test_analyze_empty_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        analyzer = ImpactAnalyzer(project_root=root)
        result = analyzer.analyze(["src/nonexistent.py"])
        assert result.changed_files == ["src/nonexistent.py"]
        assert result.affected_tests == []
        assert result.confidence == "low"


def test_get_all_tests():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "tests").mkdir()
        (root / "tests" / "test_example.py").write_text("def test_x(): pass")
        analyzer = ImpactAnalyzer(project_root=root)
        tests = analyzer.get_all_tests()
        assert "tests/test_example.py" in tests


def test_analyze_empty_file_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        analyzer = ImpactAnalyzer(project_root=root)
        result = analyzer.analyze([])
        assert result.changed_files == []
        assert result.affected_tests == []
        assert result.confidence == "low"


def test_circular_import_handling():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        tests = root / "tests"
        src.mkdir()
        tests.mkdir()
        (src / "a.py").write_text("from b import x\n")
        (src / "b.py").write_text("from a import y\n")
        (tests / "test_a.py").write_text("from a import z\n")
        analyzer = ImpactAnalyzer(project_root=root)
        result = analyzer.analyze(["src/a.py"])
        assert isinstance(result.affected_tests, list)


def test_missing_file_graceful():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        analyzer = ImpactAnalyzer(project_root=root)
        result = analyzer.analyze(["src/missing.py"])
        assert result.changed_files == ["src/missing.py"]
        assert result.confidence == "low"
        assert len(result.coverage_gaps) > 0


def test_large_file_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        tests = root / "tests"
        src.mkdir()
        tests.mkdir()
        files = []
        for i in range(50):
            (src / f"mod{i}.py").write_text(f"# module {i}\n")
            (tests / f"test_mod{i}.py").write_text(f"from src.mod{i} import x\n")
            files.append(f"src/mod{i}.py")
        analyzer = ImpactAnalyzer(project_root=root)
        result = analyzer.analyze(files)
        assert len(result.affected_tests) > 0
        assert result.confidence in ("high", "medium", "low")