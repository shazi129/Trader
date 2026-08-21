# quantitative.backtesting 使用说明

`quantitative.backtesting` 用历史 K 线验证每条形态规则在不同持有周期上的方向命中
情况，生成样本量、成功率和可靠性权重。产物供时点分析聚合使用。

```text
历史 K 线
  → 全量因果特征
  → 每个历史 anchor 判断 active signals
  → 用 anchor + horizon 的收盘价验证方向
  → BacktestArtifact
```

## 最常用命令

```powershell
# 回测 STOCK_META 中全部股票
python -m quantitative.cli backtest

# 只回测指定标的
python -m quantitative.cli backtest --stocks Tencent,Alibaba,MaoTai

# 自定义数据库、最小历史长度和输出文件
python -m quantitative.cli backtest `
  --db database/stock_data.db `
  --min-history 120 `
  --output quantitative/backtesting/signal_statistics.json
```

命令只读取本地 `kline_daily`，不会线上拉取。需要更新行情时先运行：

```powershell
python tools/kline_fetcher/kline_fetcher.py run
```

不传 `--stocks` 时，标的来源是 `quote_api.stock_meta.STOCK_META`。本地 K 线不足
`min_history + max(horizons) + 1` 的标的会被跳过。若没有任何合格标的，命令返回
失败且不会覆盖现有统计文件。

控制台按形态输出 5、20、60 日的：

- 方向成功率；
- 样本量；
- 可靠性权重。

完整结果同时保存为 JSON。

## Python 接口

```python
from quote_api.repository import MarketDataRepository
from quantitative.backtesting import (
    BacktestArtifactRepository,
    SignalBacktester,
)

symbols = ["Tencent", "Alibaba", "MaoTai"]
with MarketDataRepository() as repository:
    datasets = {
        symbol: repository.get_range(symbol)
        for symbol in symbols
    }

artifact = SignalBacktester(min_history=120).run(datasets)
BacktestArtifactRepository().save(artifact)
```

自定义周期：

```python
backtester = SignalBacktester(horizons=(5, 10, 20), min_history=120)
artifact = backtester.run(datasets)
```

时点分析默认按 5、20、60 日读取；改变生产周期时，应同步调整分析调用方。

## 回测算法

对每个标的：

1. 按日期排序 K 线；
2. 使用 `FeatureCalculator` 一次性计算完整特征序列；
3. 从第 `min_history` 个可用 anchor 开始遍历；
4. 每个 anchor 最多向前保留 375 根 K 线构造 `SignalContext`；
5. 只统计 `active=True` 的形态；
6. 对每个 horizon 比较未来收盘价与 anchor 收盘价；
7. 实际方向和 `SignalResult.direction` 一致则计为成功。

特征是因果滚动计算，规则上下文止于 anchor；`anchor+horizon` 的未来价格只用于
事后验证，不会输入形态判断。因此单次回测流程没有行情未来函数。

当前标签定义为：

```text
future_close > anchor_close    实际方向 +1
future_close <= anchor_close   实际方向 -1
```

也就是说，持平被计入“非上涨”方向。

## 指标含义

`SignalMetric` 包含：

| 字段 | 含义 |
|---|---|
| `samples` | 该形态在该周期的触发样本数 |
| `successes` | 名义方向判断正确的次数 |
| `success_rate` | `successes / samples` |
| `weight` | 方向边际经过样本量收缩后的可靠性权重 |

权重公式：

```text
edge = abs(success_rate - 0.5) * 2
sample_shrinkage = samples / (samples + 50)
weight = edge * sample_shrinkage
```

因此：

- 50% 附近的规则权重接近 0；
- 极少样本即使成功率很高也会被降权；
- 成功率低于 50% 仍可能有较高权重，表示它具有稳定的反向信息；
- `success_rate` 是“按形态方向的命中率”，不是上涨概率。

例如看空形态成功率 70%，在分析时对应约 30% 的上涨证据；看空形态成功率
30%，则会被解释为约 70% 的反向上涨证据。

## 模型产物

默认文件：

```text
quantitative/backtesting/signal_statistics.json
```

`BacktestArtifact` 顶层字段：

| 字段 | 含义 |
|---|---|
| `model_version` | 统计模型版本 |
| `generated_at` | 生成时间 |
| `horizons` | 回测周期 |
| `universe` | 实际进入回测的标的池 |
| `data_cutoff` | 输入数据的最晚日期 |
| `metrics` | `signal_id → horizon → SignalMetric` |

读取统计：

```python
from quantitative.backtesting import BacktestArtifactRepository

artifact = BacktestArtifactRepository().load()
metric = artifact.metric("macd_golden_cross", 20)
if metric:
    print(metric.samples, metric.success_rate, metric.weight)
```

文件不存在时 `load()` 返回空 artifact，不抛出文件不存在异常。分析层会对没有统计
的已触发信号使用低置信度先验。

## 何时重新回测

以下变化后必须重建统计：

- 新增、删除或修改形态规则；
- 修改规则阈值或名义方向；
- 修改依赖特征的计算公式；
- 更换复权口径；
- 股票池或历史数据范围显著变化；
- 修改回测周期或最小历史长度。

可通过综合工具重建后继续出报告：

```powershell
python -m tools.stock_advisor.stock_advisor Tencent --rebuild-signal-stats
```

## 解读限制

- 连续多日 active 的状态形态会产生相互相关的样本；
- 当前实现没有计入手续费、滑点、停牌和可交易性；
- 成功率衡量方向，不衡量收益幅度或风险调整收益；
- 同一股票跨日期、不同股票同一宏观阶段均不完全独立；
- 样本内统计不等于样本外稳定性，正式研究还需滚动训练和样本外验证；
- artifact 记录 cutoff，但当前单文件存储不会自动保留每个历史 cutoff 的模型。

相关文档：[形态](quantitative_signals.md)、[时点分析](quantitative_analysis.md)。
