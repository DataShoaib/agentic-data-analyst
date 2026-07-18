"""Persistent conversation memory using LangGraph's SqliteSaver.

Why this matters for the interview: without a checkpointer, every message
is stateless. With it, a user can say "now break that down by region" and
the graph resumes with full prior context — and it survives a server
restart, unlike an in-memory dict.
"""
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from src.config import CHECKPOINT_DB_PATH


def get_checkpointer():
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)
