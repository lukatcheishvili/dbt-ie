"""
Append new website sessions to my_database.duckdb.

Inserts synthetic sessions for N days immediately after the current
max session_date so that a subsequent incremental dbt run processes
only the new data.

Usage:
    uv run python add_sessions.py              # 3 new days, ~40 sessions/day
    uv run python add_sessions.py --days 5     # 5 new days
    uv run python add_sessions.py --per-day 80 # denser traffic
    uv run python add_sessions.py --database other.duckdb
"""

import argparse
import random
import uuid
from datetime import date, timedelta

import duckdb

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
SOURCES = ["direct", "email", "facebook", "google", "instagram", "referral"]
LANDING_PAGES = ["/", "/products", "/categories", "/cart", "/search", "/checkout"]


def _random_ip() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def _generate_sessions(start_date: date, days: int, per_day: int) -> list[tuple]:
    rows = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        count = random.randint(max(1, per_day - 10), per_day + 10)
        for _ in range(count):
            h = random.randint(0, 23)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            session_date = f"{day} {h:02d}:{m:02d}:{s:02d}"
            is_bounce = random.random() < 0.35
            rows.append((
                str(uuid.uuid4()),
                random.choice([None, random.randint(1, 500)]),
                session_date,
                random.choice(DEVICE_TYPES),
                random.choice(BROWSERS),
                random.choice(SOURCES),
                random.choice(LANDING_PAGES),
                1 if is_bounce else random.randint(2, 20),
                random.randint(5, 90) if is_bounce else random.randint(60, 3600),
                is_bounce,
                False if is_bounce else random.random() < 0.12,
                _random_ip(),
            ))
    return rows


def add_sessions(db_path: str, days: int, per_day: int) -> None:
    conn = duckdb.connect(db_path)
    try:
        max_date = conn.execute(
            "select max(cast(session_date as date)) from main.website_sessions"
        ).fetchone()[0]
        start_date = max_date + timedelta(days=1)

        rows = _generate_sessions(start_date, days, per_day)

        conn.executemany(
            "insert into main.website_sessions values (?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )

        print(f"Added {len(rows)} sessions across {days} new day(s):")
        for offset in range(days):
            day = start_date + timedelta(days=offset)
            n = sum(1 for r in rows if r[2].startswith(str(day)))
            print(f"  {day}  →  {n} sessions")

        new_max = conn.execute(
            "select max(cast(session_date as date)) from main.website_sessions"
        ).fetchone()[0]
        total = conn.execute(
            "select count(*) from main.website_sessions"
        ).fetchone()[0]
        print()
        print(f"max session_date : {new_max}")
        print(f"total rows       : {total:,}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Append new website sessions beyond the current max date."
    )
    parser.add_argument("--days", "-d", type=int, default=3,
                        help="Number of new days to generate (default: 3)")
    parser.add_argument("--per-day", "-n", type=int, default=40,
                        help="Approximate sessions per day (default: 40)")
    parser.add_argument("--database", type=str, default="my_database.duckdb",
                        help="Path to the DuckDB file (default: my_database.duckdb)")
    args = parser.parse_args()
    add_sessions(args.database, args.days, args.per_day)
