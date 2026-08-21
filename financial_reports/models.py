# -*- coding: utf-8 -*-
"""财报统一数据模型。

设计原则：
- 数据模型与具体 PDF 格式 / 数据源解耦：解析器输出 ``FinancialReport``，
  领域仓储和基本面分析不感知具体市场格式。
- 所有金额字段统一到「元」（解析器在 ``parse`` 内部负责单位归一）；
  EPS 单位为「元/股」；比率单位为小数（0.05 = 5%，与项目惯例对齐）。
- 解析过程中遇到的"未识别科目名"放进 ``warnings`` 不阻止入库，
  累积起来用于迭代字段映射表。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


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


