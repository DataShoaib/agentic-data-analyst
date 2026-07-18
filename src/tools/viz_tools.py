"""Chart generation for the Viz Agent. Saves PNGs so the UI can display them."""
import os
import uuid
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless rendering — no display needed on server
import matplotlib.pyplot as plt

CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)


def generate_chart(rows: list[dict], chart_type: str = "bar") -> str:
    if not rows:
        return None          # 👈 badlo: "" ki jagah None

    df = pd.DataFrame(rows)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    label_col = next((c for c in df.columns if c not in numeric_cols), df.columns[0])

    if not numeric_cols:
        return None          # 👈 badlo: "" ki jagah None

    value_col = numeric_cols[0]
    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "line":
        ax.plot(df[label_col], df[value_col], marker="o")
    elif chart_type == "pie":
        ax.pie(df[value_col], labels=df[label_col], autopct="%1.1f%%")
    else:
        ax.bar(df[label_col], df[value_col])
        plt.xticks(rotation=45, ha="right")

    ax.set_title(f"{value_col} by {label_col}")
    plt.tight_layout()

    filename = f"{CHART_DIR}/chart_{uuid.uuid4().hex[:8]}.png"
    fig.savefig(filename)
    plt.close(fig)
    return filename
