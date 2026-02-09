import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "complaints.db"


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def init_db() -> None:
    orders = load_json(BASE_DIR / "orders.json")
    complaints = load_json(BASE_DIR / "complaints.json")
    policies = load_json(BASE_DIR / "policies.json")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                items TEXT NOT NULL,
                status TEXT NOT NULL,
                delivered_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                complaint_type TEXT NOT NULL,
                resolution TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                scenario TEXT NOT NULL,
                default_resolution TEXT NOT NULL
            )
            """
        )

        cur.execute("DELETE FROM orders")
        cur.execute("DELETE FROM complaints")
        cur.execute("DELETE FROM policies")

        cur.executemany(
            "INSERT INTO orders (order_id, items, status, delivered_at) VALUES (?, ?, ?, ?)",
            [(o["order_id"], o["items"], o["status"], o["delivered_at"]) for o in orders],
        )
        cur.executemany(
            "INSERT INTO complaints (order_id, complaint_type, resolution, created_at) VALUES (?, ?, ?, ?)",
            [
                (c["order_id"], c["complaint_type"], c["resolution"], c["created_at"])
                for c in complaints
            ],
        )
        cur.executemany(
            "INSERT INTO policies (policy_id, scenario, default_resolution) VALUES (?, ?, ?)",
            [
                (p["policy_id"], p["scenario"], p["default_resolution"])
                for p in policies
            ],
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
