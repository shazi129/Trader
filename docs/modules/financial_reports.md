# financial_reports 使用说明

`financial_reports` 是财报与基本面领域，负责 PDF 格式识别、字段归一、财报存储和
按公告日构建 point-in-time 基本面快照。

```text
PDF
  → ParserFactory
  → FinancialParser
  → FinancialReport
  → FinancialReportRepository
  → build_snapshot(as_of=...)
```

当前已实现港股 IFRS PDF 解析器。A 股和美股解析器仍是待扩展项，不应将
`ParserFactory.detect()` 返回 `None` 解释成文件损坏。

## 模块结构

| 文件 | 职责 |
|---|---|
| `models.py` | 统一财报模型 `FinancialReport` |
| `field_mapping.py` | `UNIFIED_FIELDS` 与市场科目映射 |
| `parser_base.py` | 财报解析器抽象契约 |
| `parser_factory.py` | 按 PDF 内容选择解析器 |
| `parsers/` | 各市场具体解析实现 |
| `repository.py` | `financial_report` 领域仓储 |
| `analysis.py` | PIT 快照、同比和财务比率 |

## 解析单个 PDF

命令行：

```powershell
python -m tools.financial_fetcher.financial_fetcher parse `
  --file tools/financial_fetcher/腾讯/2025Q3.pdf `
  --stock Tencent
```

该命令输出 JSON 中间结果，不写数据库，适合检查字段和 warnings。

Python：

```python
from pathlib import Path
from financial_reports import ParserFactory

pdf = Path("tools/financial_fetcher/腾讯/2025Q3.pdf")
parser = ParserFactory.detect(pdf)
if parser is None:
    raise RuntimeError("没有支持该 PDF 格式的解析器")

report = parser.parse(pdf, "Tencent", period_hint="2025Q3")
print(report.period_end, report.announce_date)
print(report.fields.get("Revenue"))
print(report.warnings)
```

`period_hint` 用于 PDF 内缺少标准报告期语句时兜底，不能替代真实公告日。

## 批量解析与入库

```powershell
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 `
  --stock Tencent

# 只解析，不入库
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 `
  --stock Tencent `
  --dry-run

# 跳过已存在的报告期
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 `
  --stock Tencent `
  --skip-existing
```

可使用 `--db path/to/trader.db` 指定数据库。解析后的 JSON 中间文件用于人工审阅，
不等同于数据库备份。

## 统一模型与单位

`FinancialReport` 分为两部分：

- 元信息：标的、报告期、报告类型、公告日、币种、审计状态、来源文件；
- `fields`：统一字段 key 到数值的映射。

单位约定：

| 数据 | 统一单位 |
|---|---|
| 金额 | 元，解析器负责从千元/百万元换算 |
| 股本 | 股 |
| EPS | 元/股，不乘金额单位倍率 |
| ROE 等比例 | 小数，例如 5% 写成 `0.05` |

符号尽量保留财报列示语义，例如成本、费用和现金流出通常为负。下游计算不能随意
对所有字段取绝对值。

`warnings` 保存未识别科目或推断信息，不阻止成功解析。批量工具应保留这些告警供
人工复核。

## 财报仓储

```python
from financial_reports import FinancialReportRepository

with FinancialReportRepository() as repository:
    repository.save(report)
    rows = repository.get_reports(
        "Tencent",
        start_period="2024-01-01",
        end_period="2025-12-31",
    )
    latest_period = repository.latest_period("Tencent")
```

仓储拥有 `financial_report`，主键为 `(Symbol, PeriodEnd)`。相同报告期再次保存时，
已提供字段会 UPSERT；本次解析未提供的财务字段不会因局部更新被清空。

`get_reports()` 返回按 `PeriodEnd` 升序的字典列表。调用方不要直接依赖 SQLite
游标行对象。

## PIT 基本面快照

```python
from financial_reports import FinancialReportRepository, build_snapshot

with FinancialReportRepository() as repository:
    snapshot = build_snapshot(
        "Tencent",
        repository,
        as_of="2026-08-20",
    )

if snapshot:
    print(snapshot.period_end, snapshot.announce_date)
    print(snapshot.revenue_yoy, snapshot.net_margin)
```

筛选条件为：

```text
AnnounceDate <= as_of
```

然后选择报告期最新的一份已公告财报。没有合格财报时返回 `None`。

派生指标包括：

- 营收、归母净利润和 Non-IFRS 归母净利润同比；
- 毛利率、净利率、季度 ROE；
- 资产负债率；
- 经营现金流/归母净利润；
- 自由现金流等基础快照字段。

同比只匹配上年完全相同的月日。例如 `2025-06-30` 匹配 `2024-06-30`。找不到时
同比为 `None` 并加入 warning，不使用临近季度替代。

`AnnounceDate` 是历史分析的关键字段。缺少公告日的财报不会进入 PIT 快照，即使
它已经写入数据库。

## 新增统一字段

1. 将字段加入 `financial_reports.field_mapping.UNIFIED_FIELDS`；
2. 在对应市场 mapping 中加入原始科目名；
3. 更新解析器与单位处理测试；
4. 重新解析受影响 PDF；
5. 如需展示或派生比率，在 `analysis.py` 的快照模型中显式加入。

`FinancialReportRepository` 会根据 `UNIFIED_FIELDS` 自动增加 SQLite 列，不需要
修改 `infrastructure`。

## 新增市场解析器

实现 `FinancialParser`：

```python
from financial_reports.parser_base import FinancialParser


class ExampleParser(FinancialParser):
    SOURCE_TAG = "pdf_example"

    def can_parse(self, pdf_path):
        ...

    def parse(self, pdf_path, name_key, period_hint=None):
        ...
```

然后将解析器类显式加入 `ParserFactory._PARSERS`。解析器必须输出统一模型，不得
直接写数据库。

## 常见问题

- PDF 解析需要 `pdfplumber`；只使用财报模型、仓储和分析时不会强制加载解析库。
- PDF 表格结构变化可能导致“解析成功但字段缺失”，必须审阅 warnings 和 JSON。
- `latest_period()` 是最新报告期，不代表在任意历史日期已经公告；历史查询必须用
  `build_snapshot(as_of=...)`。
- 行情 provider 的 `StockFundamental` 是另一种可选快照，不是财报 PDF 的权威
  存储模型，当前财报分析以 `financial_report` 为准。

相关文档：[财报工具](../../tools/financial_fetcher/README.md)、
[数据表](../data_schema.md)。
