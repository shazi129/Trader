# Trader

> 多数据源行情抽象 + SQLite 长表缓存 + 量化因子库 + PySide6 桌面端 + 一组命令行工具的个人交易研究项目。

## 目录

- [项目定位](#项目定位)
- [特性](#特性)
- [目录结构](#目录结构)
- [安装](#安装)
- [快速开始](#快速开始)
- [命令行入口总览](#命令行入口总览)
- [配置](#配置)
- [新增一只股票](#新增一只股票)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [更多文档](#更多文档)
- [免责声明](#免责声明)

---

## 项目定位

把"取数据 → 落库 → 算因子 → 出报告 / 看盘面"这条链路，做成**模块化、可
脚本化、可桌面化**的一套自用工具。

- **数据源解耦**：东方财富 / 腾讯财经 / 新浪财经 同一抽象接口，可随时切换。
- **本地优先**：所有 K 线和因子都落进单文件 SQLite，离线也能跑分析。
- **量化分层**：指标原语（pure function）→ 因子字段（dataclass）→ 信号编排
  （analyzer）→ 多周期回测（horizon backtester）四层解耦，不互相污染。
- **多入口**：GUI 看盘、CLI 拉数 / 跑分析、桌面浮窗看价，按需取用。

## 特性

- `QuoteAPI` 统一接口 + `QuoteAPIFactory` 进程级单例，三家数据源任意切换。
- `CachedQuoteAPI` 旁路缓存：先查 DB、缺什么拉什么，对调用方透明。
- `StockDB` 长表方案：1 张 K 线表 + 6 张因子长表（复合主键 `(Symbol, Date)`），
  天然支持横截面查询，迁移历史 DB 时自动 `ALTER TABLE` 补列。
- 60+ 个内建因子（趋势 / 动量 / 成交量 / 风险 / 均线比率），可一行命令批量入库。
- 「当前状态评分 + 历史相似态多周期回测」双视角分析报告（markdown 落盘）。
- PySide6 桌面端 + pyqtgraph 绘图；附带极简的浮窗实时报价小控件。

## 目录结构

```
Trader/
├── main.py                       # PySide6 GUI 启动入口
├── config.py                     # 全局配置：数据源、事件枚举
├── quote_api/                    # 行情数据源统一抽象层（三家实现 + 缓存包装）
│   ├── quote_base.py             # QuoteAPI 基类、DailyQuote/StockFundamental
│   ├── quote_factory.py          # QuoteAPIFactory（含进程级单例）
│   ├── cached_api.py             # CachedQuoteAPI 旁路缓存
│   ├── stock_meta.py             # STOCK_META 全项目股票清单
│   ├── eastmoney/ tencent/ sina/ # 三家具体实现 + 各自 config.json
├── quantitative/                 # 量化分析三层
│   ├── indicators/               # 纯函数指标原语（SMA/EMA/RSI/KDJ/ADX/...）
│   ├── factors/                  # KlineIndicator 字段 dataclass（6 mixin）
│   ├── analyzer/                 # 单点信号编排 + 文本报告
│   ├── factor_batch.py           # 批量计算因子并写库（CLI）
│   ├── quant_analyzer.py         # 单股快速分析（CLI）
├── database/
│   ├── stock_db_utils.py         # StockDB（长表方案）
│   └── stock_data.db             # 默认数据库文件
├── tools/                        # 各自独立的命令行小工具
│   ├── kline_fetcher/            # 定时 / 守护拉 K 线（写库后自动算因子）
│   ├── stock_advisor/            # 多因子 + 相似态回测，落盘 markdown 报告
│   ├── stock_widget/             # PySide6 浮窗实时报价
│   └── fund_holdings/            # SEC 13F 持仓抓取与可视化
├── ui/                           # 主窗口、子 widget、Qt Designer 生成
├── utils/                        # logger、event_system、ratio、stock_updater
├── test/                         # pytest（database/）+ 一些手工脚本
├── docs/                         # 工程文档（见底部"更多文档"）
└── requirements.txt              # 依赖清单
```

## 安装

需要 **Python ≥ 3.10**（项目用到 `match/case`、`str | None` union 语法）。

```bash
git clone https://github.com/<your-name>/Trader.git
cd Trader
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

> Windows 上 `PySide6` 的 `pip` 安装通常不需要额外编译，直接装即可。

## 快速开始

### 1. 拉一份初始 K 线数据并自动算因子

```bash
python tools/kline_fetcher/kline_fetcher.py run
```

执行后：`STOCK_META` 中的全部股票 → 增量拉 K 线 → 写入 `database/stock_data.db`
→ 自动调 `compute_and_save_factors` 同步刷新 6 张因子表。

### 2. 出一份分析报告

```bash
python -m tools.stock_advisor.stock_advisor Tencent
```

报告落盘到 `tools/stock_advisor/reports/Tencent_<时间戳>.md`，包含：

1. 当前状态评分（多因子加权快照）
2. 多周期涨跌预测（短 / 中 / 长 三档历史相似态频率）
3. 因子明细
4. 风险提示

### 3. 启动桌面 GUI

```bash
python main.py
```

### 4. 启动浮窗报价

```bash
python tools/stock_widget/stock_widget.py
```

## 命令行入口总览

| 入口 | 命令 | 作用 |
|---|---|---|
| GUI 主程序 | `python main.py` | PySide6 主窗口，支持比值图等 |
| 单股快速分析 | `python -m quantitative.quant_analyzer <name> [--api ...] [--days 500] [--no-cache]` | 控制台文本报告 |
| 批量因子入库 | `python -m quantitative.factor_batch [--stock X] [--api ...] [--limit 5000] [--db PATH] [--force-refresh]` | 给 `STOCK_META` 全部或指定股票算因子并 UPSERT 入库 |
| K 线增量抓取 | `python tools/kline_fetcher/kline_fetcher.py {run\|daemon} [--config PATH] [--run-on-start]` | 写库后**自动**同步刷新因子表 |
| 股票顾问 | `python -m tools.stock_advisor.stock_advisor <name> [--api ...] [--top-k 80] [--no-write] [--force-refresh]` | 因子 + 相似态回测，markdown 报告 |
| 浮窗报价 | `python tools/stock_widget/stock_widget.py` | 极简浮空小控件 |
| 全市场更新 | `python utils/stock_updater.py` | 从 DB 最新日期增量补 K 线 |

各子工具内还有自己的 README（[`kline_fetcher`](tools/kline_fetcher/README.md) /
[`stock_advisor`](tools/stock_advisor/README.md) /
[`stock_widget`](tools/stock_widget/readme.md) /
[`fund_holdings`](tools/fund_holdings/README.md)）讲细节。

## 配置

| 位置 | 字段 | 说明 |
|---|---|---|
| `config.py` | `QUOTE_SOURCE` | 默认行情源：`"eastmoney"` / `"tencent"` / `"sina"` |
| `quote_api/stock_meta.py` | `STOCK_META` | 全项目股票清单（`name_key → StockInfo`） |
| `quote_api/<src>/config.json` | `stocks` 映射 | 该数据源支持的 `name_key → 真实代码` |
| `tools/kline_fetcher/config.json` | `api / db_path / earliest_date / schedule_time / stocks` | 抓取行为 |
| `tools/stock_widget/config.json` | `api / stocks / refresh_interval / opacity / font_size / position` | 浮窗显示 |

数据库默认路径是 `database/stock_data.db`，由 `StockDB(db_path=None)` 内部解析；
所有工具都接受 `--db` 或在配置里覆盖。

## 新增一只股票

按这四步走，全项目就都认了：

1. **`quote_api/stock_meta.py`** 的 `STOCK_META` 里加一条 `StockInfo`，`name_key`
   就是项目内部的逻辑标识。
2. **`quote_api/<source>/config.json`** 的 `stocks` 里加 `name_key → 真实代码`
   映射（每个想用的源都要加）。
3. 跑 `python tools/kline_fetcher/kline_fetcher.py run` 拉历史 K 线，
   写库后会自动计算因子。
4. 跑 `python -m tools.stock_advisor.stock_advisor <name_key>` 验证。

## 开发指南

- **日志**：所有模块统一用 `from utils.logger import get_logger; _log = get_logger(__name__)`，
  不要直接 `print`。
- **测试**：
  ```bash
  pytest test/database          # 数据库层单测
  ```
  `test/` 下另外散落一些手工探活脚本（带 `test_` / `check_` 前缀），按需直接 `python` 跑。
- **新增因子的最短路径**：
  1. 在 `quantitative/indicators/` 加一个纯函数算法；
  2. 在 `quantitative/factors/<group>.py` 的对应 mixin 上加字段；
  3. 在 `database/stock_db_utils.py` 的 `_*_columns` 里加列、`_FACTOR_FIELD_MAP`
     里加 `(列名, 属性名)` 映射 —— 下次启动会自动 `ALTER TABLE`；
  4. 如果要让该因子参与打分，在 `quantitative/analyzer/` 里挂上信号规则。
- **新增数据源的最短路径**：
  1. 写一个继承 `QuoteAPI` 的实现类，至少 override `get_klines`；
  2. 在 `QuoteAPIFactory._REGISTRY` 注册 或 运行时 `QuoteAPIFactory.register(...)`；
  3. 加一份 `quote_api/<src>/config.json`。
- 工程结构和数据流的全景图见 [docs/architecture.md](docs/architecture.md)。

## 常见问题

**Q：`ModuleNotFoundError: No module named 'tools'`**
A：你在 `tools/xxx` 子目录里跑了 `python -m tools.xxx.yyy`。`-m` 必须从项目根
跑（或者直接 `python yyy.py` 文件式运行，子工具脚本头部都做了 `sys.path` 兜底）。

**Q：`attempted relative import with no known parent package`**
A：在子目录里跑了 `python -m yyy`（无父包）。回项目根用 `-m` 或者直接 `python yyy.py`。
详见 [tools/stock_advisor/README.md](tools/stock_advisor/README.md#常见错误)。

**Q：东方财富 / 腾讯接口抽风、超时？**
A：临时切到另一个数据源即可，`config.QUOTE_SOURCE` 改一下，或者命令行加
`--api tencent`。三家实现都已经做了基本的 UA / 错误兜底。

**Q：因子表跟 K 线表日期对不上？**
A：`kline_fetcher` 写库成功后会自动调 `compute_and_save_factors` 把因子刷到
同一日；如果跳过了这一步（比如直接用 `CachedQuoteAPI` 拉数），下次跑
`stock_advisor` 时 `_load_or_build` 也会兜底重算。

**Q：能不能多进程同时写 DB？**
A：`StockDB` 用的是默认 `journal_mode=DELETE` + 单连接，不是为并发写设计的。
日常一个 `kline_fetcher` 进程 + 一个分析进程读取没问题；想并行写，请自己上锁
或改 WAL。

## 更多文档

- [docs/architecture.md](docs/architecture.md) — 模块分层、依赖关系、关键设计决策
- [docs/data_schema.md](docs/data_schema.md) — 7 张长表 schema、字段-因子对照
- [docs/cached_api_usage.md](docs/cached_api_usage.md) — `CachedQuoteAPI` 用法
- [tools/kline_fetcher/README.md](tools/kline_fetcher/README.md)
- [tools/stock_advisor/README.md](tools/stock_advisor/README.md)
- [tools/stock_widget/readme.md](tools/stock_widget/readme.md)
- [tools/fund_holdings/README.md](tools/fund_holdings/README.md)

## 免责声明

本仓库为个人研究/学习用途，不构成任何投资建议。任何基于本项目输出做出的
交易决策风险自负。
