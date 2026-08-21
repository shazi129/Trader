# quantitative.backtesting 使用说明

`quantitative.backtesting` 用历史 K 线验证每条形态规则在不同持有周期上的方向命中
情况，生成事件样本、个股周期基准、显著性、走步样本外验证和可靠性权重。产物供
时点分析聚合使用。

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

- 方向成功率及对应的个股周期基准；
- 去重后的样本量；
- 最终采用方向（名义、样本外反向或禁用）；
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
5. 先统计每个标的、每个 horizon 在所有合格 anchor 上的无条件上涨基准；
6. 只统计 `active=True` 且方向非零的形态；背离连续保持 active 时只记录首次确认，
   不把同一背离的连续日期重复当作独立样本；
7. 对每个 horizon 比较未来收盘价与 anchor 收盘价；
8. 实际方向和 `SignalResult.direction` 一致则计为成功；
9. 每个事件按所属标的和周期匹配名义方向的基础成功率，而非固定与 50% 比较；
10. 只有单侧 95% 显著优于基准的方向才获得非零权重。

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
| `baseline_success_rate` | 相同标的构成、相同周期下名义方向的基础成功率 |
| `excess_success_rate` | 名义命中率减去对应基准 |
| `direction_multiplier` | `1` 名义有效、`-1` 样本外确认反向、`0` 禁用 |
| `z_score`、`p_value` | 相对基准的显著性统计 |
| `oos_*` | 反向关系的走步样本外表现及稳定折数 |
| `weight` | 通过验证后的超额命中率经样本量收缩后的权重 |

权重公式：

```text
edge = effective_success_rate - matched_baseline_success_rate
sample_shrinkage = samples / (samples + 50)
weight = max(edge, 0) * 2 * sample_shrinkage
```

其中显著性使用每个事件对应的 Bernoulli 基准方差计算单侧 z 值。未达到单侧 95%
门槛时，无论表面命中率多高，权重均为 0。极少样本即使命中率很高，也会同时受
显著性和样本收缩限制。

名义命中率低于基准不会自动变成反向指标。反向候选必须满足：

1. 全样本反向超额命中达到单侧 95% 显著；
2. 按日期使用前 50% 作为初始训练窗口，随后执行 3 段扩展窗口验证；
3. 每段只能使用在该验证段开始前已经完成 horizon 观察的训练样本和基准；
4. 至少 2 段样本外超额为正，且正向段占比不低于 2/3；
5. 合并样本外结果仍达到单侧 95% 显著。

任何条件不满足时 `direction_multiplier=0`，生产聚合不会使用该信号。

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
| `baselines` | `symbol → horizon → 无条件上涨概率` |
| `pooled_baselines` | 未见标的使用的全池上涨概率回退值 |
| `metrics` | `signal_id → horizon → SignalMetric` |

读取统计：

```python
from quantitative.backtesting import BacktestArtifactRepository

artifact = BacktestArtifactRepository().load()
metric = artifact.metric("macd_golden_cross", 20)
if metric:
    print(metric.samples, metric.success_rate, metric.weight)
```

文件不存在时 `load()` 返回空 artifact，不抛出文件不存在异常。没有统计、使用旧版
产物或未通过验证的已触发信号权重均为 0，不再使用 55% 低置信度先验。

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

- 背离已按确认事件去重；连续多日 active 的其他状态形态仍会产生相关样本；
- 当前实现没有计入手续费、滑点、停牌和可交易性；
- 成功率衡量方向，不衡量收益幅度或风险调整收益；
- 同一股票跨日期、不同股票同一宏观阶段均不完全独立；
- 反向解释已有走步样本外门槛；名义方向目前仍使用全样本显著性，正式研究可继续
  扩展为所有方向的滚动训练和样本外验证；
- artifact 记录 cutoff，但当前单文件存储不会自动保留每个历史 cutoff 的模型。

相关文档：[形态](quantitative_signals.md)、[时点分析](quantitative_analysis.md)。
