# financial_fetcher

解析财报 PDF，保存可审阅的 JSON 中间结果，并通过财报领域仓储写入
`financial_report`。

```text
PDF
  → ParserFactory
  → FinancialReport
  ├─ JSON 中间结果
  └─ FinancialReportRepository / financial_report
```

解析器只负责识别格式、抽取字段和单位归一；表结构、UPSERT 与查询属于
`FinancialReportRepository`；PIT 快照和同比分析属于
`financial_reports.analysis`。

## 用法

```powershell
# 单文件解析，只输出 JSON
python -m tools.financial_fetcher.financial_fetcher parse `
  --file tools/financial_fetcher/腾讯/2025Q3.pdf --stock Tencent

# 批量解析并入库
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 --stock Tencent

# 只解析，不入库
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 --stock Tencent --dry-run

# 跳过数据库中已存在的报告期
python -m tools.financial_fetcher.financial_fetcher run `
  --folder tools/financial_fetcher/腾讯 --stock Tencent --skip-existing
```

可用 `--db path/to/trader.db` 指定 SQLite 文件。PDF 文件名建议以
`YYYYQ1` 到 `YYYYQ4` 开头，作为旧格式报告无法识别报告期时的提示。

## 新增字段

1. 在 `financial_reports/field_mapping.py` 的 `UNIFIED_FIELDS` 注册统一字段；
2. 在相应市场映射中加入原始科目名；
3. 更新解析器测试并重新运行工具。

仓储会从 `UNIFIED_FIELDS` 自动创建或补齐列，不需要修改通用 SQLite 基础设施。

## 时点约束

`AnnounceDate` 必须是真实公告日期。下游分析使用
`announce_date <= analysis_date` 过滤，避免把尚未公开的财报用于历史分析。
