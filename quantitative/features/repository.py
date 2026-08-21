"""Persistence owned by the quantitative feature domain."""

from __future__ import annotations

from pathlib import Path

from infrastructure.sqlite import SQLiteRepository

from .catalog import FEATURE_KEYS
from .models import FeatureSnapshot


class FeatureRepository(SQLiteRepository):
    """Persist one complete feature snapshot per symbol and trading date."""

    TABLE = "quant_feature_daily"

    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)
        columns = {
            "Symbol": "TEXT NOT NULL",
            "Date": "DATE NOT NULL",
            "FeatureVersion": "INTEGER NOT NULL DEFAULT 1",
            **{key: "REAL" for key in FEATURE_KEYS},
        }
        self.ensure_table(
            self.TABLE,
            columns,
            primary_key=("Symbol", "Date"),
            indexes=(("idx_quant_feature_daily_date", ("Date",)),),
        )

    @staticmethod
    def _value(value):
        return round(float(value), 8) if value is not None else None

    def _to_row(self, snapshot: FeatureSnapshot) -> dict:
        return {
            "Symbol": snapshot.symbol,
            "Date": snapshot.date,
            "FeatureVersion": 1,
            **{
                key: self._value(snapshot.get(key))
                for key in FEATURE_KEYS
            },
        }

    def save(self, snapshot: FeatureSnapshot) -> None:
        self.upsert(self.TABLE, self._to_row(snapshot))

    def save_many(self, snapshots: list[FeatureSnapshot]) -> None:
        self.upsert_many(self.TABLE, [self._to_row(item) for item in snapshots])

    def latest_date(self, symbol: str) -> str | None:
        return self.scalar(
            f"SELECT MAX(Date) FROM {self.TABLE} WHERE Symbol=?", (symbol,)
        )

    def count(self, symbol: str) -> int:
        return int(
            self.scalar(
                f"SELECT COUNT(*) FROM {self.TABLE} WHERE Symbol=?", (symbol,)
            )
            or 0
        )

    def get_range(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[FeatureSnapshot]:
        sql = (
            f"SELECT Date,{','.join(FEATURE_KEYS)} FROM {self.TABLE} "
            "WHERE Symbol=?"
        )
        params: list[object] = [symbol]
        if start_date:
            sql += " AND Date>=?"
            params.append(start_date)
        if end_date:
            sql += " AND Date<=?"
            params.append(end_date)
        sql += " ORDER BY Date ASC"
        snapshots = []
        for row in self.cursor.execute(sql, params).fetchall():
            snapshots.append(
                FeatureSnapshot(
                    symbol=symbol,
                    date=str(row[0]),
                    values={
                        key: (float(row[index]) if row[index] is not None else None)
                        for index, key in enumerate(FEATURE_KEYS, start=1)
                    },
                )
            )
        return snapshots

    def cross_section_rank(
        self,
        feature: str,
        date: str,
        top_n: int = 50,
        ascending: bool = False,
    ) -> list[tuple[str, float]]:
        if feature not in FEATURE_KEYS:
            raise ValueError(f"unknown feature: {feature}")
        order = "ASC" if ascending else "DESC"
        rows = self.cursor.execute(
            f"SELECT Symbol,{feature} FROM {self.TABLE} "
            f"WHERE Date=? AND {feature} IS NOT NULL "
            f"ORDER BY {feature} {order} LIMIT ?",
            (date, top_n),
        ).fetchall()
        return [(str(row[0]), float(row[1])) for row in rows]

    def delete_symbol(self, symbol: str) -> int:
        cursor = self.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE Symbol=?", (symbol,)
        )
        self.connection.commit()
        return max(cursor.rowcount, 0)


__all__ = ["FeatureRepository"]
