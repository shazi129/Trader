# -*- coding: utf-8 -*-
"""财报统一数据模型 + 解析器抽象基类。

设计原则：
- 数据模型与具体 PDF 格式 / 数据源 解耦：解析器吐出 ``FinancialReport``，
  下游 DB / 因子层完全不感知是哪个市场的财报。
- 所有金额字段统一到「元」（解析器在 ``parse`` 内部负责单位归一）；
  EPS 单位为「元/股」；比率单位为小数（0.05 = 5%，与项目惯例对齐）。
- 解析过程中遇到的"未识别科目名"放进 ``warnings`` 不阻止入库，
  累积起来用于迭代字段映射表。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


class ParserError(Exception):
    """解析失败时抛出。包含足够上下文便于排查。"""


@dataclass
class FinancialReport:
    """单份财报（解析后、入库前的中间数据模型）。

    元信息由各解析器从 PDF 抽取；``fields`` 是统一字段名 → 数值，
    单位由文档约定（金额=元，股本=股，EPS=元/股，比率=小数）。
    """

    # ---- 元信息 ----
    name_key: str                       # 'Tencent' / 'GuizhouMaotai'
    period_end: str                     # 'YYYY-MM-DD'，报告期末
    period_type: str                    # 'Q1' / 'H1' / 'Q3' / 'ANNUAL'
    announce_date: str                  # 'YYYY-MM-DD'，PIT 关键
    currency: str                       # 'CNY' / 'HKD' / 'USD'
    audited: bool                       # 是否经审计
    source: str                         # 解析器 SOURCE_TAG（如 'pdf_hk_ifrs'）
    source_file: str                    # PDF 文件名，debug 用

    # ---- 三大表合并字段 ----
    fields: dict[str, float] = field(default_factory=dict)

    # ---- 解析告警（未识别科目名等，不阻止入库）----
    warnings: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # 序列化（中间产物落盘 + 调试）
    # ------------------------------------------------------------------
    def to_json(self) -> dict:
        """转 JSON-friendly dict，``fields`` / ``warnings`` 完整保留。"""
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "FinancialReport":
        return cls(
            name_key=d["name_key"],
            period_end=d["period_end"],
            period_type=d["period_type"],
            announce_date=d["announce_date"],
            currency=d["currency"],
            audited=bool(d["audited"]),
            source=d["source"],
            source_file=d["source_file"],
            fields=dict(d.get("fields") or {}),
            warnings=list(d.get("warnings") or []),
        )

    def dump(self, path: Path) -> None:
        """落盘成漂亮 JSON（人工 review 用，git diff 友好）。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=2,
                      sort_keys=True)


class FinancialParser:
    """所有 PDF 解析器的抽象基类。

    子类必须实现：
    - ``SOURCE_TAG``：标识符，写入 DB 的 ``Source`` 列；
    - ``can_parse(pdf_path)``：扫第一页判断本解析器能否处理；
    - ``parse(pdf_path, name_key)``：返回 ``FinancialReport``。
    """

    SOURCE_TAG: str = "base"

    def can_parse(self, pdf_path: Path) -> bool:
        raise NotImplementedError

    def parse(self, pdf_path: Path, name_key: str,
              period_hint: Optional[str] = None) -> FinancialReport:
        """解析 PDF。

        :param period_hint: 可选的报告期提示，格式 ``"YYYYQ1"`` / ``"YYYYQ2"`` /
            ``"YYYYQ3"`` / ``"YYYYQ4"``。当 PDF 内没有标准 "截至XX止" 句式
            时（早期/部分年份），用此提示推断 ``period_end``。
            一般由调用方从文件名（如 ``2019Q1.pdf``）解析后传入。
        """
        raise NotImplementedError
