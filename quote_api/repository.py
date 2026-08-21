"""Persistence owned by the market-data domain."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from infrastructure.sqlite import SQLiteRepository
from quote_api.quote_base import DailyQuote
from utils.data_types import DataValue


class MarketDataRepository(SQLiteRepository):
    """Store and query normalized daily quotes.

    The repository owns only market-data tables. Quantitative features and
    financial reports are intentionally handled by their own domains.
    """

    TABLE = "kline_daily"
    COLUMNS = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "Open": "REAL",
        "Close": "REAL",
        "High": "REAL",
        "Low": "REAL",
        "Volume": "REAL",
        "Turnover": "REAL",
        "TurnoverRate": "REAL",
    }
    SELECT_COLUMNS = (
        "Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate"
    )

    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)
        self.ensure_table(
            self.TABLE,
            self.COLUMNS,
            primary_key=("Symbol", "Date"),
            indexes=(("idx_kline_daily_date", ("Date",)),),
        )

    @staticmethod
    def _round(value, precision: int = 4):
        try:
            return round(float(value), precision)
        except (TypeError, ValueError):
            return value

    def _to_row(self, symbol: str, quote: DailyQuote) -> dict:
        return {
            "Symbol": symbol,
            "Date": quote.date,
            "Open": self._round(quote.open),
            "Close": self._round(quote.close),
            "High": self._round(quote.high),
            "Low": self._round(quote.low),
            "Volume": quote.volume,
            "Turnover": self._round(quote.turnover),
            "TurnoverRate": self._round(
                getattr(quote, "turnover_rate", 0.0), 6
            ),
        }

    @staticmethod
    def _to_quote(row, source: str = "db") -> DailyQuote:
        quote = DailyQuote()
        quote.date = str(row[0])
        quote.open = float(row[1] or 0.0)
        quote.close = float(row[2] or 0.0)
        quote.high = float(row[3] or 0.0)
        quote.low = float(row[4] or 0.0)
        quote.volume = float(row[5] or 0.0)
        quote.turnover = float(row[6] or 0.0)
        quote.turnover_rate = float(row[7] or 0.0)
        quote.source = source
        return quote

    def save(self, symbol: str, quote: DailyQuote) -> None:
        self.upsert(self.TABLE, self._to_row(symbol, quote))

    def save_many(self, symbol: str, quotes: list[DailyQuote]) -> None:
        self.upsert_many(self.TABLE, [self._to_row(symbol, q) for q in quotes])

    def latest_date(self, symbol: str) -> Optional[str]:
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

    def list_symbols(self) -> list[str]:
        rows = self.cursor.execute(
            f"SELECT DISTINCT Symbol FROM {self.TABLE} ORDER BY Symbol"
        ).fetchall()
        return [str(row[0]) for row in rows]

    def latest(self, symbol: str, size: int) -> list[DailyQuote]:
        rows = self.cursor.execute(
            f"SELECT {self.SELECT_COLUMNS} FROM {self.TABLE} "
            "WHERE Symbol=? ORDER BY Date DESC LIMIT ?",
            (symbol, size),
        ).fetchall()
        return [self._to_quote(row) for row in rows]

    def get_range(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[DailyQuote]:
        sql = f"SELECT {self.SELECT_COLUMNS} FROM {self.TABLE} WHERE Symbol=?"
        params: list[object] = [symbol]
        if start_date:
            sql += " AND Date>=?"
            params.append(start_date)
        if end_date:
            sql += " AND Date<=?"
            params.append(end_date)
        sql += " ORDER BY Date ASC"
        return [
            self._to_quote(row)
            for row in self.cursor.execute(sql, params).fetchall()
        ]

    def get_by_date(self, symbol: str, date: str) -> DailyQuote | None:
        row = self.cursor.execute(
            f"SELECT {self.SELECT_COLUMNS} FROM {self.TABLE} "
            "WHERE Symbol=? AND Date=? LIMIT 1",
            (symbol, date),
        ).fetchone()
        return self._to_quote(row) if row else None

    def delete_symbol(self, symbol: str) -> int:
        cursor = self.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE Symbol=?", (symbol,)
        )
        self.connection.commit()
        return max(cursor.rowcount, 0)

    def ratio_series(
        self, denominator_symbol: str, numerator_symbol: str
    ) -> list[DataValue]:
        rows = self.cursor.execute(
            f"""
            SELECT a.Date, a.Close * 1.0 / b.Close
            FROM {self.TABLE} a
            JOIN {self.TABLE} b ON a.Date=b.Date
            WHERE a.Symbol=? AND b.Symbol=? AND b.Close<>0
            ORDER BY a.Date ASC
            """,
            (denominator_symbol, numerator_symbol),
        ).fetchall()
        return [DataValue(str(row[0]), row[1]) for row in rows]


__all__ = ["MarketDataRepository"]
