# -*- coding: utf-8 -*-
"""分析报告渲染。"""

from __future__ import annotations

from .scoring import AnalysisReport


_CATEGORY_NAMES = {
    "momentum": "动量类",
    "technical": "技术类",
    "trend": "趋势类",
    "volatility": "波动/风险类",
    "liquidity": "流动性/资金面类",
    "reversal": "短期反转类",
    "pattern": "价格形态类",
    "valuation": "估值类",
    "quality": "质量类",
    "growth": "成长类",
    "dividend": "股息类",
    "size": "规模类",
}

_SIGNAL_ICONS = {1: "[+]", -1: "[-]", 0: "[ ]"}


def generate_summary(report: AnalysisReport) -> str:
    """把 AnalysisReport 渲染成可读的文本摘要。"""
    lines: list[str] = []
    lines.append(f"[分析] {report.stock_name}({report.name_key}) 量化分析报告")
    lines.append(f"   数据源: {report.data_source} | 数据量: {report.data_days}天")
    lines.append(f"   最新价: {report.latest_price:.2f}")
    lines.append("")
    lines.append("=== 综合判断 ===")
    lines.append(f"   趋势: {report.trend}")
    lines.append(f"   上涨概率: {report.probability_up * 100:.1f}%")
    lines.append(f"   下跌概率: {report.probability_down * 100:.1f}%")
    lines.append("")
    lines.append(f"=== 因子明细 ({len(report.factors)}个) ===")

    grouped: dict[str, list] = {}
    for f in report.factors:
        grouped.setdefault(f.category, []).append(f)

    for cat, items in grouped.items():
        lines.append(f"\n   [{_CATEGORY_NAMES.get(cat, cat)}]")
        for f in items:
            icon = _SIGNAL_ICONS.get(f.signal, "[ ]")
            lines.append(f"   {icon} {f.name}: {f.description}")

    lines.append("")
    lines.append("=== 风险提示 ===")
    lines.append("   本分析仅基于技术面量化因子，不构成投资建议。")
    lines.append("   基本面、政策面、情绪面等因素未纳入考量。")

    return "\n".join(lines)
