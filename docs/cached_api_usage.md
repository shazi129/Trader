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

# 创建当前默认的原始 API
raw_api = QuoteAPIFactory.create()

# 包装为带缓存的API
api = CachedQuoteAPI(raw_api)

# 使用方式与普通API完全一致
klines = api.get_klines("Tencent", limit=500)  # 自动缓存
```

### 方式2：使用工厂方法（推荐）

```python
from quote_api import QuoteAPIFactory

# 一行代码创建当前默认的带缓存 API
api = QuoteAPIFactory.create_with_cache()

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

# 使用缓存（默认数据源由 Factory 解析）
analyzer = QuantAnalyzer(use_cache=True)
report = analyzer.analyze("Tencent", days=500)

# 不使用缓存
analyzer = QuantAnalyzer(use_cache=False)
report = analyzer.analyze("Tencent", days=500)
```

## 测试

运行测试脚本验证功能：

```bash
python -m pytest -m integration tests/integration/test_cached_api.py
```

集成测试使用临时数据库，不会修改默认行情数据库。测试会验证：
1. 首次调用是否从API拉取数据
2. 再次调用是否从数据库读取
3. 数据一致性是否正确

## 数据库表结构

`CachedQuoteAPI` 写入的表与 `quantitative.factor_batch` / `kline_fetcher` 共用同一份
schema —— **当前已经是「长表方案」**：1 张 K 线表 + 6 张因子表，复合主键
`(Symbol, Date)`，不再为每只股票单独建表。

完整 schema、字段-属性对照、常用 SQL 模板请看 [data_schema.md](data_schema.md)。

## 注意事项

1. **数据库路径**：默认 `database/stock_data.db`，可在 `StockDB(db_path=...)` 指定。
2. **数据更新**：`CachedQuoteAPI` 自身不做"过期判断"，日常增量请走
   [`tools/kline_fetcher`](../tools/kline_fetcher/README.md) ——
   它写库后会**自动调** `compute_and_save_factors` 同步刷新因子表。
3. **基本面数据**：暂不缓存，直接透传到真实 API。
4. **多进程并发写**：`StockDB` 默认 `journal_mode=DELETE` 单连接，不为并发写设计；
   读并发安全。

## 扩展方向

- **缓存过期**：在 `CachedQuoteAPI.get_klines` 里加最新日期与今天的差值判断。
- **批量预取**：循环调 `compute_and_save_factors` 已经够用，必要时可改成异步。
- **错误降级**：在 `QuoteAPIFactory` 注册多源，捕获异常后切换。
