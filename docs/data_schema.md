# 数据存储

默认 SQLite 文件为 `database/stock_data.db`。表结构由各领域 Repository 自主管理，
不存在集中式数据库业务类。

## `kline_daily`

所有者：`quote_api.repository.MarketDataRepository`

主键：`(Symbol, Date)`。

| 列 | 含义 |
|---|---|
| `Symbol` | 项目内标的键 |
| `Date` | 交易日 |
| `Open/Close/High/Low` | OHLC |
| `Volume` | 成交量 |
| `Turnover` | 成交额 |
| `TurnoverRate` | 换手率 |

## `quant_feature_daily`

所有者：`quantitative.features.FeatureRepository`

主键：`(Symbol, Date)`。每行是一份 `FeatureSnapshot`，包含 `FeatureVersion` 和
在 `FEATURE_SPECS` 注册的全部特征列。缺少预热窗口的数据写 `NULL`，不再用
`0.0` 混淆“真实为零”和“数据不足”。

特征的唯一元数据来源：
[`quantitative/features/catalog.py`](../quantitative/features/catalog.py)。新增特征：

1. 在 `indicators/` 添加或复用纯函数；
2. 在 `FEATURE_SPECS` 注册 key、类别和说明；
3. 在 `FeatureCalculator` 物化该 key；
4. 添加已知输入输出测试。

Repository 启动时会自动添加新列。

## `financial_report`

所有者：`financial_reports.repository.FinancialReportRepository`

主键：`(Symbol, PeriodEnd)`，并按 `(Symbol, AnnounceDate)` 建索引。统一财务字段
来源于 `financial_reports.field_mapping.UNIFIED_FIELDS`。基本面分析必须按
`AnnounceDate <= anchor_date` 做 point-in-time 过滤。

## 模型产物

`quantitative/backtesting/signal_statistics.json` 是版本化模型产物，不是业务表。
结构包含模型版本、生成时间、标的池、数据截止日、各标的周期上涨基准，以及每个
信号每个周期的事件样本量、方向成功次数、匹配基准、超额命中、显著性、走步样本外
反向验证结果和可靠性权重。

它应由 `python -m quantitative.cli backtest ...` 重新生成。

## 旧表

`factor_indicator`、`factor_trend`、`factor_momentum`、`factor_volume`、
`factor_risk`、`factor_ma_ratio`、`factor_liquidity` 属于已废弃架构。新代码不创建、
读取或更新这些表。考虑到已有数据库可能含历史数据，升级不会自动执行 DROP；
确认备份后可人工删除。
