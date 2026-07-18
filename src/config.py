"""Central configuration. Loads env vars and builds the LLM client once."""
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/sample.db")
CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "data/checkpoints.db")


def get_llm(temperature: float = 0.0):
    """Returns a chat model instance based on configured provider.

    Kept as a factory (not a module-level singleton) so tests can
    monkeypatch it easily.
    """
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=LLM_MODEL, temperature=temperature)
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=LLM_MODEL, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


# Keywords that trigger the Human-in-the-Loop guardrail before execution.
UNSAFE_SQL_KEYWORDS = ["DELETE", "DROP", "UPDATE", "ALTER", "TRUNCATE", "INSERT"]
