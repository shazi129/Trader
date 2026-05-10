# 数据库 Schema

> 默认数据库文件：`database/stock_data.db`，由 `database.stock_db_utils.StockDB` 管理。
> 一切 DDL 都在 `StockDB._ensure_schema()` 启动时自动建表 + `ALTER TABLE` 补列，
> **不需要手动迁移**。

## 总览

| # | 表名 | 角色 | 列数 | 主键 | 索引 |
|---|---|---|---|---|---|
| 1 | `kline_daily`        | 原始 K 线        | 9 | `(Symbol, Date)` | `idx_kline_daily_date` |
| 2 | `factor_indicator`   | 基础技术指标     | 21 | `(Symbol, Date)` | `idx_factor_indicator_date` |
| 3 | `factor_trend`       | 趋势因子         | 12 | `(Symbol, Date)` | `idx_factor_trend_date` |
| 4 | `factor_momentum`    | 动量因子         | 18 | `(Symbol, Date)` | `idx_factor_momentum_date` |
| 5 | `factor_volume`      | 成交量因子       | 9 | `(Symbol, Date)` | `idx_factor_volume_date` |
| 6 | `factor_risk`        | 风险因子         | 11 | `(Symbol, Date)` | `idx_factor_risk_date` |
| 7 | `factor_ma_ratio`    | 均线比率 / 周线  | 12 | `(Symbol, Date)` | `idx_factor_ma_ratio_date` |

通用约定：

- `Symbol` 是 `quote_api.stock_meta.STOCK_META` 的 `name_key`（项目内部逻辑标识，
  不是交易所代码）。
- `Date` 字符串 `YYYY-MM-DD`。
- 价格列保留 4 位小数，因子列保留 6 位小数（`StockDB.PRECISION_*`）。
- 全部表都用 `INSERT OR REPLACE`（UPSERT），重复跑无副作用。

---

## 1. `kline_daily` —— 原始 K 线

| 列 | 类型 | 说明 |
|---|---|---|
| `Symbol` | TEXT NOT NULL | name_key |
| `Date` | DATE NOT NULL | 交易日 |
| `Open` / `Close` / `High` / `Low` | REAL | 价格（4 位小数） |
| `Volume` | REAL | 成交量 |
| `Turnover` | REAL | 成交额（4 位小数） |
| `TurnoverRate` | REAL | 换手率（数据源未提供时为 0） |

> `pre_close` 不入库——前复权序列下 `pre_close = 上一行 close`，
> 属可派生字段，分析层按需现算。

## 2. `factor_indicator` —— 基础技术指标

来自 `quantitative.factors.basic`（`KlineIndicator` 基础字段）。

| 列 → 属性 | 含义 |
|---|---|
| `MA5/10/20/30/60/120/250` → `ma5..ma250` | 简单移动均线 |
| `BollUp` / `BollLow` → `boll_up` / `boll_low` | 布林带上下轨 |
| `K` / `D` / `J` → `k` / `d` / `j` | KDJ 三线 |
| `Dif` / `Dea` / `MACD` → `dif` / `dea` / `macd` | MACD 三件套 |
| `RSI1` / `RSI2` / `RSI3` → `rsi1..rsi3` | 不同窗口 RSI |
| `ADOSC` → `adosc` | 累积/派发震荡指标 |

## 3. `factor_trend` —— 趋势因子

来自 `quantitative.factors.trend`。

| 列 → 属性 | 含义 |
|---|---|
| `EMA12/26/50` → `ema12/26/50` | 指数移动均线 |
| `MACD_HIST` → `macd_hist` | MACD 柱 |
| `ADX` / `Plus_DI` / `Minus_DI` → `adx/plus_di/minus_di` | DMI 体系 |
| `TR` / `ATR` / `ATR_PCT` → `tr/atr/atr_pct` | 真实波动幅度 |

## 4. `factor_momentum` —— 动量因子

来自 `quantitative.factors.momentum`。

| 列 → 属性 | 含义 |
|---|---|
| `MOM1W/2W/1M/3M/6M/9M/12M` → `mom1w..mom12m` | 不同窗口动量 |
| `ROC1W/2W/1M/3M/6M/9M/12M` → `roc1w..roc12m` | 价格变化率 |
| `CCI` → `cci` | 顺势指标 |
| `WilliamsR` → `williams_r` | 威廉指标 |

## 5. `factor_volume` —— 成交量因子

来自 `quantitative.factors.volume`。

| 列 → 属性 | 含义 |
|---|---|
| `OBV` → `obv` | 能量潮 |
| `VPT` → `vpt` | 量价趋势 |
| `ADL` → `adl` | 累积/派发线 |
| `MFI` → `mfi` | 资金流量指数 |
| `ForceIndex1/13/21` → `force_index1/13/21` | 强力指数 |

## 6. `factor_risk` —— 风险因子

来自 `quantitative.factors.risk`。

| 列 → 属性 | 含义 |
|---|---|
| `HV20` / `HV60` → `hv20/hv60` | 历史波动率 |
| `MaxDrawdown` → `max_drawdown` | 最大回撤 |
| `Volatility` → `volatility` | 收益波动率 |
| `Sharpe` / `Sortino` / `Calmar` → `sharpe/sortino/calmar` | 风险调整收益 |
| `Skewness` / `Kurtosis` → `skewness/kurtosis` | 收益分布偏度 / 峰度 |

## 7. `factor_ma_ratio` —— 均线比率 / 周线

来自 `quantitative.factors.ma_ratio`。

| 列 → 属性 | 含义 |
|---|---|
| `MA_Ratio_5/10/20/60/200` → `ma_ratio_5..200` | 收盘价 / 对应均线 |
| `MA200` → `ma200` | 200 日均线本身 |
| `MA30W` / `MA75W` → `ma30w/ma75w` | 周线均线 |
| `MA_Ratio_30W_75W` → `ma_ratio_30w_75w` | 30 周线 / 75 周线 |
| `MA_Ratio_5W_30W` → `ma_ratio_5w_30w` | 5 周线 / 30 周线 |

> 这张表也兼容了少量"周线均线"字段，未来如果周线类指标变多，可以单独
> 拆表，按 `(Symbol, Date)` 主键不变即可。

---

## 字段 ↔ 属性映射的真源

`database.stock_db_utils.StockDB._FACTOR_FIELD_MAP` 是上述「列名 → 属性名」
映射的**单一真源**：新增因子时只需要在它里面加一行 `("ColName", "attr_name")`，
配合：

1. 同一个文件里 `_<group>_columns` 加列声明；
2. `quantitative/factors/<group>.py` 的 mixin 加字段；
3. `quantitative/indicators/` 加纯函数算法；

下次启动 `_ensure_schema` 会自动 `ALTER TABLE ADD COLUMN` 补列。

## 常用 SQL 模板

```sql
-- 看某只股票 K 线最新日期
SELECT MAX(Date) FROM kline_daily WHERE Symbol = 'Tencent';

-- 看该股票各表行数（StockDB.get_stock_row_counts 的实现）
SELECT 'kline'      AS t, COUNT(*) FROM kline_daily      WHERE Symbol = 'Tencent'
UNION ALL SELECT 'indicator', COUNT(*) FROM factor_indicator WHERE Symbol = 'Tencent'
UNION ALL SELECT 'trend',     COUNT(*) FROM factor_trend     WHERE Symbol = 'Tencent'
UNION ALL SELECT 'momentum',  COUNT(*) FROM factor_momentum  WHERE Symbol = 'Tencent'
UNION ALL SELECT 'volume',    COUNT(*) FROM factor_volume    WHERE Symbol = 'Tencent'
UNION ALL SELECT 'risk',      COUNT(*) FROM factor_risk      WHERE Symbol = 'Tencent'
UNION ALL SELECT 'ma_ratio',  COUNT(*) FROM factor_ma_ratio  WHERE Symbol = 'Tencent';

-- 横截面：某天全市场按 RSI1 倒序前 50（StockDB.cross_section_rank 的能力）
SELECT Symbol, RSI1
FROM factor_indicator
WHERE Date = '2026-05-09' AND RSI1 IS NOT NULL
ORDER BY RSI1 DESC LIMIT 50;

-- 两只股票收盘比值（StockDB.get_stock_ratio_data 的实现）
SELECT a.Date, a.Close * 1.0 / b.Close
FROM kline_daily a
INNER JOIN kline_daily b ON a.Date = b.Date
WHERE a.Symbol = 'Tencent' AND b.Symbol = 'Alibaba' AND b.Close <> 0
ORDER BY a.Date ASC;
```

## 兼容旧 API

`StockDB` 保留了一组兼容方法，让历史调用不用改：

- `create_all_tables(name)` —— no-op（长表已在 `__init__` 建好）
- `get_raw_table_name(name)` / `get_indicator_table_name(name)` / ... ——
  统一返回对应的长表名常量

新代码请直接用 `StockDB.TABLE_KLINE` / `TABLE_INDICATOR` 等常量。
