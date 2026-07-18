"""Tests for supervisor routing logic — pure function, no LLM/network needed."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.supervisor import supervisor_node


def test_routes_to_sql_agent_first():
    state = {"messages": [], "generated_sql": None}
    result = supervisor_node(state)
    assert result["next_agent"] == "sql_agent"


def test_routes_to_analysis_after_query_result():
    state = {"generated_sql": "SELECT 1", "query_result": [{"a": 1}], "insights": None}
    result = supervisor_node(state)
    assert result["next_agent"] == "analysis_agent"


def test_routes_to_viz_after_insights():
    state = {
        "generated_sql": "SELECT 1", "query_result": [{"a": 1}],
        "insights": "some insight", "chart_path": None,
    }
    result = supervisor_node(state)
    assert result["next_agent"] == "viz_agent"


def test_routes_to_end_on_error():
    state = {"query_error": "boom"}
    result = supervisor_node(state)
    assert result["next_agent"] == "end"


def test_routes_to_end_when_complete():
    state = {
        "generated_sql": "SELECT 1", "query_result": [{"a": 1}],
        "insights": "x", "chart_path": "chart.png", "final_report": "done",
    }
    result = supervisor_node(state)
    assert result["next_agent"] == "end"
