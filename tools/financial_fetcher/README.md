# 财报 PDF 解析与入库工具

本工具把港股 / A 股的**业绩公告 PDF** 解析为结构化字段，并写入项目数据库
`database/stock_data.db` 的 `financial_report` 表，供量化因子层（PE / PB / ROE
/ Piotroski 等）按 PIT (Point-In-Time) 对齐到日频使用。

目前已落地：**港股 IFRS 解析器**，腾讯 2015Q3 ~ 2025Q3 共 41 份业绩公告全量
解析 + 入库通过。A 股 CAS 解析器（茅台）规划中。

---

## 1. 目录结构

```
tools/financial_fetcher/
├── financial_fetcher.py    # CLI 入口（parse / run）
├── README.md               # 本文档
├── Summary.xlsx            # 历史人工汇总表（仅参考，不再使用）
├── parsed/                 # 解析中间产物（JSON），git 友好、便于 review
│   └── Tencent_2025Q3.json
├── 腾讯/                   # 港股业绩公告 PDF
│   ├── 2015Q3.pdf
│   └── ... (共 41 份)
└── 茅台/                   # A 股季报 PDF（解析器未实现）
```

解析器 / 数据模型代码位于根级领域包 `financial_reports/`：

```
financial_reports/
├── models.py               # FinancialReport dataclass
├── parser_base.py          # FinancialParser 抽象基类 + ParserError
├── field_mapping.py        # 港股科目名（繁/简）→ 统一字段名
├── parser_factory.py       # 按 PDF 内容自动选解析器
└── parsers/
    ├── _utils.py           # 中文日期 / 数字单元格 / 报告期类型 通用工具
    └── hk_ifrs.py          # 港股 IFRS 解析器
```

---

## 2. 整体设计

```
┌──────────────────────┐  detect    ┌────────────────────┐
│ ParserFactory.detect │ ────────►  │  HKIfrsParser      │
└──────────────────────┘            │  (匹配 "業績公佈"   │
        │ 扫第一页关键字              │   等签名词)        │
        ▼                           └─────────┬──────────┘
   *.pdf 文件                                  │
                                               │ parse()
                                               ▼
                              ┌──────────────────────────────┐
                              │ FinancialReport (dataclass)  │
                              │  - 元信息：name_key /         │
                              │    period_end / announce_date │
                              │    / period_type / currency / │
                              │    audited / source           │
                              │  - fields: dict[str, float]   │
                              │  - warnings: list[str]        │
                              └──────────────┬───────────────┘
                                             │ dump
                                             ▼
                          parsed/{stock}_{period}.json   ← 人工 review / git diff
                                             │
                                             │ write_financial_reports_many
                                             ▼
                                  financial_report 表 (SQLite)
                                       ↓ 后续 PIT 对齐到日频
                                 factor_fundamental_pit
```

设计目标：

1. **解耦**：解析器只负责吐 `FinancialReport`，下游 DB / 因子层不感知是哪个市场。
2. **统一单位**：所有金额字段在解析器内部归一为「**元**」；EPS = 元/股；
   比率 = 小数（0.05 = 5%）。
3. **PIT 合规**：写入 DB 的 `AnnounceDate` 必须是真实公告日，因子查询时按
   "trade_date >= announce_date" 过滤，避免未来函数。
4. **可扩展**：加新市场 = 加 1 份字段映射 + 1 个 parser，DB / 因子 0 修改。

---

## 3. 解析原理（港股 IFRS PDF）

### 3.1 为什么不用 `pdfplumber.extract_tables()`

腾讯业绩公告**没有真实表格线**（视觉对齐排版），`extract_tables()` 返回空。
我们改走「**按行抽文本 + 段落锚点 + 字段归一**」路线。

### 3.2 流水线（5 步）

#### Step 1：取全文

```python
with pdfplumber.open(pdf_path) as pdf:
    pages_text = [(p.extract_text() or "") for p in pdf.pages]
full_text = "\n".join(pages_text)
```

#### Step 2：抽元信息

| 字段 | 抽取方式 | 鲁棒点 |
|------|----------|--------|
| `period_end` | 正则 `截至(.+?)止(三個月\|九個月\|年度\|...)` | 多匹配时按 `period_hint`（来自文件名 `2024Q2`）筛掉「上年同期对比表头」误命中 |
| `announce_date` | 正则 `香港，X年X月X日` | 取**第一处**（首页"即时发布"段就有，早期 PDF 末尾无署名段） |
| `period_type` | 由 `period_end` 月份推断 | 3=Q1 / 6=H1 / 9=Q3 / 12=ANNUAL |
| `unit_factor` | 全文搜「百萬 / 百万 / 千元」 | 1e6 / 1e3 / 1.0 |
| `currency` | 全文搜「人民幣 / 港幣 / 美元」 | 默认 CNY |
| `audited` | 前 3000 字搜「未經審核 / 經審核」 | 期中报告通常未审计 |

中文日期解析见 `parsers/_utils.py::parse_chinese_date`，支持「二零二五年九月三十日」
「2025年9月30日」「二零二五年十一月十三日」等多种写法。

#### Step 3：段落锚点切分

港股业绩公告通常分 4 个独立板块，先切段、再扫描，可大幅减少误匹配：

| 段 | 起始锚点 | 终止锚点 | 用途 |
|----|---------|---------|------|
| seg_0 | `財務表現摘要 / 業績摘要` | 管理層討論 / 簡明 | **P1 摘要表**：当期最干净的数据，含 Non-IFRS |
| seg_A | `第三季與... / 上半年與...` | 簡明綜合 / 業務回顧 | **管理层比较表**：本期 vs 上期 |
| seg_B | `簡明綜合財務狀況表` | 權益變動表 / 現金流量表 | **资产负债表** |
| seg_C | `簡明綜合現金流量表` | 中期財務資料附註 | **现金流量表** |

按 `seg_0 → seg_A → seg_B → seg_C` 顺序送进 `_absorb_text`，**先到优先**
（dict 已存在就不覆盖），让 P1 摘要的 Non-IFRS 数值优先于后面调节表里的复杂值。

最后用 `_absorb_text(full_text, only_missing=True)` 兜底扫一遍，捡漏冷门字段。

#### Step 4：行级解析（核心）

`_absorb_text()` 对一段文本按行扫，每行做这几件事：

```
原始行: "應付賬款 13 128,749 118,712"
                    ↑    ↑       ↑
                  附注号  本期   上期
```

1. **`_split_label_and_numbers`**：从行尾倒着找数字 token，切出 label + nums。
   `"應付賬款 13 128,749 118,712"` → label=`"應付賬款"`, nums=`[13, 128749, 118712]`

2. **EPS 上下文消歧**：EPS 子项的 label 是 `－基本 / －攤薄`，独立看不出 IFRS 还是
   Non-IFRS。维护一个 `eps_context` 状态机，遇到 `每股盈利` 父行时根据是否含
   "非國際/非IFRS" 切换 IFRS/NonIFRS，子行据此映射到正确的字段。

3. **折行 label 处理**：腾讯 P1 摘要里有
   ```
   非國際財務報告準則本公司
   權益持有人應佔盈利 70,551 ...
   ```
   用 `pending_label_prefix` 缓存上一行 label-only 的内容，下一行命中数字时
   先尝试拼接前缀再归一，归一不到再回落用本行 label 单独试。

4. **纯数字行回填**：早期年份会出现 label 在上一行、数字在下一行的版式
   （2021Q3）：
   ```
   資產總額
   1,567,584   1,333,425
   ```
   纯数字行触发 `pending_label_prefix → label` 的回填路径。

5. **`_pick_value` 附注号过滤**：金额行从 `nums` 列表里跳过开头的「< 100 且
   无千分位」的 token（典型附注号 1~30），取第一个真正的金额。
   EPS 字段例外（数值小，不能用大于 100 过滤），直接取第一个非 None。

6. **单位归一**：`val * unit_factor`，但 `_NON_AMOUNT_FIELDS`（EPS / ROE）
   不乘单位（已经是元/股或百分比）。

#### Step 5：合理性兜底

`_sanity_check`：归母净利润不可能为负、也不应大于整体期内盈利。出现这种值
直接丢弃 + 写 warning。这是为了对付早期 PDF 里 `本公司權益持有人 (594)` 这种
「应占其它综合收益」差额被短前缀映射误抓的场景。

---

## 4. 字段归一表（field_mapping.py）

```python
HK_IFRS_TO_UNIFIED = {
    "收入": "Revenue",
    "經營盈利": "OperatingProfit",
    "本公司權益持有人應佔盈利": "NetIncomeAttr",
    "權益持有人應佔盈利":      "NetIncomeAttr",   # 折行残尾
    "本公司權益持有人":        "NetIncomeAttr",   # 早期截短前缀
    "非國際財務報告準則經營盈利":           "OperatingProfit_NonIFRS",
    "非國際財務報告準則本公司權益持有人應佔盈利": "NetIncomeAttr_NonIFRS",
    ...
    # 简体（2024Q4 起）也全部收录，繁简各一份
    "经营盈利": "OperatingProfit",
    ...

    # 特殊返回值
    "其他收益／（虧損）淨額": "_drop",          # 明确放弃，不计 warnings
    "借款":                  "_ambiguous_loan",  # 流动/非流动各有一个，需上下文
}
```

匹配前先 `_canonicalize` 把全角/异体标点（`－ — / ／ ╱ （）`）和空格全部
归一掉，避免 `"－基本"` 与 `"—基本"` 不匹配。

**统一字段集合 `UNIFIED_FIELDS`** 约 35 个字段，覆盖三大表 + EPS + 双口径，
就是 `financial_report` 表的列名 / 未来 `FundamentalFields` dataclass 的属性名。

### 4.1 加新字段流程

1. 在 `UNIFIED_FIELDS` 集合里加上统一名；
2. 在 `database/stock_db_utils.py::_financial_columns` 里加列；
3. 在对应市场的 mapping dict 里加 `"原始科目名": "统一名"` 一行；
4. 重跑 `financial_fetcher.py`（`_ensure_financial_schema` 会自动 ALTER TABLE 补缺列）。

---

## 5. 数据库 Schema

表名 `financial_report`，主键 `(Symbol, PeriodEnd)`，独立于 `_create_long_table`
体系（不是按交易日组织的长表）。约 49 列（35 个金额字段 + 元信息 + 来源标记）。

关键列：

| 列 | 类型 | 说明 |
|----|------|------|
| `Symbol` | TEXT PK | 股票代码 / name_key |
| `PeriodEnd` | TEXT PK | 报告期末 `YYYY-MM-DD` |
| `PeriodType` | TEXT | Q1 / H1 / Q3 / ANNUAL |
| `AnnounceDate` | TEXT | **PIT 关键**：真实公告日 |
| `Currency` | TEXT | CNY / HKD / USD |
| `Audited` | INTEGER | 0/1 |
| `Source` | TEXT | 解析器 SOURCE_TAG（`pdf_hk_ifrs`） |
| `SourceFile` | TEXT | 原 PDF 文件名（debug 用） |
| `Revenue` ~ `EPS_Basic` ... | REAL | 35 个统一字段 |

写入接口（`database/stock_db_utils.py`）：

- `write_financial_report(report)`：单条 upsert
- `write_financial_reports_many(reports)`：批量事务 upsert
- `get_financial_reports(name_key)`：按公司读全部历史
- `get_latest_financial_period(name_key)`：最新报告期

---

## 6. CLI 用法

### 解析单份 PDF（不入库，调试用）

```powershell
python -m tools.financial_fetcher.financial_fetcher parse `
    --file tools/financial_fetcher/腾讯/2025Q3.pdf `
    --stock Tencent
```

输出：

```
OK: tools/financial_fetcher/腾讯/2025Q3.pdf
  period_end=2025-09-30  announce=2025-11-13
  type=Q3  currency=CNY  audited=False
  fields=23  warnings=2
```

中间产物落到 `tools/financial_fetcher/parsed/Tencent_2025Q3.json`。

### 批量解析 + 入库

```powershell
# 全量入库
python -m tools.financial_fetcher.financial_fetcher run `
    --folder tools/financial_fetcher/腾讯 --stock Tencent

# 只解析、落盘 JSON、不入库（dry-run，用于核对）
python -m tools.financial_fetcher.financial_fetcher run `
    --folder tools/financial_fetcher/腾讯 --stock Tencent --dry-run

# 只补新季度（按 PeriodEnd 跳过已入库）
python -m tools.financial_fetcher.financial_fetcher run `
    --folder tools/financial_fetcher/腾讯 --stock Tencent --skip-existing
```

文件名约定：`{YYYY}Q{1-4}.pdf`。CLI 会从文件名抽出 `period_hint` 传给解析器，
作为 PDF 内日期识别的兜底。

---

## 7. 已知坑与解决方案

| 坑 | 现象 | 解决 |
|----|------|------|
| pypdf 解析腾讯繁体 PDF | 全文乱码 | 改用 pdfplumber |
| `extract_tables()` 抽不出 | 列表空 | 改行级文本扫描 |
| EPS 错误乘 unit_factor | EPS=6.952 → 6952000 | `_NON_AMOUNT_FIELDS` 集合排除 |
| Non-IFRS 抓到累计值 | Q3 单季抓成 1-9 月累计 | 优先扫 P1 摘要 `seg_0` |
| 附注号干扰金额 | `應付帳款 13 128,749` 抓到 13 | 「< 100 且无千分位」过滤 |
| label 折行 | 「非國際FRP本公司\n權益持有人應佔盈利」 | `pending_label_prefix` 缓存 |
| 早期 PDF 中文日期漏字 | 「二零一五」缺 `一` | 字符集补全 |
| 2024Q2 命中上年同期 | 「截至2023年12月31日」先出现 | `period_hint` 月份严格匹配 |
| 2021Q3 短前缀误抓负值 | `本公司權益持有人 (594)` | `_sanity_check` 删错值 |
| label 与值跨行 | label 上一行、数字下一行 | 纯数字行回填 `pending_label_prefix` |

---

## 8. 后续扩展

- [ ] **A 股 CAS 解析器**（茅台）：表格通常有真实表格线，`extract_tables()` 可用，
      复用 `FinancialParser` 抽象，新增 `parsers/pdf_a_share.py` + A 股映射 dict。
- [ ] **PIT 派生表 `factor_fundamental_pit`**：把 `financial_report` 按
      `AnnounceDate` 对齐到日频，供 K 线侧 join。
- [ ] **`FundamentalFields` mixin**：纳入 `KlineIndicator` 多继承体系，
      在 `QuantFactorEngine` 加 PE / PB / ROE / Piotroski / 营收增速等因子。
- [ ] **`backtester._FEATURES`** 加财报特征。
