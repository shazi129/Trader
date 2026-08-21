# quote_api 使用说明

`quote_api` 是行情领域。它负责把不同线上数据源标准化为 `DailyQuote`，管理标的
元信息，并拥有日 K 线表 `kline_daily`。它不计算技术特征，也不判断交易形态。

## 模块结构

| 文件 | 职责 |
|---|---|
| `quote_base.py` | `QuoteAPI`、`DailyQuote`、复权方式等公共契约 |
| `quote_factory.py` | provider 注册、创建与实例生命周期 |
| `cached_api.py` | “本地优先、缺失回源”的行情装饰器 |
| `db_api.py` | 只读本地 SQLite 的行情源 |
| `repository.py` | `kline_daily` 的领域仓储 |
| `stock_meta.py` | 项目内统一标的池与市场元信息 |
| `futu/`、`sina/`、`tencent/` | 具体线上 provider |

## 核心模型

`DailyQuote` 是所有 provider 的统一输出，主要字段如下：

```text
date, open, close, high, low
volume, turnover, turnover_rate
name, code, source, currency
```

日期统一为 `YYYY-MM-DD`，`get_klines()` 必须返回日期升序序列。业务代码只应依赖
`DailyQuote`，不要读取 provider 的原始 JSON。

历史 K 线复权方式由 `KlineAdjustment` 表示：

```text
none    不复权
qfq     前复权
hfq     后复权
```

默认值来自项目根目录 `config.KLINE_ADJUSTMENT`。

## 获取行情

### 原始线上接口

```python
from quote_api import QuoteAPIFactory

api = QuoteAPIFactory.create("futu")
quotes = api.get_klines(
    "Tencent",
    start_date="2025-01-01",
    end_date="2025-12-31",
)
latest = api.get_daily_quote("Tencent")

QuoteAPIFactory.clear_cache()
```

`start_date` 和 `end_date` 均包含边界；`limit` 表示最终最多返回最近 N 条。

### 带本地行情缓存

```python
from quote_api import QuoteAPIFactory

api = QuoteAPIFactory.create_with_cache("futu")
quotes = api.get_klines("Tencent", limit=500)

QuoteAPIFactory.clear_cache()
```

缓存流程：

1. 根据显式日期或 `StockInfo.listing_date` 确定目标区间；
2. 查询 `MarketDataRepository.latest_date()`；
3. 将尾部缺口分批交给线上 provider；
4. UPSERT 到 `kline_daily`；
5. 从本地仓储返回升序结果，再应用 `limit`。

注意：`QuoteAPIFactory.create(cached=True)` 中的 `cached` 表示“复用 Python API
实例”，并不表示 SQLite 行情缓存。只有 `create_with_cache()` 才会读写
`kline_daily`。

当前缓存策略根据数据库最大日期补齐尾部，不能自动发现中间交易日缺口。需要修复
历史缺口时，应显式拉取区间并写入 `MarketDataRepository`。

### 仅使用本地数据库

```python
from quote_api.db_api import DbQuoteAPI

with DbQuoteAPI(db_path="database/stock_data.db") as api:
    quotes = api.get_klines("Tencent", limit=500)
```

`DbQuoteAPI` 不访问网络。数据库没有对应数据时返回空列表。

## 行情仓储

```python
from quote_api.repository import MarketDataRepository

with MarketDataRepository() as repository:
    repository.save_many("Tencent", quotes)
    latest_date = repository.latest_date("Tencent")
    history = repository.get_range(
        "Tencent", start_date="2025-01-01", end_date="2025-12-31"
    )
```

公开查询接口：

| 方法 | 返回值 |
|---|---|
| `save(symbol, quote)` | 保存单条日 K |
| `save_many(symbol, quotes)` | 批量 UPSERT |
| `latest_date(symbol)` | 最新交易日或 `None` |
| `count(symbol)` | 记录数 |
| `list_symbols()` | 数据库内全部标的 |
| `latest(symbol, size)` | 按日期倒序的最近 N 条 |
| `get_range(symbol, start, end)` | 日期升序区间 |
| `get_by_date(symbol, date)` | 单日记录或 `None` |
| `delete_symbol(symbol)` | 删除该标的全部 K 线 |
| `ratio_series(a, b)` | 两标的同日收盘价比值序列 |

`delete_symbol()` 是破坏性操作。工具层的 `kline_fetcher delete` 还会同时删除该
标的的物化量化特征。

## 标的池

`quote_api.stock_meta.STOCK_META` 是项目统一股票池，key 是内部稳定标识：

```python
from quote_api.stock_meta import all_keys, get_meta

symbols = all_keys()
tencent = get_meta("Tencent")
print(tencent.code, tencent.market, tencent.listing_date)
```

新增标的时，在 `STOCK_META` 添加 `StockInfo`。某 provider 不支持该标的时，在
自身 `config.json` 中将对应值设为空字符串；代码不一致时填写覆盖代码。

## 新增 provider

```python
from quote_api import DailyQuote, QuoteAPI, QuoteAPIFactory


class ExampleQuoteAPI(QuoteAPI):
    SOURCE = "example"

    def get_klines(self, name, start_date=None, end_date=None, limit=None):
        rows = []  # 调用外部服务并转换成 DailyQuote
        return self.sort_and_trim(
            rows,
            self.normalize_date(start_date),
            self.normalize_date(end_date),
            limit,
        )


QuoteAPIFactory.register("example", ExampleQuoteAPI)
```

provider 必须处理资源释放、超时、日期标准化和结果排序，但不能写量化表或计算
技术指标。

## 生命周期与常见问题

- 工厂默认复用同一 `source + adjustment` 的实例；进程结束前调用
  `QuoteAPIFactory.clear_cache()` 释放网络和数据库连接。
- 向 `CachedQuoteAPI` 或 `DbQuoteAPI` 注入 Repository 时，Repository 生命周期
  归调用方；API 不会关闭外部 Repository。
- `kline_daily` 当前不区分复权版本。同一数据库不要混写不同复权口径；修改
  `KLINE_ADJUSTMENT` 后应重新构建该标的行情和特征。
- 线上 provider 失败不等于本地数据不存在。回测建议显式使用本地仓储，保证输入
  数据集稳定。

相关文档：[行情缓存](../cached_api_usage.md)、[数据表](../data_schema.md)。
