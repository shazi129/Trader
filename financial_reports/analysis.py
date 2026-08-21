"""Point-in-time financial-report analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from .repository import FinancialReportRepository


@dataclass
class FundamentalSnapshot:
    period_end: str
    period_type: str
    announce_date: str
    currency: str
    audited: bool
    revenue: float | None = None
    net_income_attr: float | None = None
    net_income_attr_nonifrs: float | None = None
    total_assets: float | None = None
    total_equity_attr: float | None = None
    operating_cash_flow: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    roe_quarterly: float | None = None
    eps_basic: float | None = None
    eps_basic_nonifrs: float | None = None
    revenue_yoy: float | None = None
    net_income_yoy: float | None = None
    net_income_nonifrs_yoy: float | None = None
    debt_to_assets: float | None = None
    cash_to_net_income: float | None = None
    free_cash_flow: float | None = None
    warnings: list[str] = field(default_factory=list)


def build_snapshot(
    symbol: str,
    repository: FinancialReportRepository,
    *,
    as_of: str | None = None,
) -> FundamentalSnapshot | None:
    """Build the latest report snapshot visible at ``as_of``."""

    cutoff = as_of or datetime.now().strftime("%Y-%m-%d")
    rows = [
        row for row in repository.get_reports(symbol)
        if row.get("AnnounceDate") and row["AnnounceDate"] <= cutoff
    ]
    if not rows:
        return None
    latest = rows[-1]
    previous = _find_yoy_row(rows, latest)
    snapshot = FundamentalSnapshot(
        period_end=latest["PeriodEnd"],
        period_type=latest.get("PeriodType") or "",
        announce_date=latest["AnnounceDate"],
        currency=latest.get("Currency") or "",
        audited=bool(latest.get("Audited")),
        revenue=_number(latest.get("Revenue")),
        net_income_attr=_number(latest.get("NetIncomeAttr")),
        net_income_attr_nonifrs=_number(latest.get("NetIncomeAttr_NonIFRS")),
        total_assets=_number(latest.get("TotalAssets")),
        total_equity_attr=(
            _number(latest.get("TotalEquityAttr"))
            or _number(latest.get("TotalEquity"))
        ),
        operating_cash_flow=_number(latest.get("OperatingCashFlow")),
        free_cash_flow=_number(latest.get("FreeCashFlow")),
        eps_basic=_number(latest.get("EPS_Basic")),
        eps_basic_nonifrs=_number(latest.get("EPS_Basic_NonIFRS")),
    )
    gross_profit = _number(latest.get("GrossProfit"))
    liabilities = _number(latest.get("TotalLiabilities"))
    if gross_profit is not None and snapshot.revenue:
        snapshot.gross_margin = gross_profit / snapshot.revenue
    if snapshot.net_income_attr is not None and snapshot.revenue:
        snapshot.net_margin = snapshot.net_income_attr / snapshot.revenue
    if snapshot.net_income_attr is not None and snapshot.total_equity_attr:
        snapshot.roe_quarterly = snapshot.net_income_attr / snapshot.total_equity_attr
    if liabilities is not None and snapshot.total_assets:
        snapshot.debt_to_assets = liabilities / snapshot.total_assets
    if snapshot.operating_cash_flow is not None and snapshot.net_income_attr:
        snapshot.cash_to_net_income = (
            snapshot.operating_cash_flow / snapshot.net_income_attr
        )
    if previous is None:
        snapshot.warnings.append("未找到上年同期财报，同比指标缺失")
    else:
        snapshot.revenue_yoy = _yoy(snapshot.revenue, previous.get("Revenue"))
        snapshot.net_income_yoy = _yoy(
            snapshot.net_income_attr, previous.get("NetIncomeAttr")
        )
        snapshot.net_income_nonifrs_yoy = _yoy(
            snapshot.net_income_attr_nonifrs,
            previous.get("NetIncomeAttr_NonIFRS"),
        )
    return snapshot


def _number(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _yoy(current, previous) -> float | None:
    current_value = _number(current)
    previous_value = _number(previous)
    if current_value is None or previous_value is None or previous_value <= 0:
        return None
    return current_value / previous_value - 1.0


def _find_yoy_row(rows: list[dict], latest: dict) -> dict | None:
    try:
        period = date.fromisoformat(latest.get("PeriodEnd") or "")
    except ValueError:
        return None
    target = f"{period.year - 1:04d}-{period.month:02d}-{period.day:02d}"
    return next((row for row in rows if row.get("PeriodEnd") == target), None)


__all__ = ["FundamentalSnapshot", "build_snapshot"]
