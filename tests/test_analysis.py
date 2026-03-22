"""
BetonLab - Temel testler
pytest tests/ komutuyla çalıştırın
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from analysis import GradeAnalyzer, PollutionAnalyzer


def test_sieve_analysis_uygun():
    analyzer = GradeAnalyzer()
    result = analyzer.evaluate("0-5", {
        "0.063": 5, "0.125": 12, "0.25": 22, "0.5": 38,
        "1": 50, "2": 68, "4": 90, "5.6": 97
    })
    assert result["status"] == "UYGUN"


def test_sieve_analysis_uygunsuz():
    analyzer = GradeAnalyzer()
    result = analyzer.evaluate("0-5", {
        "0.063": 25, "0.125": 40, "0.25": 60,  # Limit dışı
        "0.5": 38, "1": 50, "2": 68, "4": 90, "5.6": 97
    })
    assert result["status"] == "UYGUNSUZ"
    assert len(result["non_conformities"]) > 0


def test_unknown_aggregate_type():
    analyzer = GradeAnalyzer()
    result = analyzer.evaluate("99-999", {"1": 50})
    assert result["status"] == "BİLİNMEYEN"


def test_pollution_uygun():
    class MockData:
        aggregate_type = "0-5"
        bypass_open = False
        washing_water_dirty = False
        washing_water_insufficient = False
        mb_value = 0.6
        sand_equivalent = 75
        fine_content = 5.0
        clay_lumps = 0.1

    analyzer = PollutionAnalyzer()
    result = analyzer.evaluate(MockData())
    assert result["status"] == "UYGUN"


def test_pollution_bypass_open():
    class MockData:
        aggregate_type = "0-5"
        bypass_open = True
        washing_water_dirty = False
        washing_water_insufficient = False
        mb_value = 0.5
        sand_equivalent = 80
        fine_content = 3.0
        clay_lumps = 0.1

    analyzer = PollutionAnalyzer()
    result = analyzer.evaluate(MockData())
    assert result["status"] == "UYGUNSUZ"
    assert any("Baypas" in nc for nc in result["non_conformities"])


def test_pollution_mb_exceeded():
    class MockData:
        aggregate_type = "0-5"
        bypass_open = False
        washing_water_dirty = False
        washing_water_insufficient = False
        mb_value = 1.5  # Limit: 1.0
        sand_equivalent = 75
        fine_content = 5.0
        clay_lumps = 0.1

    analyzer = PollutionAnalyzer()
    result = analyzer.evaluate(MockData())
    assert result["status"] == "UYGUNSUZ"


def test_sieve_limits_all_types():
    analyzer = GradeAnalyzer()
    limits = analyzer.get_all_limits()
    assert "sieve_limits" in limits
    assert "0-5" in limits["sieve_limits"]
    assert "5-12" in limits["sieve_limits"]
    assert "12-22" in limits["sieve_limits"]


def test_database_operations(tmp_path):
    from database import DatabaseManager
    db = DatabaseManager(str(tmp_path / "test.db"))
    counts = db.get_record_counts()
    assert counts["sieve_analyses"] == 0
    assert counts["pollution_tests"] == 0
