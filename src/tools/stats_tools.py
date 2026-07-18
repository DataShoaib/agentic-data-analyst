"""Lightweight statistical helpers used by the Analysis Agent."""
import pandas as pd


def summarize_dataframe(rows: list[dict]) -> str:
    """Returns a human-readable statistical summary of query results."""
    if not rows:
        return "No rows returned — nothing to analyze."

    df = pd.DataFrame(rows)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    summary_parts = [f"Rows: {len(df)}, Columns: {list(df.columns)}"]

    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        summary_parts.append(f"Numeric summary:\n{desc.to_string()}")

        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr().round(2)
            summary_parts.append(f"Correlation matrix:\n{corr.to_string()}")

    return "\n\n".join(summary_parts)
