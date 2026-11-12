"""Persistent reservations for metered local model calls, in microdollars."""

import sqlite3
from contextlib import closing
from pathlib import Path


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, path: Path, limit: int | None = None):
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0):
            raise ValueError("budget limit must be a positive integer")
        self.path = path
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS config (limit_amount INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, provider TEXT NOT NULL, amount INTEGER NOT NULL, status TEXT NOT NULL)")
            row = db.execute("SELECT limit_amount FROM config").fetchone()
            if row is None:
                limit = limit if limit is not None else 2_000_000
                db.execute("INSERT INTO config VALUES (?)", (limit,))
            elif limit is not None and row[0] != limit:
                db.rollback()
                raise ValueError("budget limit differs from existing ledger")
            db.commit()

    @property
    def limit(self) -> int:
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT limit_amount FROM config").fetchone()[0]

    def set_limit(self, limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("budget limit must be a positive integer")
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE config SET limit_amount = ?", (limit,))
            db.commit()

    def reserve(self, provider: str, amount: int) -> int:
        if not provider or isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("a provider and positive reservation are required")
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            total = db.execute("SELECT COALESCE(SUM(amount), 0) FROM calls").fetchone()[0]
            limit = db.execute("SELECT limit_amount FROM config").fetchone()[0]
            if total + amount > limit:
                db.rollback()
                raise BudgetExceeded("reservation exceeds remaining budget")
            cursor = db.execute("INSERT INTO calls (provider, amount, status) VALUES (?, ?, 'reserved')", (provider, amount))
            db.commit()
            return cursor.lastrowid

    def total(self) -> int:
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT COALESCE(SUM(amount), 0) FROM calls").fetchone()[0]

    def calls(self):
        with closing(sqlite3.connect(self.path)) as db:
            return [{"id": row[0], "provider": row[1], "amount_microdollars": row[2], "status": row[3]}
                    for row in db.execute("SELECT id, provider, amount, status FROM calls ORDER BY id")]

    def settle(self, reservation: int, actual: int) -> None:
        if isinstance(actual, bool) or not isinstance(actual, int) or actual < 0:
            raise ValueError("actual amount must be a nonnegative integer")
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT amount, status FROM calls WHERE id = ?", (reservation,)).fetchone()
            if row is None or row[1] != "reserved":
                db.rollback()
                raise ValueError("invalid settlement")
            db.execute("UPDATE calls SET amount = ?, status = 'settled' WHERE id = ?", (actual, reservation))
            db.commit()
