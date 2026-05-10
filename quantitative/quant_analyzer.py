# -*- coding: utf-8 -*-
"""量化因子分析工具（薄壳）。

历史上本文件是一个 ~1900 行的"上帝模块"，包含了基础算法、因子定义、
评分、报告渲染、CLI。重构后实际逻辑迁移到了：

- 基础算法     → quantitative.indicators.{primitives,trend,momentum,volume,risk}
- 因子定义     → quantitative.analyzer.factors.QuantFactorEngine
- 评分模型     → quantitative.analyzer.scoring.compute_probability
- 报告渲染     → quantitative.analyzer.report.generate_summary
- 编排器       → quantitative.analyzer.analyzer.QuantAnalyzer

为了不破坏外部调用方（`from quantitative.quant_analyzer import QuantAnalyzer`
等用法），本文件继续 re-export 这些符号，并保留 CLI 入口。

使用方法：
    python -m quantitative.quant_analyzer Tencent
    python -m quantitative.quant_analyzer Alibaba --api tencent --days 500
"""

from __future__ import annotations

import argparse
import sys

from quantitative.analyzer import (
    AnalysisReport,
    FactorResult,
    QuantAnalyzer,
    QuantFactorEngine,
    compute_probability,
    generate_summary,
)

__all__ = [
    "AnalysisReport",
    "FactorResult",
    "QuantAnalyzer",
    "QuantFactorEngine",
    "compute_probability",
    "generate_summary",
]


# ===========================================================================
# 命令行入口（保持与旧版完全兼容）
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="量化因子分析工具")
    parser.add_argument("stock", help="股票 name_key（如 Tencent, Alibaba）")
    parser.add_argument("--api", default="tencent", help="数据源 (default: tencent)")
    parser.add_argument("--days", type=int, default=500, help="历史数据天数 (default: 500)")
    parser.add_argument("--no-cache", action="store_true",
                        help="不使用数据库缓存 (default: 使用缓存)")
    args = parser.parse_args()

    analyzer = QuantAnalyzer(api=args.api, use_cache=not args.no_cache)
    report = analyzer.analyze(args.stock, days=args.days)
    if report:
        print("\n" + report.summary)
    else:
        print("分析失败，请检查参数")
        sys.exit(1)


if __name__ == "__main__":
    main()
