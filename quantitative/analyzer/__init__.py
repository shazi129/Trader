# -*- coding: utf-8 -*-
"""量化分析子包：因子结果 / 评分 / 报告 / 分析器。

为了兼容旧调用方，对外重新导出常用符号：

    from quantitative.analyzer import (
        FactorResult, AnalysisReport, compute_probability,
        QuantFactorEngine, QuantAnalyzer, generate_summary,
    )
"""

from .scoring import (
    FactorResult,
    AnalysisReport,
    compute_probability,
    compute_period_probabilities,
)
from .report import generate_summary
from .analyzer import QuantAnalyzer

# 新因子体系（每个因子一个类，输出未来 5/30/60 日涨跌预测）
from .factors import (
    BaseFactor,
    FactorContext,
    FactorOutput,
    FactorManager,
    FactorAnalysisResult,
    all_factors,
    factor_names,
)

# 旧引擎（已迁移到新体系，保留以兼容历史调用）
from .factors_legacy import QuantFactorEngine

__all__ = [
    "FactorResult",
    "AnalysisReport",
    "compute_probability",
    "compute_period_probabilities",
    "generate_summary",
    "QuantAnalyzer",
    "BaseFactor",
    "FactorContext",
    "FactorOutput",
    "FactorManager",
    "FactorAnalysisResult",
    "all_factors",
    "factor_names",
    "QuantFactorEngine",
]
