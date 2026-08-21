# Trader 架构

Trader 按业务域组织代码。数据库只是各业务域使用的基础设施，不存在集中了解
全部业务表的数据库业务对象。

## 业务能力

```text
外部行情源
   │
   ▼
quote_api ────────────── 行情获取、标准化、K 线缓存
   │ DailyQuote
   ▼
quantitative
   ├─ indicators ─────── 数学指标算子
   ├─ features ───────── 指标物化与查询
   ├─ signals ────────── 金叉、背离、超买超卖等形态判断
   ├─ backtesting ────── 形态的 point-in-time 回测与模型统计
   └─ analysis ───────── 某标的某时点的统一分析

financial_reports
   ├─ parsers ────────── 财报 PDF 解析与字段归一
   ├─ repository ─────── 财报存储
   └─ analysis ───────── PIT 财报快照与同比分析

tools ────────────────── 对上述业务能力的 CLI、桌面或 Web 适配器
```

## 目录职责

| 目录 | 职责 | 可以依赖 |
|---|---|---|
| `infrastructure/` | SQLite 连接、建表、UPSERT 等通用设施 | 标准库、日志 |
| `quote_api/` | 行情模型、线上 provider、行情仓储和缓存 | `infrastructure` |
| `quantitative/indicators/` | 输入序列、输出序列的纯数学函数 | 标准库 |
| `quantitative/features/` | 特征目录、计算器、快照、仓储 | indicators、quote model、infrastructure |
| `quantitative/signals/` | 使用行情与已计算特征判断形态 | features、quote model |
| `quantitative/backtesting/` | 对信号做无未来函数回测 | features、signals |
| `quantitative/analysis/` | 编排特征、信号、统计和报告 | quantitative 子域、QuoteAPI |
| `financial_reports/` | 财报解析、存储和基本面分析 | infrastructure |
| `tools/` | 用户入口和展示 | 上述公开服务 |

约束：

- `indicators` 不访问数据库、不读取 API，也不解释多空方向。
- `signals` 不获取数据、不写数据库、不自行重复计算 RSI/MACD 等指标。
- `backtesting` 只在 anchor 之前构造信号，未来数据只用于验证。
- `analysis` 是量化域唯一的应用编排入口。
- `tools` 不实现业务公式。

## 统一术语

以 RSI 超卖为例：

```text
Indicator  rsi(close, 14)            数学算法
Feature    rsi_14 = 27.3             某日可存储数值
Signal     rsi_14_oversold 被触发     形态及方向
Metric     20日方向成功率 61%         历史回测统计
Analysis   20日上涨概率 58%           当前时点聚合结果
```

代码中不再用 `factor` 同时表达这些概念。

## 存储所有权

SQLite 文件仍默认位于 `database/stock_data.db`，这是数据文件位置，不是 Python
业务模块。公共基础设施 [`infrastructure/sqlite.py`](../infrastructure/sqlite.py)
只管理连接和通用 SQL。

| 所有者 | Repository | 数据 |
|---|---|---|
| 行情域 | `quote_api.repository.MarketDataRepository` | `kline_daily` |
| 量化域 | `quantitative.features.FeatureRepository` | `quant_feature_daily` |
| 财报域 | `financial_reports.repository.FinancialReportRepository` | `financial_report` |

每个 Repository 只创建、迁移和查询自己拥有的表。旧 `factor_*` 表不再被读取；
为避免破坏历史数据库，代码升级不会主动删除它们。

## 量化数据流

### 特征物化

```text
QuoteAPI / MarketDataRepository
    → list[DailyQuote]
    → FeatureCalculator.compute
    → list[FeatureSnapshot]
    → FeatureRepository.save_many
```

特征名、类别和说明唯一声明在
[`quantitative/features/catalog.py`](../quantitative/features/catalog.py)。数据库
列由该目录自动生成，不再维护第二份字段映射。

### 形态判断

```text
quotes + feature snapshots
    → SignalContext
    → SignalEngine
    → explicit RULE_TYPES
    → list[SignalResult]
```

注册表是显式列表；不会扫描目录并意外导入研究脚本。未触发信号明确表示
`active=False, direction=0`，不会被聚合器当作看空。

### 回测

```text
历史 K 线
    → 一次性计算全量特征
    → 在每个历史 anchor 仅使用 anchor 之前的数据判断形态
    → 用 anchor+h 的收盘价验证方向
    → success_rate + sample_size + reliability weight
    → signal_statistics.json
```

统一周期为 5、20、60 个交易日。权重同时考虑偏离随机水平的程度和样本量，
不再把一个没有样本量的 `accuracy` 数字直接当概率权重。

### 时点分析

```text
QuantitativeAnalysisService.analyze(symbol, anchor_date)
    → 获取一次行情
    → 计算一次特征
    → 判断当前形态
    → 载入回测统计
    → 分别输出 5/20/60 日上涨概率
```

入口：

```powershell
python -m quantitative.cli features Tencent --api futu
python -m quantitative.cli backtest                  # 全股票池
python -m quantitative.cli backtest --stocks Tencent,Alibaba
python -m quantitative.cli analyze Tencent --date 2026-08-20
```

## 基本面与舆情

`financial_reports` 已包含财报统一模型、PDF 解析器、领域仓储和 PIT 快照分析。
舆情是未来独立域，建议使用 `sentiment/`，其原始文档、抽取结果、模型版本和
时点评分均由自身管理，不应加入行情或量化特征仓储。

## 工具层

- `tools/kline_fetcher`：增量拉取行情，随后触发特征物化。
- `tools/financial_fetcher`：解析并保存财报。
- `tools/stock_advisor`：只读本地行情，组合量化分析、历史相似态和基本面报告；
  特征缺失时仅基于本地 K 线物化，不连接线上 provider。
- `tools/stock_widget`：实时行情展示。
- 其它工具保持独立，不直接实现领域存储。

## 模块使用手册

| 模块 | 文档 |
|---|---|
| 行情获取、缓存和行情仓储 | [quote_api](modules/quote_api.md) |
| K 线生成量化特征 | [quantitative.features](modules/quantitative_features.md) |
| 金叉、背离等形态判断 | [quantitative.signals](modules/quantitative_signals.md) |
| 形态成功率与权重回测 | [quantitative.backtesting](modules/quantitative_backtesting.md) |
| 某标的某时点分析 | [quantitative.analysis](modules/quantitative_analysis.md) |
| 财报解析、仓储和 PIT 分析 | [financial_reports](modules/financial_reports.md) |
| 通用 SQLite 能力 | [infrastructure](modules/infrastructure.md) |
