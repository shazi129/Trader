# 股票技术指标与量化特征体系

> 适用数据：沪深300、恒生指数、标普500成分股，日K线，近10年  
> 目标：同时兼顾**传统技术分析**与**量化/机器学习建模**。  
> 原则：指标用于描述价格、趋势、动量、波动、成交量、形态和市场环境；最终是否有效，应通过样本外回测、IC、Rank IC、收益/风险指标验证，而不是因为“经典”就默认有效。

---

## 1. 指标体系总览

建议将指标分为以下 9 类：

1. 原始价格与收益率
2. 趋势指标
3. 动量与超买超卖
4. 波动率
5. 成交量
6. K线与价格形态
7. 突破、支撑阻力与回撤
8. 横截面因子
9. 市场环境、Beta与相关性

推荐优先级：

| 类别 | 推荐程度 | 代表指标 |
|---|---|---|
| 收益率 | ★★★★★ | Return / ROC / Momentum |
| 趋势 | ★★★★★ | MA / EMA / MACD / ADX |
| 动量 | ★★★★★ | RSI / ROC |
| 波动率 | ★★★★★ | Std / ATR / Bollinger |
| 成交量 | ★★★★☆ | Volume Ratio / OBV / MFI |
| K线形态 | ★★★★☆ | Body / Shadow / Gap |
| 突破与回撤 | ★★★★★ | High/Low / Drawdown / Breakout |
| 横截面 | ★★★★★ | Rank / Percentile / Relative Strength |
| 市场环境 | ★★★★★ | Market Return / Volatility / Beta |

---

# 2. 原始价格与收益率

不要只保存 OHLCV，建议计算标准化收益率。

## 2.1 单日收益率

$$
R_t = \frac{Close_t}{Close_{t-1}}-1
$$

字段：

```text
return_1d
```

## 2.2 N日收益率

建议：

```text
return_3d
return_5d
return_10d
return_20d
return_60d
return_120d
return_250d
```

公式：

$$
R_{N,t}=\frac{Close_t}{Close_{t-N}}-1
$$

这是量化模型最基础、最重要的一组特征之一。

---

# 3. 趋势指标

## 3.1 SMA

简单移动平均：

$$
SMA_N=\frac{1}{N}\sum_{i=0}^{N-1}Close_{t-i}
$$

推荐：

```text
SMA5
SMA10
SMA20
SMA60
SMA120
SMA250
```

传统分析：

- MA5：短线
- MA20：月度趋势
- MA60：中期趋势
- MA120：中长期趋势
- MA250：年度趋势

量化模型建议进一步计算：

```text
close_ma5_ratio
close_ma20_ratio
close_ma60_ratio
close_ma120_ratio
close_ma250_ratio
```

例如：

$$
CloseMARatio_{20}=\frac{Close}{MA20}-1
$$

## 3.2 EMA

推荐：

```text
EMA5
EMA10
EMA20
EMA60
EMA120
```

EMA对近期价格更敏感。

## 3.3 均线关系

非常适合量化：

```text
ma5_ma20_ratio
ma10_ma20_ratio
ma20_ma60_ratio
ma60_ma120_ratio
ma120_ma250_ratio
```

也可以计算：

```text
ma5_slope
ma20_slope
ma60_slope
```

用于描述趋势方向。

## 3.4 MACD

经典参数：

```text
fast = 12
slow = 26
signal = 9
```

计算：

$$
DIF=EMA_{12}-EMA_{26}
$$

$$
DEA=EMA_9(DIF)
$$

$$
MACD=2(DIF-DEA)
$$

建议保存：

```text
macd_dif
macd_dea
macd_hist
macd_hist_change
```

传统分析：

- DIF/DEA金叉
- DIF/DEA死叉
- 零轴上下
- 柱体放大/缩小
- 顶背离/底背离

量化分析不要只保存“金叉=1”，应保留连续数值。

## 3.5 ADX

用于衡量趋势强度，而不是简单判断涨跌方向。

推荐：

```text
ADX14
PLUS_DI14
MINUS_DI14
```

适合判断：

> 当前市场究竟是趋势行情还是震荡行情。

## 3.6 Aroon

推荐：

```text
Aroon_Up_25
Aroon_Down_25
Aroon_Oscillator_25
```

用于判断近期高点/低点出现的位置。

---

# 4. 动量与超买超卖

## 4.1 RSI

**建议保留。**

经典：

```text
RSI14
```

建议同时：

```text
RSI6
RSI14
RSI24
```

传统分析：

- RSI > 70：超买
- RSI < 30：超卖
- RSI > 50：偏强
- RSI < 50：偏弱

量化建议：

```text
rsi6
rsi14
rsi24
rsi14_change
rsi14_distance_50
```

不要只使用：

```text
rsi_over_70 = 1
```

连续数值的信息量更高。

## 4.2 ROC

推荐优先级很高。

$$
ROC_N=\frac{Close_t}{Close_{t-N}}-1
$$

实际上与N日收益率高度相关，因此通常不必重复存储完全相同的字段。

## 4.3 Momentum

$$
Momentum_N=Close_t-Close_{t-N}
$$

如果不同股票价格尺度差异很大，更推荐使用 ROC/收益率。

## 4.4 Stochastic

随机指标：

```text
K
D
```

推荐：

```text
KDJ_K
KDJ_D
KDJ_J
```

传统技术分析中常用：

- K/D金叉
- K/D死叉
- 超买
- 超卖

### KDJ的量化定位

KDJ可以保留，但优先级低于 RSI + ROC。

原因：

KDJ、RSI、Stochastic、短期收益率之间存在明显信息重叠。

因此建议：

> 数据库可以计算KDJ；模型最终是否使用KDJ，由IC/回测决定。

## 4.5 CCI

推荐：

```text
CCI20
```

用于衡量价格偏离统计平均水平的程度。

## 4.6 Williams %R

推荐：

```text
WilliamsR14
```

与Stochastic高度相关，属于可选指标。

---

# 5. 波动率指标

这是量化研究中的核心类别。

## 5.1 收益率标准差

推荐：

```text
volatility_5
volatility_10
volatility_20
volatility_60
volatility_120
```

通常将日收益率标准差年化：

$$
\sigma_N=Std(R_{t-N+1:t})\sqrt{252}
$$

## 5.2 ATR

Average True Range。

True Range：

$$
TR_t=max(
High-Low,
|High-Close_{t-1}|,
|Low-Close_{t-1}|
)
$$

推荐：

```text
ATR14
ATR20
ATR60
```

更适合量化的形式：

```text
atr14_ratio = ATR14 / Close
```

这样不同价格股票可以比较。

## 5.3 Bollinger Bands

经典：

```text
period = 20
std = 2
```

$$
Upper=MA20+2\sigma_{20}
$$

$$
Lower=MA20-2\sigma_{20}
$$

建议保存：

```text
bollinger_upper
bollinger_lower
bollinger_mid
bollinger_width
bollinger_position
```

其中：

$$
Position=\frac{Close-Lower}{Upper-Lower}
$$

## 5.4 Parkinson Volatility

利用最高价和最低价：

$$
\sigma_P=
\sqrt{
\frac{1}{4N\ln2}
\sum
\ln^2\left(\frac{High}{Low}\right)
}
$$

可作为传统收盘收益率波动率的补充。

## 5.5 Garman-Klass

结合OHLC：

$$
\sigma_{GK}^2
=
\frac{1}{N}
\sum
\left[
\frac{1}{2}\ln^2(H/L)
-
(2\ln2-1)\ln^2(C/O)
\right]
$$

属于进阶特征。

---

# 6. 成交量指标

前提：数据必须有可靠的成交量。

## 6.1 Volume Ratio

非常推荐。

$$
VolumeRatio_N=
\frac{Volume_t}{MA(Volume,N)}
$$

建议：

```text
volume_ratio_5
volume_ratio_20
volume_ratio_60
```

传统分析：

> 放量上涨、放量下跌、缩量调整。

量化分析：

> 成交量异常是否预测未来收益或波动率？

## 6.2 OBV

On Balance Volume。

建议：

```text
OBV
OBV_change_20
OBV_slope_20
```

## 6.3 MFI

Money Flow Index：

```text
MFI14
MFI20
```

兼顾价格和成交量。

## 6.4 CMF

Chaikin Money Flow：

```text
CMF20
```

可选。

## 6.5 VWAP

日线数据中可使用当日VWAP（如果原始数据有足够的成交明细/可靠VWAP）。

如果只有日K OHLCV，则不要伪造高精度VWAP。

---

# 7. K线结构特征

相比“锤头线=1”，量化模型更适合直接使用K线几何结构。

## 7.1 实体

$$
Body=Close-Open
$$

建议：

```text
body
body_abs
body_ratio
```

## 7.2 振幅

$$
Range=High-Low
$$

建议：

```text
range
range_ratio
```

## 7.3 上影线

$$
UpperShadow=High-max(Open,Close)
$$

## 7.4 下影线

$$
LowerShadow=min(Open,Close)-Low
$$

建议：

```text
upper_shadow_ratio
lower_shadow_ratio
```

## 7.5 缺口

$$
Gap=\frac{Open_t}{Close_{t-1}}-1
$$

字段：

```text
gap
gap_up
gap_down
```

推荐进一步计算：

```text
gap_abs
large_gap_flag
```

---

# 8. 经典K线形态

传统技术分析建议识别：

## 单K

- Doji 十字星
- Hammer 锤头线
- Hanging Man 上吊线
- Inverted Hammer 倒锤头
- Shooting Star 流星
- Marubozu 光头光脚

## 双K

- Bullish Engulfing
- Bearish Engulfing
- Harami
- Piercing
- Dark Cloud Cover

## 三K

- Morning Star
- Evening Star
- Three White Soldiers
- Three Black Crows

建议数据库字段：

```text
pattern_doji
pattern_hammer
pattern_shooting_star
pattern_bullish_engulfing
pattern_bearish_engulfing
pattern_morning_star
pattern_evening_star
```

取值可以是：

```text 0 / 1
```

但机器学习中不要只依赖这些0/1特征，应同时保留：

```text
body_ratio
upper_shadow_ratio
lower_shadow_ratio
preceding_return_5d
preceding_return_20d
volume_ratio_20
```

---

# 9. 突破指标

## 9.1 N日最高价

建议：

```text
high_20
high_60
high_120
high_250
```

以及：

```text
distance_to_high_20
distance_to_high_60
distance_to_high_120
distance_to_high_250
```

公式：

$$
DistanceHigh_N=\frac{Close}{RollingHigh_N}-1
$$

## 9.2 N日最低价

对应：

```text
low_20
low_60
low_120
low_250

distance_to_low_20
distance_to_low_60
distance_to_low_120
distance_to_low_250
```

## 9.3 突破标记

例如：

```text
breakout_high_20
breakout_high_60
breakout_high_120
breakout_high_250
```

注意计算时必须使用历史窗口，避免把当前价格与包含未来数据的窗口比较。

---

# 10. 回撤与趋势位置

## 10.1 当前回撤

$$
Drawdown_N=
\frac{Close}{RollingMax(Close,N)}-1
$$

建议：

```text
drawdown_20
drawdown_60
drawdown_120
drawdown_250
```

## 10.2 距离历史高点

```text
distance_high_20
distance_high_60
distance_high_120
distance_high_250
```

## 10.3 距离历史低点

```text
distance_low_20
distance_low_60
distance_low_120
distance_low_250
```

## 10.4 历史最大回撤

建议：

```text
max_drawdown_20
max_drawdown_60
max_drawdown_120
max_drawdown_250
```

这些指标对于研究：

> 大跌后反弹、趋势回撤、超跌反转

非常有价值。

---

# 11. 连续上涨/下跌

建议：

```text
consecutive_up_days
consecutive_down_days
```

还可以计算：

```text
up_ratio_5
up_ratio_10
up_ratio_20
up_ratio_60
```

例如：

$$
UpRatio_{20}
=
\frac{\#(R_i>0)}{20}
$$

---

# 12. 统计特征

机器学习非常适合加入。

## 12.1 收益率统计

建议：

```text
return_mean_20
return_std_20
return_skew_20
return_kurt_20

return_mean_60
return_std_60
return_skew_60
return_kurt_60
```

## 12.2 极值

```text
max_return_20
min_return_20
max_return_60
min_return_60
```

## 12.3 上涨概率

```text
positive_ratio_5
positive_ratio_20
positive_ratio_60
```

---

# 13. 横截面因子

这是本项目非常值得重点建设的一层。

每天在同一市场内，对所有股票进行排名。

例如：

```text
return_rank_5
return_rank_20
return_rank_60
return_rank_120

volatility_rank_20
volume_rank_20
rsi_rank_20

drawdown_rank
distance_high_rank
```

推荐转换成：

```text
percentile_rank
```

范围：

```text
0 ~ 1
```

例如：

```text
return_20_percentile = 0.95
```

代表该股票过去20日收益率处于市场前5%。

---

# 14. 相对强弱

除了绝对收益率，还应计算相对市场表现。

例如：

$$
RelativeStrength_i=
R_i-R_{market}
$$

建议：

```text
relative_return_5
relative_return_20
relative_return_60
relative_return_120
```

也可以：

$$
RelativePrice=
\frac{StockPrice}{MarketIndex}
$$

然后计算相对价格的趋势：

```text
relative_price_ma20
relative_price_ma60
relative_price_momentum
```

这对于选股模型非常重要。

---

# 15. Beta与市场相关性

利用指数作为市场基准。

## 15.1 Beta

$$
\beta_i=
\frac{Cov(R_i,R_m)}
{Var(R_m)}
$$

建议：

```text
beta_20
beta_60
beta_120
beta_250
```

## 15.2 相关系数

```text
corr_market_20
corr_market_60
corr_market_120
corr_market_250
```

可以帮助模型区分：

- 高Beta股票
- 低Beta股票
- 高市场相关性股票
- 相对独立股票

---

# 16. 市场环境特征

由于数据覆盖：

- 沪深300
- 恒生指数
- 标普500

建议建立市场状态层。

例如：

```text
CSI300_return_1d
CSI300_return_5d
CSI300_return_20d
CSI300_return_60d

HSI_return_1d
HSI_return_5d
HSI_return_20d
HSI_return_60d

SP500_return_1d
SP500_return_5d
SP500_return_20d
SP500_return_60d
```

以及：

```text
market_ma20_ratio
market_ma60_ratio
market_ma120_ratio
market_volatility_20
market_drawdown
```

最终可以定义：

```text
bull_market
bear_market
sideways_market
high_volatility
low_volatility
```

但对于机器学习，优先保留连续变量，不要过早离散化。

---

# 17. 传统技术分析信号

如果同时兼顾传统技术分析，可以增加一些“交易信号层”。

例如：

## 均线

```text
ma_golden_cross_5_20
ma_dead_cross_5_20
ma_golden_cross_20_60
ma_dead_cross_20_60
```

## MACD

```text
macd_golden_cross
macd_dead_cross
macd_above_zero
macd_below_zero
```

## RSI

```text
rsi_over_70
rsi_below_30
rsi_cross_50_up
rsi_cross_50_down
```

## KDJ

```text
kdj_golden_cross
kdj_dead_cross
kdj_overbought
kdj_oversold
```

## 突破

```text
breakout_20d
breakout_60d
breakout_120d
breakdown_20d
breakdown_60d
breakdown_120d
```

这些字段主要服务于：

- 传统技术分析
- 策略规则回测
- 可解释性
- 交易信号展示

机器学习则应尽量同时保留对应的连续原始特征。

---

# 18. 指标优先级

## 第一梯队：必须计算

```text
return_1d
return_5d
return_20d
return_60d
return_120d
return_250d

close_ma5_ratio
close_ma20_ratio
close_ma60_ratio
close_ma120_ratio
close_ma250_ratio

ma5_ma20_ratio
ma20_ma60_ratio
ma60_ma120_ratio

RSI14
ROC20
MACD

volatility_5
volatility_20
volatility_60
ATR14

volume_ratio_20

gap
body_ratio
upper_shadow_ratio
lower_shadow_ratio

drawdown_20
drawdown_60
drawdown_120
drawdown_250

distance_high_20
distance_high_60
distance_high_120
distance_high_250
```

## 第二梯队：强烈建议

```text
RSI6
RSI24

ADX14

Bollinger_width
Bollinger_position

volume_ratio_5
volume_ratio_60

OBV
MFI14

consecutive_up_days
consecutive_down_days

positive_ratio_20

return_skew_20
return_kurt_20

beta_60
corr_market_60

return_percentile_20
return_percentile_60
volatility_percentile
```

## 第三梯队：传统技术分析/扩展研究

```text
KDJ_K
KDJ_D
KDJ_J

CCI20
WilliamsR14

Aroon

CMF

Parkinson_volatility
GarmanKlass_volatility

candlestick_patterns
```

---

# 19. RSI与KDJ的最终建议

## RSI

**保留。**

建议：

```text
RSI6
RSI14
RSI24
```

原因：

- 传统技术分析非常常用
- 能描述动量/超买超卖
- 计算简单
- 对模型也有一定信息价值

## KDJ

**保留，但作为辅助指标。**

建议：

```text
KDJ_K
KDJ_D
KDJ_J
```

原因：

- 传统A股技术分析使用广泛
- 对震荡行情有一定参考价值
- 与RSI、Stochastic、短期动量存在较强重叠

不要默认KDJ有效，最终通过：

```text
IC
Rank IC
回测收益
Sharpe
最大回撤
样本外表现
```

判断是否进入最终模型。

---

# 20. 特征工程的重要原则

## 20.1 不要只保存“金叉/死叉”

错误：

```text
golden_cross = 1
```

更好的方式：

```text
ma5_ma20_ratio
ma5_ma20_ratio_change
ma5_slope
ma20_slope
```

然后再生成：

```text
golden_cross
```

用于传统策略。

---

## 20.2 不要大量加入高度相关指标

例如：

```text
RSI
Stochastic
KDJ
Williams %R
CCI
```

全部加入模型可能导致大量冗余。

应通过相关矩阵、VIF、特征重要性、IC等方法筛选。

---

## 20.3 所有特征必须避免未来函数

例如在交易日 T 计算：

```text
MA20
RSI14
Volatility20
```

只能使用：

```text
T及以前
```

的数据。

如果你的策略在收盘后产生信号，最稳妥的回测方式通常是：

```text
T日收盘
↓
计算T日指标
↓
T+1日开盘/成交
```

不要让T日收盘价参与信号后，又假设能够以T日收盘价成交。

---

# 21. 指标计算层建议

建议把整个系统拆成：

```text
Raw OHLCV
    │
    ↓
Basic Features
    │
    ├── Return
    ├── MA / EMA
    ├── Volatility
    └── Volume
    │
    ↓
Technical Indicators
    │
    ├── RSI
    ├── MACD
    ├── KDJ
    ├── ADX
    └── Bollinger
    │
    ↓
Pattern Features
    │
    ├── Candlestick
    ├── Gap
    ├── Breakout
    └── Drawdown
    │
    ↓
Cross-sectional Features
    │
    ├── Rank
    ├── Percentile
    ├── Relative Strength
    └── Beta
    │
    ↓
Market Regime
    │
    ↓
ML Feature Dataset
```

---

# 22. 最终推荐的数据字段分层

建议数据库不要把所有指标全部塞进原始K线表。

### price_daily

```text
symbol
trade_date
open
high
low
close
volume
amount
adjust_factor
```

### technical_features_daily

```text
symbol
trade_date

return_1d
return_5d
return_20d
return_60d
return_120d
return_250d

ma5_ratio
ma20_ratio
ma60_ratio
ma120_ratio
ma250_ratio

rsi6
rsi14
rsi24

macd_dif
macd_dea
macd_hist

kdj_k
kdj_d
kdj_j

adx14

volatility_5
volatility_20
volatility_60

atr14
bollinger_width
bollinger_position

volume_ratio_5
volume_ratio_20
volume_ratio_60

gap
body_ratio
upper_shadow_ratio
lower_shadow_ratio

drawdown_20
drawdown_60
drawdown_120
drawdown_250

distance_high_20
distance_high_60
distance_high_120
distance_high_250
```

### cross_section_features_daily

```text
symbol
trade_date

return_rank_5
return_rank_20
return_rank_60
return_rank_120

volatility_rank
volume_rank
rsi_rank

relative_return_20
relative_return_60

beta_60
beta_120
corr_market_60
```

### market_features_daily

```text
market
trade_date

return_1d
return_5d
return_20d
return_60d

ma20_ratio
ma60_ratio
ma120_ratio

volatility_20
volatility_60

drawdown
```

---

# 23. 预测目标（Label）

技术指标最终是为了预测未来。

建议不要只定义：

```text
tomorrow_up = 0 / 1
```

而是同时建立：

```text
future_return_1d
future_return_5d
future_return_20d
future_return_60d
```

以及风险目标：

```text
future_max_return_20d
future_max_drawdown_20d
future_volatility_20d
```

这样可以同时研究：

- 短线预测
- 中线趋势
- 动量
- 风险
- 最大回撤

---

# 24. 最终原则

这套体系的核心不是：

> “指标越多越好。”

而是：

> **传统技术分析负责提供可解释的市场描述；量化特征负责把这些描述转换成连续、可比较、可回测的数据；统计检验和样本外测试负责决定哪些特征真正有用。**

因此第一版建议重点建立：

**收益率 + 均线 + RSI + MACD + 波动率 + ATR + 成交量 + K线结构 + 突破/回撤 + 横截面排名 + Beta/市场环境。**

KDJ、CCI、Williams %R、Aroon、CMF等作为扩展层保留，不必一开始就全部进入模型。
