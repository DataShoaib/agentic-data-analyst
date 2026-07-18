"""Unit tests for the tools layer — run offline, no LLM calls needed."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.sql_tools import is_unsafe_sql
from src.tools.stats_tools import summarize_dataframe
from src.tools.viz_tools import generate_chart


def test_is_unsafe_sql_detects_delete():
    assert is_unsafe_sql("DELETE FROM sales WHERE id = 1") is True


def test_is_unsafe_sql_allows_select():
    assert is_unsafe_sql("SELECT * FROM sales LIMIT 10") is False


def test_is_unsafe_sql_case_insensitive():
    assert is_unsafe_sql("drop table sales") is True


def test_summarize_dataframe_empty():
    result = summarize_dataframe([])
    assert "No rows" in result


def test_summarize_dataframe_basic():
    rows = [{"product": "Laptop", "revenue": 1000}, {"product": "Phone", "revenue": 2000}]
    result = summarize_dataframe(rows)
    assert "Rows: 2" in result


def test_generate_chart_empty_returns_blank():
    assert generate_chart([]) == ""


def test_generate_chart_creates_file():
    rows = [{"product": "Laptop", "revenue": 1000}, {"product": "Phone", "revenue": 2000}]
    path = generate_chart(rows, chart_type="bar")
    assert path.endswith(".png")
    assert os.path.exists(path)
    os.remove(path)
