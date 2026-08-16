# 工程架构

> 一句话：**数据源 → 缓存 → 存储 → 因子 → 信号/回测 → CLI 报告 / 独立报价浮窗**。
> 每一层只依赖下一层，且替换上层不需要改下层。

## 总览

```
        +---------------------------------------------------------+
        |                           入口                             |
        |  tools/stock_advisor       tools/kline_fetcher             |
        |  quantitative.* (CLI)      tools/stock_widget (独立浮窗)   |
        +-----------------------+---------------------------------+
                                |
                                v
        +---------------------------------------------------------+
        |                 信号 / 报告 / 回测                        |
        |  quantitative/analyzer/    (单点多因子打分 → 文本报告)     |
        |  tools/stock_advisor/backtester.py  (历史相似态多周期回测) |
        +-----------------------+---------------------------------+
                                |
                                v
        +---------------------------------------------------------+
        |                       因子层                             |
        |  quantitative/indicators/  纯函数指标原语                 |
        |  quantitative/factors/     KlineIndicator dataclass(6mixin)|
        |  quantitative/factor_batch.py  批量计算 → DB              |
        +-----------------------+---------------------------------+
                                |
                                v
        +---------------------------------------------------------+
        |                  存储 / 缓存                             |
        |  database/StockDB     SQLite 长表（K线 + 6 张因子表）      |
        |  quote_api/CachedQuoteAPI    旁路缓存包装                 |
        +-----------------------+---------------------------------+
                                |
                                v
        +---------------------------------------------------------+
        |                      数据源                              |
        |  quote_api/<provider>（由 Factory 注册表动态发现）       |
        |  统一基类: QuoteAPI / DailyQuote / StockFundamental       |
        +---------------------------------------------------------+
```

依赖方向严格自上而下，**不允许下层回调上层**（`config.py` 里只保留默认
数据源和兼容导出，股票清单下沉到了 `quote_api/stock_meta.py`）。

## 各层职责详解

### 1. 数据源层 `quote_api/`

- **`QuoteAPI`**（`quote_base.py`）：抽象基类，定义 `get_klines / get_daily_quote /
  get_fundamentals` 三个接口，并用 `KlineAdjustment` 统一不复权、
  前复权和后复权的参数语义。
- **多源实现**：每个 `quote_api/<provider>/` 自带 `config.json`；具体名单调用
  `QuoteAPIFactory.available_sources()` 获取
  保存 `name_key → 真实代码` 映射，作为「这个数据源支持哪些股票」的权威清单。
- **`QuoteAPIFactory`**（`quote_factory.py`）：
  - 按 source 字符串/枚举创建实现实例；
  - **进程级单例**（`_RAW_INSTANCES` / `_CACHED_INSTANCES`）：同一 source
    在一个进程里只活一份，避免重复构造、避免多份 DB 连接；
  - `clear_cache()` 给测试和长时进程显式释放。
- **`CachedQuoteAPI`**（`cached_api.py`）：包装一个 `QuoteAPI` 实例，
  `get_klines` 路径改成「先查 DB 缺什么 → 再去拉 → 写回 DB → 返回」。
  对调用方透明，签名完全一致。
- **`stock_meta.py`**：唯一的 `STOCK_META: dict[name_key, StockInfo]`，
  `config.global_stock_list` 仅为兼容旧代码 re-export。

### 2. 存储层 `database/`

只有一个类 `StockDB`，对应一个 SQLite 文件（默认 `database/stock_data.db`）。

- 表结构、字段、索引细节见 [docs/data_schema.md](data_schema.md)。
- 关键设计：
  - **长表方案**（`(Symbol, Date)` 复合主键）替代旧的「每只股票 7 张表」，
    天然支持横截面查询（`cross_section_rank`）。
  - **schema 自动迁移**：`_ensure_schema` 启动时跑 `ALTER TABLE ADD COLUMN`
    补齐缺失列，新增因子不需要手动迁移历史 DB。
  - **精度统一**：价格 4 位、因子 6 位（`_round_kline` / `_round_factor`）。
  - **UPSERT**（`INSERT OR REPLACE`）：所有写接口幂等，重复跑不会出错。

### 3. 因子层 `quantitative/`

**三层解耦**，避免「指标计算 + 字段定义 + 信号判断」混在一起。

| 子目录 | 角色 | 形态 |
|---|---|---|
| `indicators/` | 指标原语 | 纯函数：`(prices, window) → values` |
| `factors/` | 字段载体 | `KlineIndicator` dataclass，6 个 mixin（basic / trend / momentum / volume / risk / ma_ratio）|
| `analyzer/` | 信号编排 | 把指标读数 → 多空信号 → 加权概率 → 文字结论 |

入口：

- `quantitative.factor_batch.compute_and_save_factors(name_key, ...)`：
  给一只股票算完整时间序列的所有因子，**一张表一次 `executemany`** 写入。
  `kline_fetcher` 在写完 K 线后会自动调它。
- `quantitative.quant_analyzer.QuantAnalyzer.analyze(name, days=500)`：
  快速 CLI 入口，输出文本报告。

### 4. 报告 / 回测层 `tools/stock_advisor/`

不是 `quantitative` 的一部分（它有自己的产品形态：markdown 报告 + 历史相似态
回测），通过组合 `analyzer` + `HorizonBacktester` 实现：

- **第 1 节「当前状态评分」**：调 `QuantAnalyzer`，单点多因子加权 → 当前
  多空力量快照（注意：**不是预测**）。
- **第 2 节「多周期涨跌预测」**：`HorizonBacktester` 在历史里找跟当前因子组合
  最相似的 top-K 天，统计这些天 N 天后的真实涨跌频率（短 5 / 中 20 / 长 60）。

两节方向相反是正常的——比如当前超卖（第 1 节偏空），但历史上每次跌到此位
后多数反弹（第 2 节偏多），这是均值回归。

### 5. 入口

- **CLI**：`quantitative.quant_analyzer` / `quantitative.factor_batch` /
  `tools.stock_advisor.stock_advisor` / `tools/kline_fetcher/kline_fetcher.py`。
- **独立报价浮窗**：`tools/stock_widget/`，只依赖行情抽象层，不依赖已移除的
  `main.py` 和 `ui/` 主窗口。

## 关键数据流

### A. 日常增量更新（`kline_fetcher`）

```
配置文件 stocks 列表
   ↓
QuoteAPIFactory.create(api)  ← 单例
   ↓
api.get_klines(name_key, start=DB最新日期+1, end=today)
   ↓
StockDB.write_kline_data_many   ← UPSERT
   ↓
compute_and_save_factors(name_key)   ← 写库后自动触发
   ↓
StockDB.write_all_indicators_many    ← 6 张因子表一并刷新
```

### B. 出一份分析报告（`stock_advisor`）

```
stock_advisor <name>
   ↓
_load_or_build(name)     ← 比较 kline_daily 与 factor_indicator 的 MAX(Date)
   ├─ 一致 → 直接读 DB 拼出 KlineIndicator 序列
   └─ 不一致 → 调 compute_and_save_factors 重算并写回
   ↓
QuantAnalyzer  → 第 1 节「当前状态评分」
HorizonBacktester(top_k) → 第 2 节「多周期涨跌预测」
   ↓
_build_markdown(...) → reports/<name>_<时间戳>.md
```

### C. 缓存读路径（`CachedQuoteAPI`）

```
api.get_klines(name, limit=N)
   ↓
StockDB.get_latest_klines(name, N)   ← 优先 DB
   ├─ 数据足够 → 直接返回
   └─ 不足 → fallback 调原始 API → 写回 → 返回
```

详见 [cached_api_usage.md](cached_api_usage.md)。

## 关键设计决策记录

1. **股票元信息下沉到 `quote_api/stock_meta.py`**
   原本写在 `config.py`，但 `quote_api` 反而要从业务层读，方向不对。
   现在 `config.py` 只 re-export 一个 `global_stock_list` 为旧代码兜底。

2. **「每股 7 张表」→「7 张长表」**
   旧方案 N 只股票要建 7N 张表，DDL 维护噩梦、横截面查询要 `UNION` 一堆
   动态表名。新方案 7 张固定表 + `(Symbol, Date)` 复合主键，加索引 `idx_*_date`
   后横截面查询 1 句 SQL 就能搞定。

3. **`KlineIndicator` 拆 6 mixin**
   原来是个上帝对象（一个类承担基础指标 / 趋势 / 动量 / 成交量 / 风险 / MA 比率
   全部字段）。按因子组拆成 mixin 后，新增字段、单元测试、阅读都更清晰；
   `_FACTOR_FIELD_MAP` 用元数据驱动，新增字段只需改一处。

4. **`QuoteAPIFactory` 单例 + `CachedQuoteAPI` 旁路**
   解决两件事：① 同进程多次创建带来的连接泄漏；② 让"加缓存"完全不污染
   业务调用代码（包装一层即可）。

5. **`kline_fetcher` 写库成功后自动算因子**
   保证 `kline_daily` 与 `factor_indicator` 的最新日期始终一致；失败也只打
   日志、不影响 K 线入库主流程，下次分析时 `_load_or_build` 兜底。

6. **`stock_advisor` 报告刻意拆「快照」与「预测」两节**
   第 1 节是"此刻多空力量快照"，第 2 节是"历史相似态的未来 N 天频率"，
   两者维度不同，方向相反是正常的，文档里也反复强调这一点防误读。
