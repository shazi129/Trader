# 行情缓存

`CachedQuoteAPI` 是线上行情源的缓存装饰器。缓存数据由行情域自己的
`MarketDataRepository` 管理。

```python
from quote_api import QuoteAPIFactory

api = QuoteAPIFactory.create_with_cache("futu")
quotes = api.get_klines("Tencent", limit=500)
```

流程：

1. 根据参数和 `stock_meta.listing_date` 确定目标区间；
2. 用 `MarketDataRepository.latest_date()` 判断尾部缺口；
3. 分批从上游 provider 拉取缺失区间；
4. `MarketDataRepository.save_many()` 写入 `kline_daily`；
5. 从仓储返回升序结果，最后应用 `limit`。

量化特征不是行情缓存的一部分。更新行情后，由调用方显式执行特征物化：

```powershell
python -m quantitative.cli features Tencent --api db
```

`tools/kline_fetcher` 已自动串联这两个步骤。
