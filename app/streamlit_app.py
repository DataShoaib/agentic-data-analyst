"""Streamlit chat UI for the Agentic Data Analyst. Talks to the FastAPI backend."""
import streamlit as st
import httpx
import uuid
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Agentic Data Analyst", page_icon="🤖", layout="wide")


def load_history(thread_id: str) -> list[dict]:
    try:
        resp = httpx.get(f"{API_URL}/history/{thread_id}", timeout=15)
        if resp.status_code == 200:
            return resp.json().get("messages", [])
    except Exception as e:
        st.error(f"Could not load history: {e}")
    return []


def fetch_all_threads() -> list[dict]:
    try:
        resp = httpx.get(f"{API_URL}/threads", timeout=15)
        if resp.status_code == 200:
            return resp.json().get("threads", [])
    except Exception as e:
        st.error(f"Could not load thread list: {e}")
    return []


# ---- Read thread_id from URL ----
raw_thread_param = st.query_params.get("thread", None)
if isinstance(raw_thread_param, list):
    raw_thread_param = raw_thread_param[0] if raw_thread_param else None

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "all_threads_loaded" not in st.session_state:
    st.session_state.all_threads_loaded = fetch_all_threads()

if "active_thread" not in st.session_state:
    if raw_thread_param:
        active_id = raw_thread_param
        restored_messages = load_history(active_id)
        title = restored_messages[0]["content"][:30] + "..." if restored_messages else "New Chat"
        st.session_state.conversations[active_id] = {"title": title, "messages": restored_messages}
        st.session_state.active_thread = active_id
    else:
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.active_thread = new_id
        st.query_params["thread"] = new_id

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

with st.sidebar:
    st.header("💬 Conversations")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.active_thread = new_id
        st.query_params["thread"] = new_id
        st.rerun()

    st.divider()

    # Threads already touched in THIS session
    for tid, convo in st.session_state.conversations.items():
        if st.button(convo["title"], key=f"switch_{tid}", use_container_width=True):
            st.session_state.active_thread = tid
            st.query_params["thread"] = tid
            st.rerun()

    # Past threads from previous sessions — not yet loaded into memory
    st.divider()
    st.caption("📜 Past conversations")
    for t in st.session_state.all_threads_loaded:
        tid = t["thread_id"]
        if tid in st.session_state.conversations:
            continue  # already shown above
        if st.button(f"🕘 {t['title']}", key=f"old_{tid}", use_container_width=True):
            restored = load_history(tid)
            title = restored[0]["content"][:30] + "..." if restored else "Untitled"
            st.session_state.conversations[tid] = {"title": title, "messages": restored}
            st.session_state.active_thread = tid
            st.query_params["thread"] = tid
            st.rerun()

active_id = st.session_state.active_thread
active_convo = st.session_state.conversations[active_id]

st.title("🤖 Agentic Data Analyst Co-Pilot")
st.caption(f"Thread: `{active_id}`")

for msg in active_convo["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        charts = msg.get("charts") or []
        if charts:
            cols = st.columns(min(len(charts), 3))
            for i, chart_path in enumerate(charts):
                with cols[i % len(cols)]:
                    st.image(chart_path)
        if msg.get("trace"):
            st.caption("🔧 Agents used: " + " → ".join(msg["trace"]))

if st.session_state.pending_approval and st.session_state.pending_approval["thread"] == active_id:
    sql = st.session_state.pending_approval["sql"]
    st.warning(f"⚠️ Approval needed:\n```sql\n{sql}\n```")
    col1, col2 = st.columns(2)

    if col1.button("✅ Approve"):
        resp = httpx.post(f"{API_URL}/resume", json={"decision": "approve", "thread_id": active_id}, timeout=60)
        data = resp.json()
        active_convo["messages"].append({
            "role": "assistant",
            "content": data.get("report") or "No report returned.",
            "charts": data.get("chart_paths", []),
            "trace": data.get("agent_trace", []),
        })
        st.session_state.pending_approval = None
        st.rerun()

    if col2.button("❌ Deny"):
        resp = httpx.post(f"{API_URL}/resume", json={"decision": "deny", "thread_id": active_id}, timeout=60)
        data = resp.json()
        active_convo["messages"].append({
            "role": "assistant",
            "content": data.get("report") or "Query denied.",
            "trace": data.get("agent_trace", []),
        })
        st.session_state.pending_approval = None
        st.rerun()

if prompt := st.chat_input("e.g. give me all important info for marketing"):
    active_convo["messages"].append({"role": "user", "content": prompt})

    if active_convo["title"] == "New Chat":
        active_convo["title"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Agents at work..."):
        resp = httpx.post(f"{API_URL}/chat", json={"message": prompt, "thread_id": active_id}, timeout=90)
        if resp.status_code != 200:
            active_convo["messages"].append({
                "role": "assistant",
                "content": f"⚠️ Server error ({resp.status_code}). Check the backend terminal for details.",
            })
            st.rerun()
        data = resp.json()

    if data["status"] == "awaiting_approval":
        sql = data["interrupt"][0]["value"]["sql"]
        st.session_state.pending_approval = {"thread": active_id, "sql": sql}
    else:
        active_convo["messages"].append({
            "role": "assistant",
            "content": data.get("report") or "No report returned.",
            "charts": data.get("chart_paths", []),
            "trace": data.get("agent_trace", []),
        })

    st.rerun()