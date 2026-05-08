# 缓存API使用说明

## 概述

缓存API (`CachedQuoteAPI`) 实现了"先读DB，缺失再拉取"的逻辑。对调用者透明：使用方式与普通 `QuoteAPI` 完全一致。

## 工作原理

1. **首次调用**：查询数据库 → 无数据 → 调用真实API拉取 → 存入数据库 → 返回数据
2. **后续调用**：查询数据库 → 有数据 → 直接从DB返回（不再调用API）

## 使用方法

### 方式1：直接使用 CachedQuoteAPI

```python
from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI

# 创建原始API
raw_api = QuoteAPIFactory.create("eastmoney")

# 包装为带缓存的API
api = CachedQuoteAPI(raw_api)

# 使用方式与普通API完全一致
klines = api.get_klines("Tencent", limit=500)  # 自动缓存
```

### 方式2：使用工厂方法（推荐）

```python
from quote_api import QuoteAPIFactory

# 一行代码创建带缓存的API
api = QuoteAPIFactory.create_with_cache("eastmoney")

# 使用方式与普通API完全一致
klines = api.get_klines("Tencent", limit=500)  # 自动缓存
```

### 方式3：在 QuantAnalyzer 中使用

```bash
# 默认使用缓存（推荐）
python -m quantitative.quant_analyzer Tencent

# 不使用缓存
python -m quantitative.quant_analyzer Tencent --no-cache
```

或者在代码中使用：

```python
from quantitative.quant_analyzer import QuantAnalyzer

# 使用缓存（默认）
analyzer = QuantAnalyzer(api="tencent", use_cache=True)
report = analyzer.analyze("Tencent", days=500)

# 不使用缓存
analyzer = QuantAnalyzer(api="tencent", use_cache=False)
report = analyzer.analyze("Tencent", days=500)
```

## 测试

运行测试脚本验证功能：

```bash
python test/test_cached_api.py
```

测试脚本会验证：
1. 首次调用是否从API拉取数据
2. 再次调用是否从数据库读取
3. 数据一致性是否正确

## 数据库表结构

缓存API使用 `StockDB` 管理数据库，会自动为每只股票创建以下表：

- **原始数据表** (表名：股票名，如 `Tencent`)
  - Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate, PE

- **基础指标表** (表名：股票名+`_Ind`)
  - Date, MA5, MA10, MA20, MA30, MA60, MA120, MA250, BollUp, BollLow, K, D, J, Dif, Dea, MACD, RSI1, RSI2, RSI3, ADOSC

- **趋势因子表** (表名：股票名+`_Trend`)
  - Date, EMA12, EMA26, EMA50, MACD_HIST, ADX, Plus_DI, Minus_DI, TR, ATR, ATR_PCT

- **动量因子表** (表名：股票名+`_Momentum`)
  - Date, MOM1W, MOM2W, MOM1M, MOM3M, MOM6M, MOM9M, MOM12M, ROC1W, ROC2W, ROC1M, ROC3M, ROC6M, ROC9M, ROC12M, CCI, WilliamsR

- **成交量因子表** (表名：股票名+`_Volume`)
  - Date, OBV, VPT, ADL, MFI, ForceIndex1, ForceIndex13, ForceIndex21

- **风险指标表** (表名：股票名+`_Risk`)
  - Date, HV20, HV60, MaxDrawdown, Volatility, Sharpe, Sortino, Calmar, Skewness, Kurtosis

- **均线比率表** (表名：股票名+`_MA_Ratio`)
  - Date, MA_Ratio_5, MA_Ratio_10, MA_Ratio_20, MA_Ratio_60, MA_Ratio_200, MA200, MA30W, MA75W, MA_Ratio_30W_75W, MA_Ratio_5W_30W

## 注意事项

1. **数据库路径**：默认使用 `database/stock_data.db`，可在 `StockDB` 初始化时指定
2. **数据更新**：缓存API不会自动更新数据，需要手动删除数据库或实现更新逻辑
3. **日期范围**：当前实现会读取 `limit or 1000` 条数据，然后按日期范围过滤
4. **基本面数据**：暂不缓存，直接透传到真实API

## 扩展建议

1. **自动更新**：添加逻辑，检查数据库数据是否最新，如果不是则自动更新
2. **批量预取**：支持一次性拉取多只股票的并缓存
3. **缓存过期**：添加缓存过期时间，自动刷新过期数据
4. **错误处理**：增强错误处理，API失败时有降级方案
