# kline_fetcher

增量拉取日 K 线，并在行情写入完成后物化量化特征。

## 数据流

```text
QuoteAPI provider
  → CachedQuoteAPI
  → MarketDataRepository / kline_daily
  → FeatureCalculator
  → FeatureRepository / quant_feature_daily
```

工具只负责编排。K 线表属于行情域，特征表属于量化域，SQLite 通用设施不会感知
两者的业务字段。

## 配置

`config.json` 示例：

```json
{
  "api": "futu",
  "schedule_time": "17:30",
  "exclude": ["DisabledSymbol"]
}
```

- `api` 必须是 `QuoteAPIFactory.available_sources()` 返回的数据源；
- `schedule_time` 是守护模式的本机时间；
- `exclude` 可选，用于排除 `STOCK_META` 中的部分标的。

拉取起点优先使用数据库中该标的的最新日期加一天；没有历史记录时使用
`StockInfo.listing_date`。工具会按市场收盘时间决定当天日 K 是否已经定型。

## 命令

```powershell
# 全股票池增量更新
python tools/kline_fetcher/kline_fetcher.py run

# 每日定时运行
python tools/kline_fetcher/kline_fetcher.py daemon
python tools/kline_fetcher/kline_fetcher.py daemon --run-on-start

# 单标的操作
python tools/kline_fetcher/kline_fetcher.py fill Tencent
python tools/kline_fetcher/kline_fetcher.py recent Tencent --days 60
python tools/kline_fetcher/kline_fetcher.py delete Tencent

# 指定配置
python tools/kline_fetcher/kline_fetcher.py run --config path/to/config.json
```

`delete` 会同时删除该标的的 K 线和物化特征。重复拉取使用 UPSERT，不会产生
重复记录。

生产环境更适合用 Windows 任务计划程序或 cron 周期执行 `run`；`daemon` 适合
简单的常驻场景。
