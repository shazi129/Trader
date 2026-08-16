# -*- coding: utf-8 -*-
"""PDF 解析共享工具：中文数字日期、数字单元格解析、单位识别等。

这些函数都是**纯函数**，便于单测；解析器主体复用，不重复实现。
"""

from __future__ import annotations

import re
from typing import Optional


# ===========================================================================
# 中文数字 → 阿拉伯数字
# ===========================================================================

_CN_DIGIT = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "两": 2,
    "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}


def _cn_section_to_int(s: str) -> int:
    """把"二零二五"或"十一"或"三十"等小段中文数字转 int。

    支持：
    - 纯数字串（"二零二五" → 2025）
    - 带"十"的两位数（"十一" → 11、"三十" → 30、"二十五" → 25）
    """
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    if "十" in s:
        parts = s.split("十", 1)
        tens = _CN_DIGIT.get(parts[0], 1) if parts[0] else 1
        units = _CN_DIGIT.get(parts[1], 0) if parts[1] else 0
        return tens * 10 + units
    val = 0
    for ch in s:
        if ch in _CN_DIGIT:
            val = val * 10 + _CN_DIGIT[ch]
        elif ch.isdigit():
            val = val * 10 + int(ch)
    return val


_DATE_CN_RE = re.compile(
    r"([一二三四五六七八九零〇\d]{2,5})\s*年"
    r"\s*([一二三四五六七八九十\d]{1,3})\s*月"
    r"\s*([一二三四五六七八九十\d]{1,3})\s*日"
)


def parse_chinese_date(text: str) -> Optional[str]:
    """从一段文本中抽第 1 个中文/阿拉伯数字日期，返回 ``YYYY-MM-DD``。

    匹配示例：
    - "二零二五年九月三十日" → "2025-09-30"
    - "二零二五年十一月十三日" → "2025-11-13"
    - "2025年9月30日" → "2025-09-30"
    """
    m = _DATE_CN_RE.search(text or "")
    if not m:
        return None
    y = _cn_section_to_int(m.group(1))
    mo = _cn_section_to_int(m.group(2))
    d = _cn_section_to_int(m.group(3))
    if not (1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


# ===========================================================================
# 数字单元格解析
# ===========================================================================

_NUM_RE = re.compile(r"^\s*\(?\s*[-−+]?\s*[\d,]+(?:\.\d+)?\s*\)?\s*$")


def parse_number(cell: Optional[str]) -> Optional[float]:
    """把 PDF 里的数字单元格转 float。

    支持：
    - "192,869" → 192869.0
    - "(84,071)" → -84071.0   （会计括号表示负数）
    - "(84,071.00)" → -84071.0
    - "—" / "–" / "" / None → None
    - 含中文（如"不適用"、"穩定"）→ None
    """
    if cell is None:
        return None
    s = str(cell).strip()
    if not s:
        return None
    if s in {"—", "–", "-", "－", "...", "／", "╱"}:
        return None
    if not _NUM_RE.match(s):
        return None
    negative = s.startswith("(") and s.endswith(")")
    s2 = s.strip("()").replace(",", "").replace(" ", "").replace("−", "-")
    try:
        v = float(s2)
    except ValueError:
        return None
    return -v if negative else v


# ===========================================================================
# 报告期类型推断
# ===========================================================================

def infer_period_type(period_end: str) -> str:
    """从 ``YYYY-MM-DD`` 推断 ``Q1`` / ``H1`` / ``Q3`` / ``ANNUAL``。

    港股惯例：3 月底=Q1、6 月底=H1、9 月底=Q3、12 月底=ANNUAL。
    """
    try:
        mo = int(period_end.split("-")[1])
    except (ValueError, IndexError):
        return "UNKNOWN"
    return {3: "Q1", 6: "H1", 9: "Q3", 12: "ANNUAL"}.get(mo, "UNKNOWN")
