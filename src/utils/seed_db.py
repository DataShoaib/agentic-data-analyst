"""Creates data/sample.db with a small sales dataset so the demo works
out of the box. Run: python -m src.utils.seed_db
"""
import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "data/sample.db"

PRODUCTS = ["Laptop", "Phone", "Headphones", "Keyboard", "Monitor", "Webcam", "Tablet"]
REGIONS = ["North", "South", "East", "West"]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS sales")
    conn.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            sale_date TEXT,
            product TEXT,
            region TEXT,
            quantity INTEGER,
            revenue REAL
        )
    """)

    start = date(2025, 1, 1)
    rows = []
    for i in range(500):
        d = start + timedelta(days=random.randint(0, 400))
        product = random.choice(PRODUCTS)
        region = random.choice(REGIONS)
        qty = random.randint(1, 20)
        unit_price = {"Laptop": 55000, "Phone": 25000, "Headphones": 2000,
                      "Keyboard": 1500, "Monitor": 12000, "Webcam": 2500,
                      "Tablet": 18000}[product]
        revenue = qty * unit_price
        rows.append((d.isoformat(), product, region, qty, revenue))

    conn.executemany(
        "INSERT INTO sales (sale_date, product, region, quantity, revenue) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Seeded {len(rows)} rows into {DB_PATH}")


if __name__ == "__main__":
    seed()
