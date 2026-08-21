# -*- coding: utf-8 -*-
"""财报科目名 → 统一字段 key 的映射表。

设计原则
========

1. **统一字段名**就是 ``financial_report`` 表的财务数据列名（首字母大写驼峰）。
2. 每个市场（A 股 CAS / 港股 IFRS / 美股 GAAP）维护独立 dict；港股因繁简
   并存，两版都收录（实测腾讯 2024Q4 突然切到简体）。
3. 同义词显式列出，例如 A 股 "总资产" / "资产总计" 对应同一统一字段
   ``TotalAssets``。
4. **新增市场只需加一份 dict + 一个 parser**，仓储与分析服务无需修改。

加新字段流程
============

1. 在 ``UNIFIED_FIELDS`` 集合里加上统一名；
2. 在对应市场的 mapping dict 里加 "原始科目名": "统一名" 一行；
3. 重跑 ``financial_fetcher.py``；``FinancialReportRepository`` 会按
   ``UNIFIED_FIELDS`` 自动补齐数据库列。
"""

from __future__ import annotations

from typing import Optional


# ===========================================================================
# 统一字段集合（即 DB 列名 / FundamentalFields 属性名）
# ===========================================================================

#
# 单位约定（解析器内部归一后写入 fields）：
#   - 金额：元（解析港股「百萬」时已乘 1e6；A 股若以「元」披露则乘 1）
#   - EPS：元/股（不乘单位因子）
#   - 比率（如 ROE）：小数（5% → 0.05，与项目内其它因子惯例一致）
#   - 股数：股
#
# 符号约定：
#   - 收入 / 资产 / 现金流入：正
#   - 成本 / 费用 / 税：负（来自财报本身的列示，会计括号→负号）
#   - 现金流出（CapEx / DividendPaid）：负
#
UNIFIED_FIELDS: frozenset[str] = frozenset({
    # =====================================================================
    # 利润表（Income Statement）
    # =====================================================================
    "Revenue",                  # 营业收入。港股「收入」/ A 股「营业收入」。正值。
                                # 投研最常用的"营收"口径，PE / PS / 营收增速因子的分母。
    "RevenueTotal",             # 营业总收入。A 股专用：含利息收入、手续费收入等
                                # （金融行业），与 Revenue 的差额代表非主营。港股不区分，
                                # 通常 = Revenue。
    "OperatingCost",            # 营业成本（COGS）。负值。Revenue + OperatingCost = GrossProfit。
    "GrossProfit",              # 毛利。正值。毛利率 = GrossProfit / Revenue。
    "SellingExpense",           # 销售费用 / 销售及市场推广开支。负值。
    "AdminExpense",             # 管理费用 / 一般及行政开支。负值。
                                # 注意：腾讯把研发费合并在此项内，未单列 RnDExpense。
    "RnDExpense",               # 研发费用。负值。A 股单列；港股科技股大多并入 Admin。
    "FinanceExpense",           # 财务成本（含利息支出）。负值。
    "InterestIncome",           # 利息收入。正值。港股利润表常单列；A 股一般在 Revenue 下。
    "OperatingProfit",          # 经营盈利 / 营业利润（IFRS 或 CAS 口径）。正值。
                                # 注意：港股 IFRS 与 A 股 CAS 计算口径有差异，但都是
                                # "Revenue - 各项经营费用 ± 经营性其他收益"。
    "OperatingProfit_NonIFRS",  # 港股 Non-IFRS 经营盈利。腾讯/阿里等公司给出的"非通用准则"
                                # 口径，剔除了股份酬金、并购摊销、投资公允价值变动等
                                # 一次性 / 非现金项目，更贴近"经营性现金创造力"。
    "IncomeBeforeTax",          # 除税前盈利 / 利润总额。正值。= OperatingProfit
                                #   + 投资收益 + 营业外收支 - 财务成本。
    "TaxExpense",               # 所得税开支。负值。IncomeBeforeTax + TaxExpense = NetIncome。
    "NetIncome",                # 期内盈利 / 净利润（**含**少数股东权益）。正值。
                                # = NetIncomeAttr + MinorityInterest。
    "NetIncomeAttr",            # 归母净利润。正值。**核心字段**：
                                # PE / EPS / ROE 等一切估值因子的分子。
    "NetIncomeAttr_NonIFRS",    # 港股 Non-IFRS 归母净利润。同 OperatingProfit_NonIFRS 逻辑，
                                # 是港股科技股投研的"主流口径"，市场看的就是这个。
    "NetIncomeNonRecur",        # A 股「扣非归母」。剔除非经常性损益（政府补贴 / 资产处置
                                # 收益等）后的归母，反映持续盈利能力。港股没有此口径。
    "EPS_Basic",                # 基本每股收益（IFRS / CAS 口径）。元/股。
                                # = NetIncomeAttr / 加权平均流通股数。
    "EPS_Diluted",              # 摊薄每股收益（考虑期权 / 可转债等潜在稀释）。元/股。
                                # ≤ EPS_Basic。
    "EPS_Basic_NonIFRS",        # 港股 Non-IFRS 基本 EPS。元/股。
    "EPS_Diluted_NonIFRS",      # 港股 Non-IFRS 摊薄 EPS。元/股。
    "WeightedROE",              # A 股「加权平均净资产收益率」。**小数**（5% → 0.05）。
                                # 财报里以百分比披露，解析器需要 /100 入库。
                                # 港股不直接披露，用 NetIncomeAttr / TotalEquityAttr 推算。

    # =====================================================================
    # 资产负债表（Balance Sheet）—— 时点值，单位元
    # =====================================================================
    "TotalAssets",              # 资产总额 / 资产总计。正值。**核心字段**：
                                # PB 因子的分母组件，Piotroski 资产周转率分母。
                                # 港股早期版用「權益及負債總額」（资产=负债+权益），
                                # 已在 mapping 里映射到同一字段。
    "CurrentAssets",            # 流动资产合计。港股资产负债表把流动/非流动作为分组小标题
                                # 而非合計行，常 NULL。A 股有合計行可抓。
    "NonCurrentAssets",         # 非流动资产合计。同上，港股常 NULL。
    "Cash",                     # 现金及现金等价物。正值。流动性核心；流动比率分子。
    "Inventory",                # 存货。正值。腾讯类轻资产公司极小（亿级），
                                # 制造业 / 零售业是大头。
    "AccountsReceivable",       # 应收账款。正值。营运资本 / 应收周转天数因子用。
    "TotalLiabilities",         # 负债总额。正值。资产负债率 = TotalLiabilities / TotalAssets。
    "CurrentLiabilities",       # 流动负债。同 CurrentAssets，港股常 NULL；流动比率分母。
    "NonCurrentLiabilities",    # 非流动负债。同上，港股常 NULL。
    "ShortTermDebt",            # 短期借款（一年内到期的有息负债）。正值。
                                # 与 LongTermDebt 合计 = 总有息负债，用于净负债 / 利息保障倍数。
    "LongTermDebt",             # 长期借款（一年以上到期的有息负债）。正值。
    "AccountsPayable",          # 应付账款。正值。营运资本 / 应付周转天数因子用。
    "TotalEquity",              # 权益总额（**含**少数股东权益）。正值。
                                # = TotalAssets - TotalLiabilities。
    "TotalEquityAttr",          # 归母权益（本公司权益持有人应占权益）。正值。
                                # **核心字段**：PB 因子的真实分母（市值 / 归母权益）。
                                # = TotalEquity - MinorityInterest。
    "MinorityInterest",         # 少数股东权益。正值。

    # =====================================================================
    # 现金流量表（Cash Flow Statement）—— 期间值，单位元
    # =====================================================================
    "OperatingCashFlow",        # 经营活动产生的现金流量净额。正值（经营正常的公司）。
                                # 现金流质量因子核心：NetIncomeAttr / OperatingCashFlow ≈ 1
                                # 才说明利润有现金支撑。港股 Q1/Q3 经常 NULL（不披露）。
    "InvestingCashFlow",        # 投资活动产生的现金流量净额。**通常为负**
                                # （持续投资 → 流出）；为正常见于减持子公司 / 收回理财。
    "FinancingCashFlow",        # 筹资活动产生的现金流量净额。可正可负：
                                # 正 = 借款 / 增发；负 = 还债 / 分红 / 回购。
    "CapEx",                    # 资本开支（Capital Expenditure）。负值。
                                # 自由现金流 = OperatingCashFlow + CapEx（CapEx 已为负）。
                                # 港股摘要里直接披露；A 股需从「购建固定资产支付的现金」抓。
    "DividendPaid",             # 已支付股息。负值。分红率 = -DividendPaid / NetIncomeAttr。
    "Depreciation",             # 折旧与摊销。正值（虽是费用但现金流量表里作为加回项）。
                                # EBITDA 推算用：EBITDA ≈ OperatingProfit + Depreciation。
    "FreeCashFlow",             # 自由现金流。港股部分公司在摘要段直接给出（腾讯有），
                                # 缺失时可由代码后置计算：OperatingCashFlow + CapEx。

    # =====================================================================
    # 股本（Share Capital）
    # =====================================================================
    "SharesOutstanding",        # 已发行股份（股）。期末时点值。
                                # 市值 = 收盘价 × SharesOutstanding；
                                # EPS_Basic ≈ NetIncomeAttr / 加权平均股数（≈ SharesOutstanding）。
                                # 当前港股解析器未抓（在权益变动表 / 附注里），常 NULL。
})


# ===========================================================================
# 港股 IFRS 业绩公告 → 统一字段
# ===========================================================================
#
# 来源：实测 腾讯 2015Q3 ~ 2025Q3 共 41 份业绩公告。繁体（早期/2025）
# 与简体（2023Q4 / 2024Q4 起部分）混用，两版都收录。
# ===========================================================================

HK_IFRS_TO_UNIFIED: dict[str, str] = {
    # =====================================================================
    # 利润表（繁体）
    # ---------------------------------------------------------------------
    # 港股利润表科目顺序通常是：
    #   收入 - 收入成本 = 毛利
    #     - 销售费用 - 管理费用 + 其他收益 = 经营盈利
    #     + 利息收入 - 财务成本 + 投资收益 + 联营/合营 = 除税前盈利
    #     - 所得税 = 期内盈利（净利润）
    #     拆分为：归母 + 少数股东
    # =====================================================================
    "收入": "Revenue",                                       # 营收（正）
    "收入成本": "OperatingCost",                             # 营业成本（负，会计括号→负号）
    "毛利": "GrossProfit",                                   # 毛利（正）
    "銷售及市場推廣開支": "SellingExpense",                  # 销售费用（负）
    "一般及行政開支": "AdminExpense",                        # 管理费用（负）；腾讯研发并入此项
    # _drop：明确放弃这些"波动性损益项"——它们会让经营盈利失真，且
    # 量化因子（PE/ROE）通常用 NetIncomeAttr 而非 OperatingProfit，
    # 不入库这些项目能避免误用。映射成 _drop 也避免被计入 warnings。
    "其他收益／（虧損）淨額": "_drop",
    "其他收益╱（虧損）淨額": "_drop",                        # ╱ = U+2571 异体斜杠
    "經營盈利": "OperatingProfit",                           # 经营盈利（正）
    "投資收益／（虧損）淨額及其他": "_drop",
    "投資收益╱（虧損）淨額及其他": "_drop",
    "利息收入": "InterestIncome",                            # 利息收入（正，港股单列）
    "財務成本": "FinanceExpense",                            # 财务成本（负）
    "分佔聯營公司及合營公司盈利／（虧損）淨額": "_drop",     # 联营合营投资损益（波动大）
    "分佔聯營公司及合營公司盈利╱（虧損）淨額": "_drop",
    "除稅前盈利": "IncomeBeforeTax",                         # 利润总额（正）
    "所得稅開支": "TaxExpense",                              # 所得税（负）
    "期內盈利": "NetIncome",                                 # 净利润（正，含少数股东）
    "本公司權益持有人應佔盈利": "NetIncomeAttr",             # 归母净利润（**核心字段**，正）
    # 折行 / 截短场景的回退映射（解析器逐行扫，碰上这两种残片也能命中）：
    "本公司權益持有人": "NetIncomeAttr",                     # 早期表格里截短前缀
    "權益持有人應佔盈利": "NetIncomeAttr",                   # 折行残尾
    "非控制性權益": "MinorityInterest",                      # 少数股东权益（正）
    # Non-IFRS 双口径：剔除股份酬金、并购摊销、投资公允价值变动等一次性项目
    # 后的"经调整"利润，是港股科技股市场看的主流口径。
    "非國際財務報告準則經營盈利": "OperatingProfit_NonIFRS",
    "非國際財務報告準則本公司權益持有人應佔盈利": "NetIncomeAttr_NonIFRS",

    # ---- EPS（繁体）----
    # EPS 行格式如 "－基本 6.952 5.762"，独立看不出 IFRS / Non-IFRS。
    # 真正的字段名（EPS_Basic vs EPS_Basic_NonIFRS）由 parser 维护
    # eps_context 状态机做上下文消歧，这里只是把"－基本/－攤薄"先归一。
    # 多种破折号变体（－/—/–）都收录，因为不同年份 PDF 排版不同。
    "－基本": "EPS_Basic",
    "－攤薄": "EPS_Diluted",
    "—基本": "EPS_Basic",                                   # 全角破折号变体
    "—攤薄": "EPS_Diluted",

    # =====================================================================
    # 资产负债表（繁体）—— 时点值
    # =====================================================================
    "資產總額": "TotalAssets",                               # 资产总计（**核心**）
    "資產總計": "TotalAssets",                               # 同义
    "權益及負債總額": "TotalAssets",                         # 早期版用此名（资产=负债+权益恒等）
    "流動資產": "CurrentAssets",                             # 港股常 NULL（小标题非合计行）
    "非流動資產": "NonCurrentAssets",                        # 同上
    "現金及現金等價物": "Cash",                              # 流动性核心
    "存貨": "Inventory",                                     # 腾讯类轻资产公司极小
    "應收賬款": "AccountsReceivable",                        # 营运资本因子用
    "應收帳款": "AccountsReceivable",                        # 早期版异体字"帳"（非"賬"）
    "負債總額": "TotalLiabilities",                          # 资产负债率分子
    "流動負債": "CurrentLiabilities",                        # 港股常 NULL
    "非流動負債": "NonCurrentLiabilities",                   # 港股常 NULL
    # 歧义字段：港股资产负债表里"借款"和"應付票據"在「流動」「非流動」两个
    # section 各出现一次，单看 label 不知是 ShortTermDebt 还是 LongTermDebt。
    # 解析器需要结合所在 section（流动 / 非流动）来消歧——目前未实现，
    # 先标 _ambiguous，避免误抓后给出错误的短债 / 长债。
    "借款": "_ambiguous_loan",
    "應付票據": "_ambiguous_note",
    "應付賬款": "AccountsPayable",                           # 应付账款
    "應付帳款": "AccountsPayable",                           # 早期版异体字
    "權益總額": "TotalEquity",                               # 含少数股东（正）
    "本公司權益持有人應佔權益": "TotalEquityAttr",           # 归母权益（**核心**，PB 分母）

    # =====================================================================
    # 现金流量表（繁体）—— 期间值
    # ---------------------------------------------------------------------
    # 港股披露惯例：根据当期净额正负，用不同的科目名：
    #   净流入 → "所得現金流量淨額"
    #   净流出 → "耗用現金流量淨額"
    # 因此同一字段需要收录两个 label，符号由具体数字决定（投资/筹资为负是常态）。
    # =====================================================================
    "經營活動所得現金流量淨額": "OperatingCashFlow",         # 经营性现金流（**核心**）
    "投資活動所得現金流量淨額": "InvestingCashFlow",
    "投資活動耗用現金流量淨額": "InvestingCashFlow",         # 净流出版本
    "融資活動所得現金流量淨額": "FinancingCashFlow",
    "融資活動耗用現金流量淨額": "FinancingCashFlow",         # 净流出版本
    "資本開支": "CapEx",                                     # 资本开支（负）
    "資本開支付款": "CapEx",                                 # 摘要段里的另一种表述
    "自由現金流": "FreeCashFlow",                            # 港股部分公司直接给出

    # =====================================================================
    # 利润表（简体，2023Q4 / 2024Q4 起腾讯部分章节切换简体）
    # ---------------------------------------------------------------------
    # 注意：dict 中后定义的 key 会覆盖前面相同的 key。"收入成本" 和 "利息收入"
    # 这两个词繁简同形，重复定义不影响（值一样）。
    # =====================================================================
    "收入成本": "OperatingCost",
    "销售及市场推广开支": "SellingExpense",
    "一般及行政开支": "AdminExpense",
    "其他收益/（亏损）净额": "_drop",
    "其他收益／（亏损）净额": "_drop",                       # 全角斜杠变体
    "经营盈利": "OperatingProfit",
    "投资收益/（亏损）净额及其他": "_drop",
    "投资收益／（亏损）净额及其他": "_drop",
    "利息收入": "InterestIncome",
    "财务成本": "FinanceExpense",
    "分占联营公司及合营公司盈利/（亏损）净额": "_drop",
    "分占联营公司及合营公司盈利／（亏损）净额": "_drop",
    "除税前盈利": "IncomeBeforeTax",
    "所得税开支": "TaxExpense",
    "期内盈利": "NetIncome",                                 # 期中报告口径
    "年内盈利": "NetIncome",                                 # 年报口径（"年内" vs "期内"）
    "本公司权益持有人应占盈利": "NetIncomeAttr",
    "本公司权益持有人": "NetIncomeAttr",                     # 早期截短前缀
    "权益持有人应占盈利": "NetIncomeAttr",                   # 折行残尾
    "非控制性权益": "MinorityInterest",
    "非国际财务报告准则经营盈利": "OperatingProfit_NonIFRS",
    "非国际财务报告准则本公司权益持有人应占盈利": "NetIncomeAttr_NonIFRS",

    # ---- 资产负债表（简体）----
    "资产总额": "TotalAssets",
    "资产总计": "TotalAssets",
    "流动资产": "CurrentAssets",
    "非流动资产": "NonCurrentAssets",
    "现金及现金等价物": "Cash",
    "存货": "Inventory",
    "应收账款": "AccountsReceivable",
    "负债总额": "TotalLiabilities",
    "流动负债": "CurrentLiabilities",
    "非流动负债": "NonCurrentLiabilities",
    "应付账款": "AccountsPayable",
    "权益总额": "TotalEquity",
    "本公司权益持有人应占权益": "TotalEquityAttr",

    # ---- 现金流量表（简体）----
    "经营活动所得现金流量净额": "OperatingCashFlow",
    "投资活动所得现金流量净额": "InvestingCashFlow",
    "投资活动耗用现金流量净额": "InvestingCashFlow",         # 净流出版本
    "融资活动所得现金流量净额": "FinancingCashFlow",
    "融资活动耗用现金流量净额": "FinancingCashFlow",         # 净流出版本
    "资本开支": "CapEx",
    "资本开支付款": "CapEx",
    "自由现金流": "FreeCashFlow",
}


# ===========================================================================
# 公共归一接口
# ===========================================================================

# 标点白名单：解析时把全角/异体标点统一掉，避免 "－基本" 与 "—基本" 不匹配
_PUNCT_NORMALIZE = str.maketrans({
    "－": "-",   # U+FF0D 全角连字符
    "—": "-",   # U+2014 em dash
    "–": "-",   # U+2013 en dash
    "／": "/",  # 全角斜杠
    "╱": "/",  # U+2571 BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT
    "（": "(",
    "）": ")",
    " ": "",    # 删除半角空格
    "\u3000": "",  # 全角空格
    "\xa0": "",    # NBSP
})


def _canonicalize(label: str) -> str:
    """把抽出来的科目名做标准化（去空格、统一标点）。"""
    if not label:
        return ""
    return label.strip().translate(_PUNCT_NORMALIZE)


# 预建归一后的查找表（O(1) 命中）
_HK_NORMALIZED: dict[str, str] = {
    _canonicalize(k): v for k, v in HK_IFRS_TO_UNIFIED.items()
}


def normalize(label: str, market: str) -> Optional[str]:
    """label → 统一字段 key；返回 None 表示未识别。

    特殊返回值：
    - ``"_drop"``：明确放弃（如"其他收益净额"这种含义模糊、不入库的科目）；
      解析器应跳过且**不**计入 warnings。
    - ``"_ambiguous_..."``：歧义科目（如港股资产负债表里的"借款"，
      流动/非流动各有一个），解析器需结合上下文消歧。
    """
    if not label:
        return None
    canon = _canonicalize(label)
    if market == "HK_IFRS":
        return _HK_NORMALIZED.get(canon)
    # 后续可加 A_SHARE / US_GAAP
    return None
