"""Persistence owned by the financial-report domain."""

from __future__ import annotations

from pathlib import Path

from infrastructure.sqlite import SQLiteRepository

from .field_mapping import UNIFIED_FIELDS
from .models import FinancialReport


class FinancialReportRepository(SQLiteRepository):
    TABLE = "financial_report"
    META_COLUMNS = {
        "Symbol": "TEXT NOT NULL",
        "PeriodEnd": "DATE NOT NULL",
        "PeriodType": "TEXT",
        "AnnounceDate": "DATE",
        "Currency": "TEXT",
        "Audited": "INTEGER",
        "Source": "TEXT",
        "SourceFile": "TEXT",
        "LastModified": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    }
    FIELD_COLUMNS = tuple(sorted(UNIFIED_FIELDS))

    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)
        self.ensure_table(
            self.TABLE,
            {
                **self.META_COLUMNS,
                **{field: "REAL" for field in self.FIELD_COLUMNS},
            },
            primary_key=("Symbol", "PeriodEnd"),
            indexes=(
                ("idx_financial_report_announce", ("Symbol", "AnnounceDate")),
            ),
        )

    def save(self, report: FinancialReport) -> None:
        row = {
            "Symbol": report.name_key,
            "PeriodEnd": report.period_end,
            "PeriodType": report.period_type,
            "AnnounceDate": report.announce_date,
            "Currency": report.currency,
            "Audited": 1 if report.audited else 0,
            "Source": report.source,
            "SourceFile": report.source_file,
        }
        for field in self.FIELD_COLUMNS:
            value = report.fields.get(field)
            if value is not None:
                row[field] = value
        self.upsert(self.TABLE, row)

    def save_many(self, reports: list[FinancialReport]) -> None:
        for report in reports:
            self.save(report)

    def get_reports(
        self,
        symbol: str,
        start_period: str | None = None,
        end_period: str | None = None,
    ) -> list[dict]:
        columns = list(self.META_COLUMNS) + list(self.FIELD_COLUMNS)
        sql = f"SELECT {','.join(columns)} FROM {self.TABLE} WHERE Symbol=?"
        params: list[object] = [symbol]
        if start_period:
            sql += " AND PeriodEnd>=?"
            params.append(start_period)
        if end_period:
            sql += " AND PeriodEnd<=?"
            params.append(end_period)
        sql += " ORDER BY PeriodEnd ASC"
        return [
            dict(row)
            for row in self.cursor.execute(sql, params).fetchall()
        ]

    def latest_period(self, symbol: str) -> str | None:
        return self.scalar(
            f"SELECT MAX(PeriodEnd) FROM {self.TABLE} WHERE Symbol=?", (symbol,)
        )


__all__ = ["FinancialReportRepository"]
