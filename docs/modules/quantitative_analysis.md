# quantitative.analysis 使用说明

`quantitative.analysis` 是量化域的应用编排层。它负责在一次调用中完成行情读取、
特征计算、形态判断、回测统计加载和多周期概率聚合。

```text
QuantitativeAnalysisService
  ├─ QuoteAPI
  ├─ FeatureCalculator
  ├─ SignalEngine
  ├─ BacktestArtifactRepository
  └─ aggregate_signals
       → QuantitativeReport
```

它不负责财报分析、舆情分析或历史相似态 k-NN；这些能力由其他领域或工具组合。

## 命令行分析

```powershell
# 使用默认线上行情源
python -m quantitative.cli analyze Tencent

# 仅使用本地行情
python -m quantitative.cli analyze Tencent --api db

# 分析指定历史日期
python -m quantitative.cli analyze Tencent --api db --date 2026-08-20

# 自定义回看长度与数据库
python -m quantitative.cli analyze Tencent `
  --api db `
  --lookback 500 `
  --db database/stock_data.db
```

CLI 输出基准日期、基准价、5/20/60 日上涨概率、趋势和当前实际触发的形态。

## Python：从 QuoteAPI 分析

```python
from quote_api import QuoteAPIFactory
from quantitative.analysis import QuantitativeAnalysisService

api = QuoteAPIFactory.create_with_cache("futu")
service = QuantitativeAnalysisService(api)

report = service.analyze(
    "Tencent",
    anchor_date="2026-08-20",
    lookback=500,
)

if report:
    print(report.summary)
    print(report.to_dict())

QuoteAPIFactory.clear_cache()
```

`analyze()` 会把 `anchor_date` 作为行情查询的 `end_date`，并在服务内部再次过滤
日期。没有行情时返回 `None`。

## Python：分析已有 K 线

```python
from quote_api.db_api import DbQuoteAPI
from quantitative.analysis import QuantitativeAnalysisService

service = QuantitativeAnalysisService(DbQuoteAPI())
report = service.analyze_quotes(
    "Tencent",
    quotes,
    anchor_date="2026-08-20",
)
```

`analyze_quotes()` 适合回放、测试和上层工具已经取得行情的场景，可以避免再次访问
数据源。

如果希望同时保存本次计算的特征：

```python
from quantitative.features import FeatureRepository

with FeatureRepository() as feature_repository:
    service = QuantitativeAnalysisService(
        api,
        feature_repository=feature_repository,
    )
    report = service.analyze_quotes(
        "Tencent",
        quotes,
        persist_features=True,
    )
```

只有显式设置 `persist_features=True` 且注入 `FeatureRepository` 才会写特征表。

## 输出模型

`QuantitativeReport` 主要字段：

| 字段 | 含义 |
|---|---|
| `symbol`、`name` | 标的内部 key 与展示名 |
| `anchor_date` | 分析时点 |
| `anchor_price` | 时点收盘价 |
| `data_source` | 行情来源 |
| `data_days` | 实际使用的交易日数 |
| `signals` | 所有规则结果，包括 inactive |
| `active_signals` | 仅实际触发的形态属性 |
| `horizons` | 5/20/60 日聚合结果 |
| `summary` | 控制台文本摘要 |

每个 `HorizonAnalysis` 包含：

```text
horizon_days
probability_up
probability_down
confidence
contributing_signals
trend
```

趋势阈值为：上涨概率不低于 60% 为偏多，不高于 40% 为偏空，其余为中性。

## 聚合规则

聚合器只处理 `active=True` 的形态。对每条形态和周期：

1. 从 artifact 读取该形态的 `success_rate` 和 `weight`；
2. 用 `samples / (samples + 50)` 作为样本可靠性，把命中率向 50% 收缩；
3. 看多形态的上涨证据为收缩后的命中率；
4. 看空形态的上涨证据为 `1 - 收缩后的命中率`；
5. 有效权重为 `weight * max(strength, 0)`；
6. 对上涨证据做加权平均。

收缩公式为：

```text
calibrated_rate = 0.5 + (success_rate - 0.5) * samples / (samples + 50)
```

它避免极小样本的极端命中率对最终概率产生过大影响；原始命中率和样本数仍会在
报告中分别展示。

没有历史统计或样本数为 0 时，当前先验为：

```text
success_rate = 0.55
weight = 0.05
```

这是低置信度兜底，不应替代正式回测。没有 active signal 时，上涨/下跌概率均为
50%。最终概率限制在 5%～95%，避免输出伪确定性。

`confidence` 反映平均有效权重，不是传统置信区间，也不是“预测正确概率”。

## 依赖注入

服务可以替换以下组件：

```python
service = QuantitativeAnalysisService(
    quote_api=my_api,
    feature_repository=my_feature_repository,
    artifact_repository=my_artifact_repository,
    calculator=my_calculator,
    signal_engine=my_signal_engine,
)
```

这适合测试、研究规则集合、使用不同统计文件，以及严格控制数据版本。

## 历史时点与 PIT 边界

`anchor_date` 能保证本次行情、特征和形态只使用该日期之前的数据。但默认
`BacktestArtifactRepository` 始终加载当前 `signal_statistics.json`。

如果该文件的 `data_cutoff` 晚于 `anchor_date`，那么行情判断仍是时点正确的，
但模型权重使用了分析日之后的统计，不属于严格的历史模型回放。严格 PIT 研究应：

1. 用截止到目标日期的数据生成独立 artifact；
2. 保存到带 cutoff 的文件；
3. 将对应 `BacktestArtifactRepository(path)` 注入分析服务。

当前代码不会自动选择历史版本 artifact。

## 与 stock_advisor 的区别

`QuantitativeAnalysisService` 只给出形态统计聚合结果。`tools/stock_advisor` 在此基础
上额外组合：

- 特征空间的历史相似态分析；
- PIT 财报快照；
- 长期财务趋势和估值；
- Markdown 报告，包括每个触发形态的名义方向、回测有效方向、反向标记、历史
  命中率、样本数、权重占比和对最终概率的贡献。

stock_advisor 会明确区分形态加权模型与历史相似态模型，并使用可靠性加权凸组合
生成综合概率。相似态可靠性来自距离质量、有效样本量和逐时点 Brier 校准；若没有
正的校准技能，则只展示该子模型，不让它影响综合概率。

因此核心量化判断优先调用 analysis service，完整研究报告使用 stock_advisor。

相关文档：[回测](quantitative_backtesting.md)、[架构](../architecture.md)。
