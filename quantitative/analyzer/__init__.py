# -*- coding: utf-8 -*-
"""量化分析子包：因子结果 / 评分 / 报告 / 分析器。

为了兼容旧调用方，对外重新导出常用符号：

    from quantitative.analyzer import (
        FactorResult, AnalysisReport, compute_probability,
        QuantFactorEngine, QuantAnalyzer, generate_summary,
    )
"""

from .scoring import FactorResult, AnalysisReport, compute_probability
from .report import generate_summary
from .factors import QuantFactorEngine
from .analyzer import QuantAnalyzer

__all__ = [
    "FactorResult",
    "AnalysisReport",
    "compute_probability",
    "generate_summary",
    "QuantFactorEngine",
    "QuantAnalyzer",
]
