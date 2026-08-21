"""Minimal SQLite infrastructure used by domain-owned repositories.

This module deliberately knows nothing about quotes, quantitative features, or
financial reports.  Table schemas and queries live in their owning domains.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from utils.logger import get_logger

_log = get_logger(__name__)


def default_db_path() -> Path:
    """Return the shared SQLite file used by the application.

    The existing location is retained so the architecture migration does not
    destroy or silently abandon historical data.
    """

    return Path(__file__).resolve().parents[1] / "database" / "stock_data.db"


class SQLiteRepository:
    """Connection lifecycle and schema helpers for a domain repository."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        try:
            self.cursor.execute("PRAGMA journal_mode=DELETE")
            self.cursor.fetchall()
        except sqlite3.Error:
            pass

    def close(self) -> None:
        if self.connection is None:
            return
        try:
            self.connection.commit()
            self.connection.close()
        finally:
            self.connection = None
            self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None and self.connection is not None:
            self.connection.commit()
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def ensure_table(
        self,
        table: str,
        columns: Mapping[str, str],
        primary_key: Sequence[str],
        indexes: Iterable[tuple[str, Sequence[str]]] = (),
    ) -> None:
        """Create a table, add newly declared columns, and create indexes."""

        cols_sql = ", ".join(f"{name} {decl}" for name, decl in columns.items())
        pk_sql = ", ".join(primary_key)
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table} "
            f"({cols_sql}, PRIMARY KEY ({pk_sql}))"
        )
        self.cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in self.cursor.fetchall()}
        for name, declaration in columns.items():
            if name in existing:
                continue
            type_only = declaration.split()[0]
            self.cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {name} {type_only}"
            )
            _log.info("schema migration: add %s.%s", table, name)
        for index_name, index_columns in indexes:
            joined = ", ".join(index_columns)
            self.cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({joined})"
            )
        self.connection.commit()

    def upsert(self, table: str, row: Mapping[str, object]) -> None:
        if not row:
            return
        keys = list(row)
        placeholders = ",".join("?" for _ in keys)
        updates = ",".join(f"{key}=excluded.{key}" for key in keys)
        self.cursor.execute(
            f"INSERT INTO {table} ({','.join(keys)}) VALUES ({placeholders}) "
            f"ON CONFLICT DO UPDATE SET {updates}",
            [row[key] for key in keys],
        )
        self.connection.commit()

    def upsert_many(self, table: str, rows: Sequence[Mapping[str, object]]) -> None:
        if not rows:
            return
        keys = list(rows[0])
        placeholders = ",".join("?" for _ in keys)
        updates = ",".join(f"{key}=excluded.{key}" for key in keys)
        self.cursor.executemany(
            f"INSERT INTO {table} ({','.join(keys)}) VALUES ({placeholders}) "
            f"ON CONFLICT DO UPDATE SET {updates}",
            [[row.get(key) for key in keys] for row in rows],
        )
        self.connection.commit()

    def scalar(self, sql: str, params: Sequence[object] = ()):
        row = self.cursor.execute(sql, params).fetchone()
        return row[0] if row else None
