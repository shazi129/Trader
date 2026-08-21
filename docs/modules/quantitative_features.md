# quantitative.features 使用说明

`quantitative.features` 将标准日 K 线转换成可查询、可存储的技术特征。它是基础
K 线到 RSI、MACD、均线、波动率等数值的唯一业务入口。

```text
list[DailyQuote]
    → FeatureCalculator.compute
    → list[FeatureSnapshot]
    → FeatureRepository.save_many
```

## 模块结构

| 文件 | 职责 |
|---|---|
| `catalog.py` | 特征 key、分组和说明的唯一目录 |
| `calculator.py` | 调用 `quantitative.indicators` 并生成完整特征序列 |
| `models.py` | `FeatureSnapshot` 数据模型 |
| `repository.py` | `quant_feature_daily` 领域仓储 |
| `materialization.py` | 行情读取、计算、落库的应用入口 |

`quantitative.indicators` 只提供序列数学函数；`features` 才负责将结果命名为稳定的
业务 key，并与标的、日期绑定。

## 计算特征

```python
from quote_api.repository import MarketDataRepository
from quantitative.features import FeatureCalculator

with MarketDataRepository() as market_repository:
    quotes = market_repository.get_range("Tencent")

snapshots = FeatureCalculator().compute("Tencent", quotes)
latest = snapshots[-1]

print(latest.date)
print(latest.get("rsi_14"))
print(latest.get("macd_hist"))
print(latest.get("ma_20"))
```

计算器具有以下契约：

- 输入为空时返回空列表；
- 输入会按日期排序；
- 输出与输入等长且日期一一对应；
- 预热窗口不足的值为 `None`，不会用 `0.0` 冒充有效值；
- 计算器不访问网络和数据库；
- 每个时点的特征只依赖该时点及之前的行情。

## 特征目录

```python
from quantitative.features.catalog import (
    FEATURE_BY_KEY,
    FEATURE_KEYS,
    FEATURE_SPECS,
)

for spec in FEATURE_SPECS:
    print(spec.key, spec.group, spec.description)
```

当前主要分组：

| 分组 | 示例 |
|---|---|
| `trend` | MA、EMA、价格/均线、布林带、MACD、ATR、ADX |
| `momentum` | RSI、KDJ、5～252 日动量、CCI、Williams %R |
| `volume` | OBV、VPT、ADL、MFI、Force Index、量比 |
| `risk` | 历史波动率、最大回撤、Sharpe、Sortino、Calmar、偏度峰度 |
| `liquidity` | 换手率、成交额均值、Amihud、量价相关、资金强度 |

数据库列直接由 `FEATURE_KEYS` 生成，不存在第二份手工字段映射。

## 特征快照

`FeatureSnapshot` 表示一个标的在一个交易日的完整特征：

```python
snapshot.symbol
snapshot.date
snapshot.values
snapshot.get("rsi_14")
```

读取不存在的 key 会得到 `None`。规则代码应显式处理 `None`，不要把数据不足解释
为中性、看多或看空。

## 保存与查询

```python
from quantitative.features import FeatureRepository

with FeatureRepository() as repository:
    repository.save_many(snapshots)
    latest_date = repository.latest_date("Tencent")
    stored = repository.get_range("Tencent", end_date="2026-08-20")
    ranking = repository.cross_section_rank(
        "momentum_20", "2026-08-20", top_n=20
    )
```

公开接口：

| 方法 | 作用 |
|---|---|
| `save(snapshot)` | 保存一个快照 |
| `save_many(snapshots)` | 批量 UPSERT |
| `latest_date(symbol)` | 最新特征日期 |
| `count(symbol)` | 快照数量 |
| `get_range(symbol, start, end)` | 读取日期升序序列 |
| `cross_section_rank(feature, date, ...)` | 同日跨标的排序 |
| `delete_symbol(symbol)` | 删除该标的全部特征 |

未知的横截面特征名会抛出 `ValueError`，防止将用户输入直接拼接为 SQL 列名。

## 一键物化

命令行：

```powershell
# 从线上拉取/复用行情缓存，然后写入特征仓储
python -m quantitative.cli features Tencent --api futu

# 只用本地 kline_daily
python -m quantitative.cli features Tencent --api db

# 重新从 provider 拉取完整区间
python -m quantitative.cli features Tencent --api futu --force-refresh
```

Python：

```python
from quantitative.features import materialize_symbol

count = materialize_symbol(
    "Tencent",
    source="db",
    db_path="database/stock_data.db",
)
```

`materialize_symbol()` 会完整重算该标的特征并 UPSERT。它不是增量特征算法；长历史
数据会重新计算，以确保所有滚动窗口一致。

## 新增特征

1. 在 `quantitative/indicators/` 添加或复用纯序列函数；
2. 在 `FEATURE_SPECS` 注册唯一 key、分组和说明；
3. 在 `FeatureCalculator.compute()` 将序列分配到该 key，并给出正确预热长度；
4. 添加已知输入输出和仓储 round-trip 测试；
5. 重新物化历史特征；
6. 若形态规则依赖该特征，重新生成回测统计。

不要在 `FeatureCalculator` 中写多空阈值；例如“RSI < 30”属于 signal，不属于
feature。

## 常见问题

- `FeatureRepository` 初始化时会根据目录自动增加新列，但不会删除、重命名旧列。
- `FeatureVersion` 当前为 `1`。公式发生不兼容变化时，应提升版本策略并重建历史
  快照，而不是混用两种口径。
- `turnover_rate=0` 可能表示 provider 未提供换手率，不一定表示真实换手为零。
- 特征仓储只是加速查询；信号引擎也可以直接使用内存中计算出的快照。

相关文档：[形态判断](quantitative_signals.md)、[数据表](../data_schema.md)。
