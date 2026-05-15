# -*- coding: utf-8 -*-
"""港股 IFRS 业绩公告 PDF 解析器（适用于腾讯/阿里等港股科技股）。

核心策略
========

港股业绩公告排版**没有真实表格线**（视觉对齐），``pdfplumber.extract_tables``
返回空。改走"按行抽文本 + 段落锚点 + 字段归一"路线：

1. 用 ``page.extract_text()`` 拿到带换行的全页文本，拼成 full_text；
2. 按"已知段落锚点"切出 4 个区段（管理层比较/财务状况/现金流量/EPS 表）：
   - **当季比较表**（"X季與X季的比較"段）：抓利润表本期值
   - **简明综合财务状况表**：抓资产负债表
   - **简明综合现金流量表**：抓现金流量净额
3. 在每段内逐行扫描，按"label + 数字"切分；
4. 数字过滤掉行内的"附注号"（无千分位、< 100 的整数），保留真实金额；
5. 单位换算：金额字段乘 ``unit_factor``（百萬元 → 元）；EPS / 比率不乘。

EPS 上下文消歧
==============

EPS 行格式如 ``－基本 6.952 5.762 ...``，独立看不出 IFRS / Non-IFRS，
靠"上一行非空科目是哪个 EPS 父项"做上下文消歧。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import pdfplumber

from quote_api.financial.financial_base import (
    FinancialReport,
    FinancialParser,
    ParserError,
)
from quote_api.financial.field_mapping import normalize, _canonicalize
from quote_api.financial.parsers._utils import (
    parse_chinese_date,
    parse_number,
    infer_period_type,
)

_log = logging.getLogger(__name__)


# 这些字段是"小数/比率/每股值"，不参与单位换算（unit_factor=1）
_NON_AMOUNT_FIELDS: frozenset[str] = frozenset({
    "EPS_Basic", "EPS_Diluted",
    "EPS_Basic_NonIFRS", "EPS_Diluted_NonIFRS",
    "WeightedROE",
})


class HKIfrsParser(FinancialParser):
    """港股 IFRS 业绩公告解析器。"""

    SOURCE_TAG = "pdf_hk_ifrs"

    _SIGNATURES = (
        "業績公佈", "业绩公布", "聯交所", "联交所",
        "本公司權益持有人", "本公司权益持有人",
        "國際財務報告準則", "国际财务报告准则",
        "香港聯合交易所", "香港联合交易所",
    )

    # ------------------------------------------------------------------
    # 探测
    # ------------------------------------------------------------------
    def can_parse(self, pdf_path: Path) -> bool:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                head = (pdf.pages[0].extract_text() or "")[:2000]
        except Exception as e:  # noqa: BLE001
            _log.debug("can_parse open failed: %s", e)
            return False
        return any(sig in head for sig in self._SIGNATURES)

    # ------------------------------------------------------------------
    # 主解析入口
    # ------------------------------------------------------------------
    def parse(self, pdf_path: Path, name_key: str,
              period_hint: Optional[str] = None) -> FinancialReport:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = [(p.extract_text() or "") for p in pdf.pages]
        full_text = "\n".join(pages_text)

        if not full_text.strip():
            raise ParserError(f"empty text extracted from {pdf_path.name}")

        # 1. 元信息
        period_end = self._extract_period_end(full_text, period_hint)
        announce_date = self._extract_announce_date(full_text)
        period_type = infer_period_type(period_end)
        unit_factor = self._extract_unit_factor(full_text)
        currency = self._extract_currency(full_text)
        audited = self._is_audited(full_text)

        # 2. 字段抽取（按段落锚点）
        fields: dict[str, float] = {}
        warnings: list[str] = []

        # 段 0：开头的"財務表現摘要"段（P1），最干净的当期数据
        seg_0 = self._extract_segment(
            full_text,
            anchors_start=("財務表現摘要", "财务表现摘要", "業績摘要", "业绩摘要"),
            anchor_end=("管理層討論", "管理层讨论", "業務回顧", "业务回顾",
                        "經營資料", "经营资料", "簡明", "简明"),
        )
        # 段 A：管理层比较表（本期 vs 上期）
        seg_a = self._extract_segment(
            full_text,
            anchors_start=("第三季與", "第二季與", "第一季與", "上半年與", "全年與",
                           "第三季与", "第二季与", "第一季与", "上半年与", "全年与"),
            anchor_end=("簡明綜合", "简明综合", "業務回顧", "业务回顾"),
        )
        # 段 B：简明综合财务状况表（资产负债）
        seg_b = self._extract_segment(
            full_text,
            anchors_start=("簡明綜合財務狀況表", "简明综合财务状况表"),
            anchor_end=("簡明綜合權益變動表", "简明综合权益变动表",
                        "簡明綜合現金流量表", "简明综合现金流量表"),
        )
        # 段 C：简明综合现金流量表
        seg_c = self._extract_segment(
            full_text,
            anchors_start=("簡明綜合現金流量表", "简明综合现金流量表"),
            anchor_end=("中期財務資料附註", "中期财务资料附注", "附註", "附注"),
        )

        for seg in (seg_0, seg_a, seg_b, seg_c):
            if seg:
                self._absorb_text(seg, fields, warnings, unit_factor)

        # 兜底：剩余字段全文再扫
        self._absorb_text(full_text, fields, warnings, unit_factor,
                          only_missing=True)

        # 数据合理性校验：归母净利润应 > 0 且 ≤ 期内盈利（净利润）
        # 否则可能是从"综合收益表"或"调节表"误抓的值，删掉以免误用。
        self._sanity_check(fields, warnings)

        return FinancialReport(
            name_key=name_key,
            period_end=period_end,
            period_type=period_type,
            announce_date=announce_date,
            currency=currency,
            audited=audited,
            source=self.SOURCE_TAG,
            source_file=pdf_path.name,
            fields=fields,
            warnings=warnings,
        )

    # ==================================================================
    # 段落锚点切分
    # ==================================================================

    @staticmethod
    def _extract_segment(text: str,
                         anchors_start: tuple[str, ...],
                         anchor_end: tuple[str, ...]) -> Optional[str]:
        """从 full_text 切出 [first(anchor_start), next(anchor_end)] 之间的文本。

        - 找 ``anchors_start`` 中**最早出现**的那个作为开始位置；
        - 在开始位置之后找 ``anchor_end`` 中**最早出现**的那个作为结束位置；
        - 找不到任何一个返回 None。
        """
        starts = [text.find(a) for a in anchors_start]
        starts = [s for s in starts if s >= 0]
        if not starts:
            return None
        s = min(starts)
        ends = [text.find(a, s + 5) for a in anchor_end]
        ends = [e for e in ends if e >= 0]
        e = min(ends) if ends else len(text)
        return text[s:e]

    # ==================================================================
    # 元信息抽取
    # ==================================================================

    def _extract_period_end(self, text: str,
                             period_hint: Optional[str] = None) -> str:
        """报告期末日期。

        多种格式兼容（按可靠性优先级）：
        1. "截至XX年XX月XX日止三個月/九個月/年度" —— 业绩公告标题段
        2. "公佈/公布截至 YYYY 年 M 月 D 日" —— 早期版（2015~2017）
        3. "於X年X月X日"（资产负债表表头）
        4. ``period_hint``（如 ``"2019Q1"``）—— 来自文件名的兜底

        注：当 period_hint 给定时，模式 1 命中的日期必须**落在 hint 所述
        年份的 ±1 年内**才被采纳，避免把"截至上年同期"对比表头错认为
        本期末（典型场景：2024Q2 的"截至二零二三年十二月三十一日止年度"
        会先于"截至二零二四年六月三十日止三个月"出现）。
        """
        hint_year: Optional[int] = None
        hint_quarter: Optional[int] = None
        if period_hint:
            hm = re.match(r"^(\d{4})Q([1234])$", period_hint.strip().upper())
            if hm:
                hint_year = int(hm.group(1))
                hint_quarter = int(hm.group(2))

        def _within_hint(dstr: str) -> bool:
            if hint_year is None:
                return True
            try:
                yr, mo, _ = dstr.split("-")
                yr = int(yr); mo = int(mo)
            except (ValueError, IndexError):
                return False
            # 同一年才算命中：Q1=>3, Q2=>6, Q3=>9, Q4=>12
            expected_mo = {1: 3, 2: 6, 3: 9, 4: 12}.get(hint_quarter)
            return yr == hint_year and mo == expected_mo

        # 1. "截至...止..." —— 最可靠（带"止"字消除歧义）；遍历所有匹配，
        # hint 给定时只取月份与 hint 一致的；hint 缺失时取第一个。
        matches = list(re.finditer(
            r"截至(.{6,40}?)止(?:三個月|三个月|六個月|六个月|九個月|九个月|"
            r"年度|十二個月|十二个月|第[一二三四1234]季)",
            text,
        ))
        for m in matches:
            d = parse_chinese_date(m.group(1))
            if d and _within_hint(d):
                return d
        # hint 严格命中失败，回落到第一个能解析的（hint 缺失场景）
        if hint_year is None:
            for m in matches:
                d = parse_chinese_date(m.group(1))
                if d:
                    return d

        # 2. "公佈/公布截至 YYYY年M月D日"（早期版）
        m2 = re.search(
            r"公[佈布]\s*截至\s*([一二三四五六七八九零〇\d]{2,5}\s*年"
            r"\s*[一二三四五六七八九十\d]{1,3}\s*月"
            r"\s*[一二三四五六七八九十\d]{1,3}\s*日)",
            text,
        )
        if m2:
            d = parse_chinese_date(m2.group(1).replace(" ", ""))
            if d and _within_hint(d):
                return d

        # 3. 资产负债表表头 "於X年X月X日"
        m3 = re.search(r"於([一二三四五六七八九零〇\d]{2,5}年.{2,12}日)", text)
        if m3:
            d = parse_chinese_date(m3.group(1))
            if d and _within_hint(d):
                return d

        # 4. 文件名提示兜底
        if period_hint:
            d = self._period_hint_to_date(period_hint)
            if d:
                return d

        raise ParserError("period_end not found")

    @staticmethod
    def _period_hint_to_date(hint: str) -> Optional[str]:
        """``"2019Q1"`` → ``"2019-03-31"``（Q1=3-31, Q2=6-30, Q3=9-30, Q4=12-31）。"""
        m = re.match(r"^(\d{4})Q([1234])$", hint.strip().upper())
        if not m:
            return None
        y = int(m.group(1))
        q = int(m.group(2))
        return {1: f"{y:04d}-03-31", 2: f"{y:04d}-06-30",
                3: f"{y:04d}-09-30", 4: f"{y:04d}-12-31"}[q]

    def _extract_announce_date(self, text: str) -> str:
        """公告日：取**第一处** '香港，X年X月X日'。

        港股财报首页"即时发布"段就有公告日；末尾的署名段（"承董事會命"）
        是同一日期。早期（2015~2017）PDF 末尾没有署名段，因此只用首处。
        """
        m = re.search(
            r"香港[，,]\s*([一二三四五六七八九零〇\d]{2,5}\s*年"
            r"\s*[一二三四五六七八九十\d]{1,3}\s*月"
            r"\s*[一二三四五六七八九十\d]{1,3}\s*日)",
            text,
        )
        if m:
            d = parse_chinese_date(m.group(1).replace(" ", ""))
            if d:
                return d
        raise ParserError("announce_date (香港，X年X月X日) not found")

    def _extract_unit_factor(self, text: str) -> float:
        if "百萬" in text or "百万" in text:
            return 1_000_000.0
        if "千元" in text:
            return 1_000.0
        return 1.0

    def _extract_currency(self, text: str) -> str:
        if "人民幣" in text or "人民币" in text:
            return "CNY"
        if "港幣" in text or "港币" in text or "港元" in text:
            return "HKD"
        if "美元" in text:
            return "USD"
        return "CNY"

    @staticmethod
    def _is_audited(text: str) -> bool:
        head = text[:3000]
        if "未經審核" in head or "未经审核" in head:
            return False
        if "經審核" in head or "经审核" in head:
            return True
        return False

    @staticmethod
    def _sanity_check(fields: dict[str, float], warnings: list[str]) -> None:
        """对解析出的字段做合理性校验，明显错值删掉以免下游误用。

        港股财报常见误匹配：
        - "本公司权益持有人 (594)" 实际是综合收益表里"应占其它综合收益"的
          差额，被短前缀映射误抓为 ``NetIncomeAttr``。归母净利润不可能
          常态为负，且数值上必 ≤ 期内盈利。
        """
        ni_attr = fields.get("NetIncomeAttr")
        ni = fields.get("NetIncome")
        if ni_attr is not None and ni is not None and ni > 0:
            # 归母净利润不应为负、不应大于整体净利润
            if ni_attr < 0 or ni_attr > ni * 1.5:
                warnings.append(
                    f"sanity: drop NetIncomeAttr={ni_attr:.0f} "
                    f"(NetIncome={ni:.0f})"
                )
                fields.pop("NetIncomeAttr", None)

    # ==================================================================
    # 字段抽取（行级文本解析）
    # ==================================================================

    def _absorb_text(self, text: str,
                     fields: dict[str, float],
                     warnings: list[str],
                     unit_factor: float,
                     only_missing: bool = False) -> None:
        """逐行扫描 text，把识别到的科目→数字写进 fields。"""
        if not text:
            return
        eps_context: Optional[str] = None  # IFRS / NonIFRS / None
        # 上一行的"label-only"残留，用于处理折行情况
        # （腾讯 P1 表里 "非國際財務報告準則本公司\n權益持有人應佔盈利 70,551 ..."）
        pending_label_prefix: Optional[str] = None

        for raw_line in text.split("\n"):
            line = raw_line.rstrip()
            if not line:
                pending_label_prefix = None
                continue
            stripped = line.strip()

            # 维护 EPS 上下文（独立的"每股盈利"父项行）
            if "每股盈利" in stripped or "每股收益" in stripped:
                if "非國際" in stripped or "非国际" in stripped \
                        or "非IFRS" in stripped or "非通用" in stripped:
                    eps_context = "NonIFRS"
                else:
                    eps_context = "IFRS"
                pending_label_prefix = None
                continue

            label, nums = self._split_label_and_numbers(line)

            if not nums:
                # 整行无数字：可能是折行 label 的上半段，缓存起来给下一行用
                if label and len(label) <= 30 and not label.endswith("。") \
                        and not label.endswith("，"):
                    pending_label_prefix = label
                else:
                    pending_label_prefix = None
                continue

            if not label:
                # 纯数字行：可能是上一行 label 的延续（"资产总额\n1,567,584 1,333,425"）
                if pending_label_prefix:
                    label = pending_label_prefix
                    pending_label_prefix = None
                else:
                    continue

            # 把 pending 前缀拼到当前 label 前（label 也在但前缀更早）
            full_label = label
            if pending_label_prefix:
                full_label = pending_label_prefix + label
            pending_label_prefix = None

            key = self._normalize_with_context(full_label, eps_context)
            if key is None and full_label != label:
                # 拼接后认不出，回落用本行 label 单独再试
                key = self._normalize_with_context(label, eps_context)

            if key is None:
                if any(n is not None for n in nums):
                    warnings.append(f"unmapped: {full_label.strip()[:40]}")
                continue
            if key.startswith("_"):
                continue
            if only_missing and key in fields:
                continue
            if key in fields and not only_missing:
                continue

            val = self._pick_value(nums, key)
            if val is None:
                continue

            scale = 1.0 if key in _NON_AMOUNT_FIELDS else unit_factor
            fields[key] = val * scale

    # ------------------------------------------------------------------
    # 数字挑选：处理"附注号"
    # ------------------------------------------------------------------
    @staticmethod
    def _pick_value(nums: list[Optional[float]], key: str) -> Optional[float]:
        """从一行抽到的数字列表里挑"本期值"。

        港股表格常见版式：
            ``應付賬款 13 128,749 118,712``
                附注号(13) + 本期(128,749) + 上期(118,712)

        启发式：
        - 跳过开头的"小整数 + 无千分位"的 token（疑似附注号）；
        - 取第一个真正的金额（带千分位 / 大于 1000 / 或带小数）作为本期值。

        EPS 字段例外：EPS 数值很小（< 100），不能用"大于 1000"过滤。
        """
        if not nums:
            return None

        # 对 EPS 直接取第一个非 None 数字（不会有附注号干扰，EPS 行没附注）
        if key in _NON_AMOUNT_FIELDS:
            for v in nums:
                if v is not None:
                    return v
            return None

        # 金额行：跳过 < 100 的疑似附注号
        for v in nums:
            if v is None:
                continue
            # 附注号典型范围 1~30，金额都是百万为单位 → 至少千万级 → 远 > 100
            if abs(v) < 100:
                continue
            return v
        # 如果都很小，老老实实取第一个非 None
        for v in nums:
            if v is not None:
                return v
        return None

    # ------------------------------------------------------------------
    # 工具：从一行里切出 label 和 trailing 数字
    # ------------------------------------------------------------------
    def _split_label_and_numbers(self, line: str) -> tuple[str, list[Optional[float]]]:
        """按"行尾若干数字 token"切分 label / 数字。"""
        toks = line.split()
        if not toks:
            return "", []

        n = len(toks)
        first_num_idx = n
        for i in range(n - 1, -1, -1):
            if self._looks_like_number_or_percent(toks[i]):
                first_num_idx = i
            else:
                break
        if first_num_idx == n:
            return line.strip(), []

        label = " ".join(toks[:first_num_idx]).strip()
        num_tokens = toks[first_num_idx:]

        nums: list[Optional[float]] = []
        for t in num_tokens:
            if t.endswith("%") or t in {"NM", "穩定", "稳定"}:
                nums.append(None)
                continue
            v = parse_number(t)
            nums.append(v)
        return label, nums

    @staticmethod
    def _looks_like_number_or_percent(tok: str) -> bool:
        if tok in {"NM", "穩定", "稳定", "—", "–", "-", "－"}:
            return True
        if tok.endswith("%"):
            tok = tok[:-1]
            if tok.startswith("-") or tok.startswith("+"):
                tok = tok[1:]
        t = tok.lstrip("(").rstrip(")").lstrip("-").lstrip("+")
        if not t:
            return False
        return all(c.isdigit() or c in ",." for c in t) and any(c.isdigit() for c in t)

    # ------------------------------------------------------------------
    # 工具：归一 + EPS 上下文消歧
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_with_context(label: str,
                                 eps_context: Optional[str]) -> Optional[str]:
        canon = _canonicalize(label)
        is_eps_child = canon in {"-基本", "-攤薄", "-摊薄"}
        if is_eps_child:
            if eps_context == "NonIFRS":
                return {
                    "-基本": "EPS_Basic_NonIFRS",
                    "-攤薄": "EPS_Diluted_NonIFRS",
                    "-摊薄": "EPS_Diluted_NonIFRS",
                }.get(canon)
            if eps_context == "IFRS":
                return {
                    "-基本": "EPS_Basic",
                    "-攤薄": "EPS_Diluted",
                    "-摊薄": "EPS_Diluted",
                }.get(canon)
            return None
        return normalize(label, "HK_IFRS")
