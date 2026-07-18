"""SQL Agent — converts natural language into one OR MORE SQL queries.

Handles 3 cases:
1. Single specific question -> 1 query
2. Multi-part question ("X and also Y") -> multiple queries, one per part
3. Open-ended business/marketing request ("give me key insights") ->
   the LLM proactively decides 3-5 useful exploratory queries on its own
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.sql_tools import run_sql_query, is_unsafe_sql, get_schema_summary
from src.graph.state import AgentState

SQL_SYSTEM_PROMPT = """You are a SQL expert working with a sales database.

Given the schema and the user's question, decide:
- If it's ONE specific question, write exactly ONE SQL query.
- If the question has MULTIPLE distinct parts (e.g. "top 5 by revenue and
  also top 5 by quantity"), write ONE query per part.
- If the request is OPEN-ENDED or asks for general business/marketing
  insights (e.g. "give me important insights for marketing", "what should
  I know about my sales data", "help me understand my product performance"),
  proactively write 3-5 SQL queries covering different useful angles on
  your own judgment — for example: top products by revenue, revenue by
  region, monthly/seasonal trend, top and bottom performers, average order
  size. Choose the angles yourself based on what's in the schema.

Rules:
- Output ONLY SQL queries, nothing else — no explanation, no markdown fences.
- If writing multiple queries, separate each one with a line containing
  exactly: ---SPLIT---
- Always include every column used for ranking/aggregation in the SELECT
  list with a clear alias (e.g. SUM(revenue) AS total_revenue).
- Prefer SELECT queries. Only write DELETE/UPDATE/INSERT/DROP if the user
  explicitly asks to modify data.
- Use the exact table/column names from the schema below.

Schema:
{schema}
"""


def sql_agent_node(state: AgentState) -> dict:
    llm = get_llm()
    schema = get_schema_summary()
    user_question = state["messages"][-1].content
    trace = state.get("agent_trace") or []

    response = llm.invoke([
        SystemMessage(content=SQL_SYSTEM_PROMPT.format(schema=schema)),
        HumanMessage(content=user_question),
    ])
    raw = response.content.strip()

    queries = [
        q.strip().strip("```sql").strip("```").strip()
        for q in raw.split("---SPLIT---")
    ]
    queries = [q for q in queries if q]

    unsafe_queries = [q for q in queries if is_unsafe_sql(q)]

    if unsafe_queries:
        return {
            "sql_queries": queries,
            "generated_sql": unsafe_queries[0],
            "sql_is_safe": False,
            "requires_approval": True,
            "sql_done": True,
            "agent_trace": trace + ["🔍 SQL agent"],
        }

    results = []
    for q in queries:
        exec_result = run_sql_query(q)
        if exec_result["success"]:
            results.append({"sql": q, "rows": exec_result["rows"], "error": None})
        else:
            results.append({"sql": q, "rows": [], "error": exec_result["error"]})

    return {
        "sql_queries": queries,
        "generated_sql": "\n\n".join(queries),
        "sql_is_safe": True,
        "requires_approval": False,
        "query_results": results,
        "sql_done": True,
        "agent_trace": trace + ["🔍 SQL agent"],
    }