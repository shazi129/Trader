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

### 复用现有特征的扩展形态

以下形态只读取 `quant_feature_daily` 已有字段，不会增加数据库列或触发 schema
迁移。加入后内置信号总数为 52。

为兼容现有物化数据，DMI 规则会把库中按 Wilder 平滑和保存的 `adx_14`
除以 14，再按市场常用的 0～100 ADX 刻度判断 25 门槛；不需要重写历史特征。

| ID | 名称 | 名义方向 | 类型/确认条件 |
|---|---|---:|---|
| `price_ma_20_cross_up` | 价格上穿 MA20 | +1 | 当日穿越事件 |
| `price_ma_20_cross_down` | 价格下穿 MA20 | -1 | 当日穿越事件 |
| `ma_60_200_golden_cross` | MA60/MA200 金叉 | +1 | 中长期穿越事件 |
| `ma_60_200_death_cross` | MA60/MA200 死叉 | -1 | 中长期穿越事件 |
| `dmi_bullish_cross` | DMI 多头交叉 | +1 | +DI 上穿 -DI，且 ADX ≥ 25 |
| `dmi_bearish_cross` | DMI 空头交叉 | -1 | -DI 上穿 +DI，且 ADX ≥ 25 |
| `macd_zero_cross_up` | MACD 上穿零轴 | +1 | DIF 当日上穿零轴 |
| `macd_zero_cross_down` | MACD 下穿零轴 | -1 | DIF 当日下穿零轴 |
| `macd_hist_bullish_reexpand` | MACD 红柱重新放大 | +1 | 正柱缩短一日后再次增长 |
| `macd_hist_bearish_reexpand` | MACD 绿柱重新放大 | -1 | 负柱缩短一日后再次增长 |
| `bollinger_squeeze_breakout_up` | 布林带收口向上突破 | +1 | 前一日带宽处于近 60 个有效值的低 20%，随后突破上轨 |
| `bollinger_squeeze_breakout_down` | 布林带收口向下突破 | -1 | 前一日带宽处于近 60 个有效值的低 20%，随后跌破下轨 |
| `bollinger_lower_reentry` | 布林带下轨假跌破回归 | +1 | 前一日轨外、当日重新收回带内 |
| `bollinger_upper_reentry` | 布林带上轨假突破回归 | -1 | 前一日轨外、当日重新落回带内 |
| `kdj_oversold_golden_cross` | KDJ 低位金叉 | +1 | 前一日 K < 20，K 当日上穿 D |
| `kdj_overbought_death_cross` | KDJ 高位死叉 | -1 | 前一日 K > 80，K 当日下穿 D |
| `rsi_14_oversold_exit` | RSI 离开超卖区 | +1 | RSI 当日向上穿越 30 |
| `rsi_14_overbought_exit` | RSI 离开超买区 | -1 | RSI 当日向下穿越 70 |
| `mfi_14_oversold_exit` | MFI 离开超卖区 | +1 | MFI 当日向上穿越 20 |
| `mfi_14_overbought_exit` | MFI 离开超买区 | -1 | MFI 当日向下穿越 80 |
| `cci_20_breakout_up` | CCI 上穿 +100 | +1 | 趋势突破事件 |
| `cci_20_breakout_down` | CCI 下穿 -100 | -1 | 趋势突破事件 |
| `cci_20_oversold_exit` | CCI 离开超卖区 | +1 | CCI 向上穿越 -100 |
| `cci_20_overbought_exit` | CCI 离开超买区 | -1 | CCI 向下穿越 +100 |
| `williams_r_14_oversold_exit` | Williams %R 离开超卖区 | +1 | 向上穿越 -80 |
| `williams_r_14_overbought_exit` | Williams %R 离开超买区 | -1 | 向下穿越 -20 |
| `rsi_top_divergence` | RSI 顶背离 | -1 | 近期价格高点抬高、RSI 高点降低 |
| `rsi_bottom_divergence` | RSI 底背离 | +1 | 近期价格低点降低、RSI 低点抬高 |
| `mfi_top_divergence` | MFI 顶背离 | -1 | 近期价格高点抬高、MFI 高点降低 |
| `mfi_bottom_divergence` | MFI 底背离 | +1 | 近期价格低点降低、MFI 低点抬高 |
| `obv_top_divergence` | OBV 顶背离 | -1 | 近期价格高点抬高、OBV 高点降低 |
| `obv_bottom_divergence` | OBV 底背离 | +1 | 近期价格低点降低、OBV 低点抬高 |
| `bearish_price_volume_divergence` | 价涨量缩 | -1 | 5 日动量为正且当日量比低于 0.8 |
| `bearish_volume_expansion` | 下跌放量 | -1 | 5 日动量为负且当日量比高于 1.2 |

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
- 离开超买超卖区、零轴穿越、带外回归也只在发生当天触发；
- 均线排列、超买超卖可以连续多日触发；
- 背离和双顶双底使用近期约束，避免一个旧形态无限期保持 active；
- 双顶需要跌破颈线，双底需要突破颈线，不只是两个价格接近的极值。

布林带收口突破至少需要 20 个可比较的历史带宽值。DMI 交叉必须同时通过
ADX 强度确认，避免把无趋势区间内频繁发生的 DI 交叉全部计入样本。

连续状态会产生相关样本，不能把每一天都理解为独立实验。解释回测结果时需要结合
市场、标的和样本聚类风险。

## 容错

`SignalEngine` 会隔离单条规则异常并记录日志，其他规则仍继续运行。这个行为用于
保证报告可用，不代表规则错误可以被忽略；测试和日志中出现的异常仍应修复。

相关文档：[特征](quantitative_features.md)、[回测](quantitative_backtesting.md)。
