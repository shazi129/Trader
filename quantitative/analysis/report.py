"""Text rendering for quantitative reports."""

from __future__ import annotations

from .models import QuantitativeReport


def render_summary(report: QuantitativeReport) -> str:
    lines = [
        f"[量化分析] {report.name}({report.symbol}) @ {report.anchor_date}",
        f"基准价: {report.anchor_price:.2f} | 数据: {report.data_days}日",
    ]
    for horizon in sorted(report.horizons):
        result = report.horizons[horizon]
        lines.append(
            f"{horizon}日: 上涨概率 {result.probability_up:.1%} "
            f"({result.trend}, 信号数 {result.contributing_signals})"
        )
    lines.append("有效形态:")
    if not report.active_signals:
        lines.append("- 无")
    else:
        for signal in report.active_signals:
            direction = "看多" if signal.direction > 0 else "看空"
            lines.append(f"- [{signal.category}] {signal.name}: {direction}; {signal.description}")
    return "\n".join(lines)


__all__ = ["render_summary"]
