# quantitative.signals 使用说明

`quantitative.signals` 负责根据行情与已计算特征判断指标形态，例如金叉、背离、
超买超卖和双顶双底。它输出有明确方向和是否触发状态的 `SignalResult`。

该模块不获取行情、不访问数据库，也不重复计算 RSI、MACD 等指标。

## 核心契约

```python
from quantitative.signals import SignalContext, SignalEngine

context = SignalContext(
    symbol="Tencent",
    quotes=quotes,
    features=snapshots,
)
results = SignalEngine().evaluate(context)
active = [result for result in results if result.active]
```

`SignalContext` 要求行情和特征非空，并且两者最后一条日期相同。常用属性：

| 属性/方法 | 含义 |
|---|---|
| `anchor_date` | 当前判断日期 |
| `anchor_price` | 当前收盘价 |
| `latest` | 当前 `FeatureSnapshot` |
| `previous` | 前一日快照或 `None` |
| `feature_series(key)` | 某特征的历史序列 |

`SignalResult` 字段：

| 字段 | 约束 |
|---|---|
| `signal_id` | 跨版本稳定的唯一 ID |
| `name` | 展示名称 |
| `category` | crossover、momentum、divergence 等类别 |
| `active` | 当前时点是否触发 |
| `direction` | 看多 `1`、看空 `-1`、中性 `0` |
| `value` | 用于解释的代表数值，可为空 |
| `strength` | 聚合时使用的非负强度，默认 `1.0` |
| `description` | 人类可读解释 |

未触发形态必须满足 `active=False, direction=0`。不能用 `direction=-1` 表达
“看多形态未触发”，否则聚合器会错误地把未触发当成看空。

## 内置形态

| ID | 名称 | 名义方向 | 类型 |
|---|---|---:|---|
| `ma_alignment_bullish` | 均线多头排列 | +1 | 状态 |
| `ma_alignment_bearish` | 均线空头排列 | -1 | 状态 |
| `ma_5_20_golden_cross` | MA5/MA20 金叉 | +1 | 事件 |
| `ma_5_20_death_cross` | MA5/MA20 死叉 | -1 | 事件 |
| `macd_golden_cross` | MACD 金叉 | +1 | 事件 |
| `macd_death_cross` | MACD 死叉 | -1 | 事件 |
| `bollinger_lower_touch` | 布林带下轨支撑 | +1 | 状态 |
| `bollinger_upper_touch` | 布林带上轨阻力 | -1 | 状态 |
| `rsi_14_oversold` | RSI 超卖 | +1 | 状态 |
| `rsi_14_overbought` | RSI 超买 | -1 | 状态 |
| `momentum_20_positive` | 20 日动量向上 | +1 | 状态 |
| `momentum_20_negative` | 20 日动量向下 | -1 | 状态 |
| `bullish_volume_expansion` | 上涨放量 | +1 | 状态 |
| `volatility_contraction` | 波动率收敛 | 由动量决定 | 状态 |
| `macd_top_divergence` | MACD 顶背离 | -1 | 近期事件 |
| `macd_bottom_divergence` | MACD 底背离 | +1 | 近期事件 |
| `price_double_top` | 双顶且跌破颈线 | -1 | 近期事件 |
| `price_double_bottom` | 双底且突破颈线 | +1 | 近期事件 |

形态的名义方向只是先验解释。最终分析会结合回测成功率；若某个名义看多形态长期
低于 50% 命中率，聚合器会把它视为经验上的反向证据。

## 显式注册表

所有生产规则必须加入 `quantitative.signals.registry.RULE_TYPES`：

```python
from quantitative.signals import RULE_TYPES

for rule_type in RULE_TYPES:
    print(rule_type.signal_id)
```

注册表不会扫描文件系统。这样可以保证：

- 规则顺序稳定；
- 重复 `signal_id` 在导入时立即失败；
- 研究脚本不会因为放进目录而自动进入生产分析；
- 回测与时点分析使用完全相同的规则集合。

## 新增形态

```python
from quantitative.signals import SignalContext, SignalRule


class StrongTrend(SignalRule):
    signal_id = "strong_trend"
    name = "强趋势"
    category = "trend"

    def evaluate(self, context: SignalContext):
        adx = context.latest.get("adx_14")
        momentum = context.latest.get("momentum_20")
        if adx is None or momentum is None:
            return self.result(False, 0, description="特征数据不足")
        active = adx > 25 and momentum > 0
        return self.result(
            active,
            1,
            value=adx,
            description=f"ADX14={adx:.2f}, MOM20={momentum:.2f}%",
        )
```

然后：

1. 将类加入 `RULE_TYPES`；
2. 添加触发、不触发、预热不足三个测试；
3. 运行全股票池回测，生成该 `signal_id` 的样本统计；
4. 检查各周期样本量，而不是只看成功率。

## 事件与状态

- 金叉/死叉只在穿越发生当天触发；
- 均线排列、超买超卖可以连续多日触发；
- 背离和双顶双底使用近期约束，避免一个旧形态无限期保持 active；
- 双顶需要跌破颈线，双底需要突破颈线，不只是两个价格接近的极值。

连续状态会产生相关样本，不能把每一天都理解为独立实验。解释回测结果时需要结合
市场、标的和样本聚类风险。

## 容错

`SignalEngine` 会隔离单条规则异常并记录日志，其他规则仍继续运行。这个行为用于
保证报告可用，不代表规则错误可以被忽略；测试和日志中出现的异常仍应修复。

相关文档：[特征](quantitative_features.md)、[回测](quantitative_backtesting.md)。
