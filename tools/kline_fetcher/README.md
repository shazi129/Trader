# kline_fetcher

定时增量拉取日 K 线数据入库的小工具。

## 工作流程

1. 读 `config.json` 拿到拉取列表与全局参数
2. 对每只股票去 `kline_daily` 表查最新一条记录的日期
3. 有就从 **最新日期 + 1 天** 起增量拉，没有就从配置的 `earliest_date` 起拉
4. 按个股所在市场判断"今天是否已收盘"，决定 `end_date`：
   - A 股（SH/SZ）：本地时间 ≥ 15:00 才认为今天定型
   - 港股（HK）：本地时间 ≥ 16:00
   - 美股（NASDAQ/NYSE/US/COMEX）：美东时间 ≥ 16:00（自动处理夏/冬令时）
   - 周末以及未收盘的工作日 → `end_date` 回退到最近的工作日，避免把盘中实时价当成"日 K"写库
5. 调用所选数据源的 API 抓取 `[start, end_date]` 区间，批量 UPSERT 入库
6. 单只失败不会中断其它股票

## 配置文件 `config.json`

```json
{
    "api": "<source>",             // 有效值见 QuoteAPIFactory.available_sources()
    "db_path": null,               // null = 用 database/stock_data.db 默认路径
    "earliest_date": "2010-01-01", // 全局兜底：DB 无记录、个股也没单独配 earliest_date 时使用
    "schedule_time": "17:30",      // 守护模式每日触发时间（本机时区，HH:MM）
    "stocks": [
        { "name_key": "Tencent",  "earliest_date": null, "enabled": true },
        { "name_key": "Alibaba",  "earliest_date": "2019-11-26", "enabled": false }
    ]
}
```

`stocks` 也可以简写为字符串列表：`["Tencent", "Alibaba"]`，等价于 enabled=true、earliest_date=null。

`name_key` 必须是 `quote_api/stock_meta.py` 中 `STOCK_META` 已注册的键。

省略 `api` 时使用 `QuoteAPIFactory.current_source()`；provider 如有额外运行环境
要求，以其自身目录中的说明为准。

### 起始日期优先级

DB 最新日期 +1 天 > 该股票自己的 `earliest_date` > `StockInfo.listing_date`（不早于全局兜底）> 全局 `earliest_date`

## 用法

```bash
# 单次执行（适合做 cron / 任务计划程序的一次性命令）
python tools/kline_fetcher/kline_fetcher.py run

# 守护模式：每天定时执行一次
python tools/kline_fetcher/kline_fetcher.py daemon

# 守护模式 + 启动时先立刻跑一次（首次部署很有用）
python tools/kline_fetcher/kline_fetcher.py daemon --run-on-start

# 自定义配置文件
python tools/kline_fetcher/kline_fetcher.py run --config path/to/my_config.json
```

## 接 Windows 任务计划程序（推荐做法）

守护模式跑在前台 / 终端窗口里，机器重启后不会自动恢复；如果要"开机自启 + 每日执行"，更推荐：

1. 创建一次性任务，触发器选 **每日 17:30**
2. 操作填 `python.exe`，参数 `D:\GitHub\Trader\tools\kline_fetcher\kline_fetcher.py run`
3. 起始位置填 `D:\GitHub\Trader`

这样不需要常驻进程，系统会替你管理调度。

## 设计说明

- 不引入 `schedule` / `APScheduler` / `cron` 等三方依赖；守护模式用最朴素的"算下一次时间 → sleep → 跑"循环实现，跨平台
- DB / API 都直接复用项目内的 `StockDB` 与 `QuoteAPIFactory`，不重复造轮子
- 入库走 UPSERT，重复跑安全（不会产生重复行）
