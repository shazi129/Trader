# Trader 目标架构与重构准备方案

> 状态：设计已成形，尚未开始目录迁移  
> 用途：作为后续重构的目标结构、依赖规则、迁移顺序和验收依据  
> 原则：先建立基线和兼容层，再分阶段迁移；Go/No-Go 清单满足前不执行重构

## 1. 背景与目标

Trader 已具备行情获取与缓存、技术指标、特征物化、信号判断、回测、机器学习、
时点分析和财报分析等能力。当前代码基本按业务域组织，但还存在以下结构问题：

- `quote_api` 同时承担模型、数据源接口、Provider、缓存、仓储和工厂职责；
- `utils` 中混入行情同步和股票比值等业务代码；
- `tools/stock_advisor` 直接组合多个领域的内部组件；
- 特征物化代码同时访问 Provider、行情仓储和特征仓储；
- 数据库、模型、回测统计、财报原件和源码混放；
- 多个顶层 Python 包不利于打包和约束依赖。

重构目标：

1. 使用单一 `trader` Python 命名空间；
2. 按行情、量化、财报三个业务域组织核心代码；
3. 将跨领域流程集中到 `application`，让 CLI、Web、桌面工具只负责输入输出；
4. 分离源码、配置、测试夹具、原始数据、运行数据和模型产物；
5. 保留现有数据库和命令的兼容迁移路径；
6. 用自动化测试保护业务行为和模块边界；
7. 动态维护沪深 300、恒生指数、标普 500 成分股及指定白银标的，并增量维护
   最近十年的日 K 线。

本轮重构不重写算法、不更换 SQLite、不引入微服务或大型框架，也不同时开发舆情、
实盘交易等新功能。

UI 与 OpenWorkspace 接入采用第 17 节的演进方案。本轮先统一现有入口的应用服务与
数据契约；Vue 工作台和常驻 FastAPI 服务属于后续扩展，不作为本轮重构完成的前提。
第 18 节记录结合现有代码发现的进一步改进方向。正确性修复与结构迁移独立实施，
待验证风险不直接作为已确认缺陷，后续服务化与性能工作也不自动扩入本轮范围。
第 20 节记录个人工具的“研究主库 + 行情缓存库”方案：主库低频更新，预测按需补拉，
下次重构实施；暂不按市场、年份或股票拆分研究主库，也不设计远端增量同步。

## 2. 架构原则

### 2.1 业务域优先

- `market_data`：证券元信息、行情模型、外部行情源、缓存和行情仓储；
- `quantitative`：指标、特征、信号、回测、机器学习和量化分析；
- `financial_reports`：财报模型、字段归一、解析、存储和基本面分析。

数据库、HTTP、日志、数据拉取命令和 UI 都不是业务域。

### 2.2 单向依赖

```text
tools / interfaces
        │
        ▼
application
        │
        ├──────────────┬──────────────────┐
        ▼              ▼                  ▼
market_data      quantitative      financial_reports
        │              │                  │
        └──────────────┴──────────────────┘
                       │
                       ▼
                infrastructure
                       │
                       ▼
                     core
```

依赖规则：

- `core` 只依赖 Python 标准库；
- `infrastructure` 不包含行情、指标或财报字段；
- 领域模块不能导入 `application` 或 `tools`；
- `application` 可以组合多个领域的公开接口；
- `tools` 原则上只调用 `application`，不组合领域内部对象；
- 测试可以访问内部模块，但不能成为运行时代码依赖。

### 2.3 纯计算与 I/O 分离

- `indicators` 输入数值序列、输出数值序列，不访问数据库、网络或文件；
- `signals` 根据行情和特征判断形态，不自行抓取行情；
- `backtesting` 接收明确的数据与配置，anchor 后的数据只用于验证；
- Provider 只获取并标准化外部数据；
- Repository 只负责持久化；
- 应用服务负责编排获取、计算、保存和报告生成。

RSI、EMA、ATR 等无状态算法继续使用纯函数，不设置没有必要的 `IndicatorBase`。
外部行情源需要统一行为和契约测试，因此保留 `QuoteProvider` 抽象。

## 3. 完整目标目录

```text
Trader/
├─ pyproject.toml
├─ README.md
├─ .gitignore
│
├─ src/
│  └─ trader/
│     ├─ __init__.py
│     ├─ core/
│     │  ├─ __init__.py
│     │  ├─ config.py
│     │  ├─ logging.py
│     │  └─ paths.py
│     ├─ infrastructure/
│     │  ├─ __init__.py
│     │  └─ sqlite.py
│     ├─ market_data/
│     │  ├─ __init__.py
│     │  ├─ instruments/
│     │  │  ├─ __init__.py
│     │  │  ├─ models.py
│     │  │  └─ repository.py
│     │  ├─ universes/
│     │  │  ├─ __init__.py
│     │  │  ├─ models.py
│     │  │  ├─ provider.py
│     │  │  ├─ repository.py
│     │  │  └─ providers/
│     │  │     ├─ __init__.py
│     │  │     ├─ csi.py
│     │  │     ├─ hang_seng.py
│     │  │     └─ sp500.py
│     │  └─ quotes/
│     │     ├─ __init__.py
│     │     ├─ models.py
│     │     ├─ provider.py
│     │     ├─ factory.py
│     │     ├─ cache.py
│     │     ├─ repository.py
│     │     └─ providers/
│     │        ├─ __init__.py
│     │        ├─ futu.py
│     │        ├─ sina.py
│     │        └─ tencent.py
│     ├─ quantitative/
│     │  ├─ __init__.py
│     │  ├─ indicators/
│     │  │  ├─ __init__.py
│     │  │  ├─ primitives.py
│     │  │  ├─ trend.py
│     │  │  ├─ momentum.py
│     │  │  ├─ volume.py
│     │  │  ├─ liquidity.py
│     │  │  └─ risk.py
│     │  ├─ features/
│     │  │  ├─ __init__.py
│     │  │  ├─ models.py
│     │  │  ├─ catalog.py
│     │  │  ├─ calculator.py
│     │  │  └─ repository.py
│     │  ├─ signals/
│     │  │  ├─ __init__.py
│     │  │  ├─ models.py
│     │  │  ├─ rule.py
│     │  │  ├─ registry.py
│     │  │  ├─ engine.py
│     │  │  ├─ trend.py
│     │  │  ├─ momentum.py
│     │  │  ├─ patterns.py
│     │  │  └─ volume_risk.py
│     │  ├─ backtesting/
│     │  │  ├─ __init__.py
│     │  │  ├─ models.py
│     │  │  ├─ service.py
│     │  │  └─ repository.py
│     │  ├─ ml/
│     │  │  ├─ __init__.py
│     │  │  ├─ dataset.py
│     │  │  ├─ sequence_dataset.py
│     │  │  ├─ models.py
│     │  │  ├─ training.py
│     │  │  ├─ evaluation.py
│     │  │  ├─ inference.py
│     │  │  └─ signal.py
│     │  └─ analysis/
│     │     ├─ __init__.py
│     │     ├─ models.py
│     │     ├─ aggregation.py
│     │     ├─ service.py
│     │     └─ report.py
│     ├─ financial_reports/
│     │  ├─ __init__.py
│     │  ├─ models.py
│     │  ├─ field_mapping.py
│     │  ├─ parser.py
│     │  ├─ parser_factory.py
│     │  ├─ repository.py
│     │  ├─ analysis.py
│     │  └─ parsers/
│     │     ├─ __init__.py
│     │     ├─ common.py
│     │     └─ hk_ifrs.py
│     └─ application/
│        ├─ __init__.py
│        ├─ refresh_universes.py
│        ├─ sync_market_history.py
│        ├─ update_market_data.py
│        ├─ materialize_features.py
│        ├─ run_backtest.py
│        ├─ analyze_stock.py
│        └─ build_stock_report.py
│
├─ tools/
│  ├─ universe_manager/
│  ├─ kline_fetcher/
│  ├─ financial_fetcher/
│  ├─ stock_advisor/
│  ├─ stock_widget/
│  ├─ db_inspector/
│  └─ fund_holdings/
├─ tests/
│  ├─ unit/
│  │  ├─ market_data/
│  │  ├─ quantitative/
│  │  └─ financial_reports/
│  ├─ contract/providers/
│  ├─ integration/
│  ├─ application/
│  └─ e2e/
├─ docs/
├─ config/providers/
│  ├─ quotes/
│  │  ├─ futu.json
│  │  ├─ sina.json
│  │  └─ tencent.json
│  └─ universes/
│     ├─ csi.json
│     ├─ hang_seng.json
│     └─ sp500.json
├─ data/
│  ├─ raw/financial_reports/
│  └─ processed/financial_reports/
├─ var/
│  ├─ database/
│  ├─ cache/                       # 行情缓存库，见第 20 节
│  ├─ logs/
│  └─ reports/
└─ artifacts/
   ├─ models/
   └─ backtesting/
```

`src/` 是最终目标，不要求第一阶段立即完成。先建立行为基线和模块边界，再迁移
命名空间，避免一次性修改全部 import。

## 4. 模块职责

### 4.1 `core` 与 `infrastructure`

`core` 保存类型化配置、日志配置和统一路径解析，禁止放入股票业务代码。
`infrastructure.sqlite` 只处理连接、事务、UPSERT 等通用能力；可以知道如何建表，
但不能知道 `kline_daily` 的业务字段。

### 4.2 `market_data`

- `instruments`：证券主数据，包括稳定 ID、代码、名称、市场、币种、证券类型、
  上市/退市状态和 Provider 专用代码；
- `universes`：股票池定义、指数成分 Provider、当前成员和成员变更历史；
- `quotes`：`DailyQuote`、复权方式、行情 Provider、缓存和日 K 线仓储；
- `universes/providers`：沪深 300、恒指和标普 500 成分获取适配器；
- `quotes/providers`：Futu、腾讯、新浪等行情适配器。

`StockFundamental` 不属于行情核心模型，迁入财报/基本面领域。原静态
`quote_api.stock_meta.STOCK_META` 在迁移完成后删除，但证券元信息这个概念不能
删除，而是改为由 `InstrumentRepository` 持久化管理。指数成员关系不写入证券主表，
由 `UniverseRepository` 单独维护。

`DbQuoteAPI` 若保留，必须明确它是本地只读适配器，不能和线上 Provider 混淆数据
新鲜度。

建议公开入口：

```python
from trader.market_data import (
    DailyQuote,
    Instrument,
    InstrumentRepository,
    KlineAdjustment,
    MarketDataRepository,
    QuoteProvider,
    QuoteProviderFactory,
    Universe,
    UniverseRepository,
)
```

### 4.3 `quantitative`

- `indicators`：纯数学算法，不解释方向；
- `features`：从行情生成可存储特征，`catalog.py` 是特征定义唯一来源；
- `signals`：根据行情与特征判断形态，显式注册规则；
- `backtesting`：PIT 回测、事件去重、基准比较、显著性和样本外验证；
- `ml`：数据集、训练、评估、推理和 ML 信号；
- `analysis`：量化域内部的特征、信号和回测统计聚合。

`features` 不创建线上 Provider。现有特征物化流程中的跨域 I/O 移到
`application.materialize_features`。回测统计和模型文件属于产物，不放在源码包。

### 4.4 `financial_reports`

负责财报统一模型、字段映射、解析器、持久化和 PIT 基本面分析。原始 PDF 与解析
JSON 不放在 Python 包或工具目录中。

### 4.5 `application`

应用层是跨领域编排的唯一位置：

| 服务 | 职责 |
|---|---|
| `refresh_universes` | 获取三大指数成分、规范化证券、计算成员变更并保存快照 |
| `query_universes`（下次重构待实现） | 查询指数列表、已保存成分、快照及历史成员，不隐式请求外部数据源；见第 19 节 |
| `sync_market_history` | 对当前股票池及指定白银标的补齐最近十年日 K 线 |
| `update_market_data` | 选择 Provider、增量拉取并保存行情 |
| `materialize_features` | 读取行情、计算并保存特征 |
| `run_backtest` | 选择标的与截止点、执行回测、保存产物 |
| `analyze_stock` | 获取 PIT 行情和量化结果，返回应用 DTO |
| `forecast_stock`（下次重构待实现） | 组合主库、行情缓存与 Provider 补齐预测窗口，在内存中计算特征并使用指定模型预测；见第 20 节 |
| `build_stock_report` | 组合量化、基本面及展示数据 |

应用层不包含指标公式、SQL 或 PDF 解析规则。

查询与数据准备的目标边界见第 18.1 节：查询不隐式物化特征，数据准备由显式用例承担。
现有报告入口的自动准备行为需通过独立行为修复与兼容策略迁移，不能在移动代码时悄然改变。

`application` 与各业务域继续使用 Python，不为接入 OpenWorkspace 迁移到
JavaScript/TypeScript。应用 DTO 不依赖 FastAPI、Vue 或 PySide6；HTTP、JSON 和
界面事件的转换由入口适配层完成，具体边界见第 17 节。

### 4.6 `tools`

`tools` 只负责参数、协议和展示适配。CLI、Web 和桌面入口调用应用服务，将应用 DTO
渲染成 Markdown、JSON 或界面组件，不直接计算指标、判断信号或拼接 SQL。

`fund_holdings` 暂时保持独立工具；等领域模型稳定并被其它功能复用时，再考虑新增
`portfolio` 或 `funds` 领域。

## 5. 核心数据流

### 5.1 股票池刷新

```text
tools/universe_manager refresh
  → RefreshUniversesService
  → ConstituentProvider.fetch_constituents(as_of)
  → normalize Instrument + provider symbols
  → validate completeness and uniqueness
  → save the complete constituent snapshot
  → compare with the previous successful snapshot
  → transaction:
      upsert instruments
      insert snapshot and all snapshot members
      close removed memberships
      insert added memberships
      mark the new snapshot active
      save refresh audit
  → UniverseRefreshResult
```

成分股“删除”的准确语义是从当前股票池退出：把成员记录的 `effective_to` 设为刷新
生效日。不得删除证券主数据、历史成员关系或已经拉取的 K 线。若证券以后重新入选，
创建新的成员有效期记录。

Provider 每次返回的全部成分股都必须入库，而不只是保存本次新增和删除的差异：

- 证券自身属性写入或更新 `instrument`；
- Provider 专用代码写入 `instrument_provider_symbol`；
- 本次完整名单写入 `universe_snapshot_member`；
- 调入调出后的有效期写入 `universe_membership`；
- 权重、排名、源端原始字段等属于本次快照的数据随快照成员保存。

只有通过数量范围、代码唯一性、必填字段和异常变更比例检查的完整快照才允许成为
活动快照。空响应、部分分页失败或异常大幅删减必须标记刷新失败，并继续使用上一份
成功快照。

首次接入的数据源如果只能返回当前成分，则只能从首次观测日期开始形成可靠的成员
历史。若未来回测要求消除幸存者偏差，必须另外导入历史成分及其真实生效日期，不能
把今天的成分股假装成十年前的成分股。

下次重构计划将该能力通过第 19 节的成分股 API 暴露：POST 显式提交刷新任务，GET 查询
已保存结果。HTTP 与 CLI 复用 `RefreshUniversesService`，不在路由中复制抓取和入库逻辑。

### 5.2 十年行情同步

```text
tools/kline_fetcher sync-universe --years 10
  → SyncMarketHistoryService
  → UniverseRepository.list_active_members(CSI300, HSI, SP500)
  → append configured silver instrument
  → de-duplicate by instrument_id
  → route each instrument to a supported QuoteProvider
  → determine missing date range
  → fetch in resumable chunks
  → MarketDataRepository.upsert_many
  → SyncRunResult
```

同步规则：

- 第一次加入股票池：拉取 `max(上市日, 当前日期 - 10 年)` 至今的数据；
- 已存在行情：从数据库最后交易日之后增量拉取，并定期扫描内部缺口；
- 新增成分：在同一次刷新流程之后进入十年回填队列；
- 退出成分：停止日常更新，但保留主数据和历史行情；手工固定标的可继续更新；
- 所有写入必须幂等，重复执行不能产生重复 K 线；
- 按标的记录成功、失败、重试次数和同步水位，单只失败不回滚整个股票池；
- Provider 调用需要限速、指数退避、分段下载和可恢复执行；
- 股票池刷新成功后才切换活动快照，部分结果不能覆盖上一份有效快照。

“白银”必须落实为具体 `Instrument`。若保持当前行为，它是美股白银 ETF `SLV`；
若改为 `XAG/USD` 现货或沪银期货，则属于不同标的，后者还需要主力连续/换月规则，
不能继续复用 `SLV` 的历史数据。白银通过手工维护的 `CORE_ASSETS` 股票池加入同步，
而不是硬编码到指数成分列表。

### 5.3 周期行情更新与特征物化

个人使用不要求每天更新研究主库，按配置每一至两周或每月执行，也可手动触发。
第 20 节实施后，正式更新先复用有效行情缓存，再向 Provider 补齐剩余缺口；预测时
按需补拉属于独立用例，不隐式触发本节的主库写入与特征物化。

```text
tools/kline_fetcher
  → UpdateMarketDataService
  → QuoteProviderFactory
  → QuoteProvider.fetch_klines
  → MarketDataRepository.save_many

MaterializeFeaturesService
  → MarketDataRepository.get_range
  → FeatureCalculator.compute
  → FeatureRepository.save_many
```

两个步骤可以由同一命令连续触发，但必须保持为可独立测试的应用服务。

### 5.4 信号、回测与报告

```text
quotes + feature snapshots
  → SignalContext
  → SignalEngine
  → explicit rule registry
  → BacktestService
  → BacktestArtifact

stock_advisor CLI / Web
  → BuildStockReportService
      ├─ QuantitativeAnalysisService
      └─ FinancialReport analysis
  → StockReport DTO
  → Markdown / JSON renderer
```

CLI 与 Web 必须共享 `BuildStockReportService`，只保留协议和渲染差异。

## 6. 存储所有权与 Git 策略

| 数据 | 所有者 | 目标位置 |
|---|---|---|
| 证券主数据及 Provider 代码 | `market_data.instruments.repository` | `var/database/stock_data.db` |
| 股票池与成员有效期 | `market_data.universes.repository` | 同一 SQLite 文件中的领域表 |
| 日 K 线 | `market_data.quotes.repository` | 同一 SQLite 文件中的领域表 |
| 预测补拉的日 K 线缓存 | `market_data.quotes` 的缓存 Repository | `var/cache/market_cache.db`，见第 20 节 |
| 量化特征 | `quantitative.features.repository` | 同一 SQLite 文件中的领域表 |
| 财报数据 | `financial_reports.repository` | 同一 SQLite 文件中的领域表 |
| 原始财报 PDF | 外部数据输入 | `data/raw/financial_reports` |
| 解析财报 JSON | 可重建数据 | `data/processed/financial_reports` |
| ML 模型 | `quantitative.ml` 产物 | `artifacts/models` |
| 回测统计 | `quantitative.backtesting` 产物 | `artifacts/backtesting` |
| 生成报告 | 运行产物 | `var/reports` |
| 日志 | 运行产物 | `var/logs` |

每个 Repository 只创建、迁移和查询自己拥有的表。共享 SQLite 文件不代表共享表
所有权。

研究数据继续保存在一个主库，缓存库只承担预测增量暂存。两个数据库都是本地运行
数据，目标为不纳入 Git；缓存库不代替主库备份，也不是股票池成员名单的独立存储。

### 6.1 股票池相关表

| 表 | 关键字段 | 说明 |
|---|---|---|
| `instrument` | `instrument_id`, `canonical_symbol`, `name`, `asset_type`, `exchange`, `currency`, `listing_date`, `status` | 稳定的证券主数据 |
| `instrument_provider_symbol` | `instrument_id`, `provider`, `provider_symbol`, `valid_from`, `valid_to` | 隔离不同数据源的代码差异 |
| `universe` | `universe_id`, `code`, `name`, `kind`, `source` | `CSI300`、`HSI`、`SP500`、`CORE_ASSETS` |
| `universe_snapshot` | `snapshot_id`, `universe_id`, `as_of`, `fetched_at`, `source`, `checksum`, `is_active` | 一次经过验证的完整成分快照 |
| `universe_snapshot_member` | `snapshot_id`, `instrument_id`, `weight`, `rank`, `source_payload` | 该快照中的全部成分及源端补充字段 |
| `universe_membership` | `universe_id`, `instrument_id`, `effective_from`, `effective_to`, `weight`, `observed_at`, `source` | 可做 PIT 查询的成员历史 |
| `universe_refresh_run` | `run_id`, `universe_id`, `as_of`, `fetched_at`, `checksum`, `status`, `added_count`, `removed_count` | 刷新审计与失败恢复 |
| `market_sync_run` | `run_id`, `started_at`, `finished_at`, `status`, `requested_years` | 一次行情同步任务 |
| `market_sync_item` | `run_id`, `instrument_id`, `from_date`, `to_date`, `status`, `rows_written`, `error` | 标的级进度与断点恢复 |

### 6.2 SQLite 物理表设计

以下 DDL 是目标结构。实际迁移通过 Repository migration 分版本执行，不能直接在
历史数据库上整段运行。

统一约定：

- 主键使用内部 `INTEGER` ID，业务代码不再把名称或 Provider symbol 当主键；
- 日期使用 ISO `YYYY-MM-DD`，时间戳使用 UTC；
- `effective_from` 包含当天，`effective_to` 不包含当天，即 `[from, to)`；
- 金额和价格使用 SQLite `REAL`，Provider 原始精度需要原样审计时保留原始载荷；
- JSON 使用 `TEXT` 保存，只承载源端补充字段，不代替正常关系字段；
- 每个数据库连接必须执行 `PRAGMA foreign_keys = ON`；
- 历史快照和已结束成员关系默认不可修改、不可级联删除。

#### 6.2.1 证券主数据

```sql
CREATE TABLE instrument (
    instrument_id       INTEGER PRIMARY KEY,           -- 项目内部稳定证券 ID
    canonical_symbol    TEXT NOT NULL UNIQUE,           -- 项目统一代码，如 XHKG:00700
    local_symbol        TEXT NOT NULL,                  -- 交易所本地代码，如 00700
    name                TEXT NOT NULL,                  -- 主要展示名称
    name_en             TEXT,                           -- 英文名称，可为空
    asset_type          TEXT NOT NULL,                  -- 资产类型，如 equity、etf、spot、future
    market              TEXT NOT NULL,                  -- 市场，如 CN、HK、US
    exchange            TEXT NOT NULL,                  -- 交易所 MIC 或项目统一交易所代码
    currency            TEXT,                           -- 计价币种，如 CNY、HKD、USD
    timezone            TEXT,                           -- 交易所 IANA 时区
    listing_date        TEXT,                           -- 上市日期，YYYY-MM-DD
    delisting_date      TEXT,                           -- 退市日期，YYYY-MM-DD；未退市为空
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'delisted')), -- 证券状态
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 首次入库时间（UTC）
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 最近更新时间（UTC）
    CHECK (listing_date IS NULL OR length(listing_date) = 10),
    CHECK (delisting_date IS NULL OR length(delisting_date) = 10),
    UNIQUE (exchange, local_symbol)
);

CREATE INDEX idx_instrument_market_status
    ON instrument(market, status);

CREATE TABLE instrument_provider_symbol (
    instrument_id       INTEGER NOT NULL,               -- 关联的内部证券 ID
    provider            TEXT NOT NULL,                  -- 数据源标识，如 futu、tencent
    provider_symbol     TEXT NOT NULL,                  -- 数据源使用的证券代码
    valid_from          TEXT NOT NULL DEFAULT '0001-01-01', -- 代码生效日期（含）
    valid_to            TEXT,                           -- 代码失效日期（不含）；当前有效为空
    is_primary          INTEGER NOT NULL DEFAULT 1 CHECK (is_primary IN (0, 1)), -- 是否首选代码
    metadata_json       TEXT,                           -- 数据源专用扩展属性 JSON
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 映射创建时间（UTC）
    PRIMARY KEY (instrument_id, provider, valid_from),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE UNIQUE INDEX uq_provider_symbol_open
    ON instrument_provider_symbol(provider, provider_symbol)
    WHERE valid_to IS NULL;

CREATE INDEX idx_provider_symbol_lookup
    ON instrument_provider_symbol(instrument_id, provider, valid_to);
```

`canonical_symbol` 使用项目自己的稳定格式，例如 `XSHG:600000`、`XHKG:00700`、
`XNAS:AAPL`；Provider 使用的 `sh600000`、`HK.00700` 等形式只存在于
`instrument_provider_symbol`。

#### 6.2.2 股票池、刷新任务与完整快照

```sql
CREATE TABLE universe (
    universe_id         INTEGER PRIMARY KEY,            -- 项目内部稳定股票池 ID
    code                TEXT NOT NULL UNIQUE,            -- 股票池代码，如 CSI300、HSI、SP500
    name                TEXT NOT NULL,                   -- 股票池展示名称
    kind                TEXT NOT NULL,                   -- 类型，如 index、manual
    market              TEXT,                            -- 主要所属市场；跨市场时可为空
    is_enabled          INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)), -- 是否参与刷新
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间（UTC）
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 最近更新时间（UTC）
);

CREATE TABLE universe_refresh_run (
    run_id              INTEGER PRIMARY KEY,            -- 股票池刷新任务 ID
    universe_id         INTEGER NOT NULL,                -- 本次刷新的股票池 ID
    provider            TEXT NOT NULL,                   -- 成分数据源标识
    requested_as_of     TEXT NOT NULL,                   -- 请求的成分时点，YYYY-MM-DD
    started_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 任务开始时间（UTC）
    finished_at         TEXT,                            -- 任务结束时间（UTC）
    status              TEXT NOT NULL
                        CHECK (status IN ('running', 'succeeded', 'failed')), -- 执行状态
    member_count        INTEGER,                         -- 成功抓取的完整成员数
    added_count         INTEGER,                         -- 相比上一快照的调入数
    removed_count       INTEGER,                         -- 相比上一快照的调出数
    checksum            TEXT,                            -- 规范化完整名单的内容校验值
    error_message       TEXT,                            -- 失败原因；成功时为空
    FOREIGN KEY (universe_id) REFERENCES universe(universe_id)
);

CREATE INDEX idx_universe_refresh_run_lookup
    ON universe_refresh_run(universe_id, requested_as_of, status);

CREATE TABLE universe_snapshot (
    snapshot_id         INTEGER PRIMARY KEY,            -- 完整成分快照 ID
    universe_id         INTEGER NOT NULL,                -- 所属股票池 ID
    refresh_run_id      INTEGER NOT NULL UNIQUE,         -- 生成该快照的刷新任务 ID
    as_of_date          TEXT NOT NULL,                   -- 快照业务生效日期，YYYY-MM-DD
    fetched_at          TEXT NOT NULL,                   -- 数据实际抓取时间（UTC）
    provider            TEXT NOT NULL,                   -- 成分数据源标识
    checksum            TEXT NOT NULL,                   -- 规范化完整名单的内容校验值
    member_count        INTEGER NOT NULL CHECK (member_count > 0), -- 快照成员总数
    is_active           INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)), -- 是否当前快照
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 入库时间（UTC）
    FOREIGN KEY (universe_id) REFERENCES universe(universe_id),
    FOREIGN KEY (refresh_run_id) REFERENCES universe_refresh_run(run_id),
    UNIQUE (universe_id, as_of_date, provider, checksum)
);

CREATE UNIQUE INDEX uq_universe_active_snapshot
    ON universe_snapshot(universe_id)
    WHERE is_active = 1;

CREATE INDEX idx_universe_snapshot_asof
    ON universe_snapshot(universe_id, as_of_date DESC);

CREATE TABLE universe_snapshot_member (
    snapshot_id         INTEGER NOT NULL,                -- 所属完整快照 ID
    instrument_id       INTEGER NOT NULL,                -- 成分证券 ID
    weight              REAL,                            -- 指数权重，统一为 0 到 1；未知为空
    rank                INTEGER,                         -- 数据源给出的成分排名；未知为空
    source_payload      TEXT,                            -- 该成员未归一化的源端扩展字段 JSON
    PRIMARY KEY (snapshot_id, instrument_id),
    FOREIGN KEY (snapshot_id) REFERENCES universe_snapshot(snapshot_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    CHECK (weight IS NULL OR (weight >= 0 AND weight <= 1)),
    CHECK (rank IS NULL OR rank > 0)
);

CREATE INDEX idx_snapshot_member_instrument
    ON universe_snapshot_member(instrument_id, snapshot_id);
```

权重统一存为 `[0, 1]` 比例；源端给出百分数时由 Provider 归一化。完整快照不可只存
diff，`member_count` 必须与 `universe_snapshot_member` 实际行数一致后才能激活。

#### 6.2.3 成员有效期历史

```sql
CREATE TABLE universe_membership (
    universe_id          INTEGER NOT NULL,               -- 股票池 ID
    instrument_id        INTEGER NOT NULL,               -- 成分证券 ID
    effective_from       TEXT NOT NULL,                  -- 成员关系生效日期（含）
    effective_to         TEXT,                           -- 成员关系结束日期（不含）；当前成员为空
    effective_date_source TEXT NOT NULL
                         CHECK (effective_date_source IN ('official', 'observed')), -- 日期来源
    opened_snapshot_id   INTEGER NOT NULL,               -- 首次确认本有效期的快照 ID
    last_seen_snapshot_id INTEGER NOT NULL,              -- 最近一次仍确认其存在的快照 ID
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 记录创建时间（UTC）
    updated_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 记录更新时间（UTC）
    PRIMARY KEY (universe_id, instrument_id, effective_from),
    FOREIGN KEY (universe_id) REFERENCES universe(universe_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    FOREIGN KEY (opened_snapshot_id) REFERENCES universe_snapshot(snapshot_id),
    FOREIGN KEY (last_seen_snapshot_id) REFERENCES universe_snapshot(snapshot_id),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE UNIQUE INDEX uq_universe_open_membership
    ON universe_membership(universe_id, instrument_id)
    WHERE effective_to IS NULL;

CREATE INDEX idx_universe_membership_asof
    ON universe_membership(universe_id, effective_from, effective_to);

CREATE INDEX idx_instrument_membership_history
    ON universe_membership(instrument_id, universe_id, effective_from);
```

如果数据源给出正式调入日期，使用 `official`；如果系统只观察到某次刷新前后发生
变化，则使用刷新生效日并标记为 `observed`，不能伪装成官方生效日期。

当前成员查询：

```sql
SELECT i.*
FROM universe_membership m
JOIN universe u ON u.universe_id = m.universe_id
JOIN instrument i ON i.instrument_id = m.instrument_id
WHERE u.code = :universe_code
  AND m.effective_to IS NULL;
```

历史时点成员查询：

```sql
SELECT i.*
FROM universe_membership m
JOIN universe u ON u.universe_id = m.universe_id
JOIN instrument i ON i.instrument_id = m.instrument_id
WHERE u.code = :universe_code
  AND m.effective_from <= :anchor_date
  AND (m.effective_to IS NULL OR :anchor_date < m.effective_to);
```

#### 6.2.4 日 K 线

```sql
CREATE TABLE kline_daily (
    instrument_id       INTEGER NOT NULL,                -- 行情所属证券 ID
    trade_date          TEXT NOT NULL,                   -- 交易日，YYYY-MM-DD
    adjustment          TEXT NOT NULL
                        CHECK (adjustment IN ('none', 'qfq', 'hfq')), -- 复权方式
    open                REAL NOT NULL,                   -- 开盘价
    high                REAL NOT NULL,                   -- 最高价
    low                 REAL NOT NULL,                   -- 最低价
    close               REAL NOT NULL,                   -- 收盘价
    pre_close           REAL,                            -- 前一交易日收盘价
    volume              REAL,                            -- 成交量，Provider 适配后统一单位
    turnover            REAL,                            -- 成交额，币种见 currency
    turnover_rate       REAL,                            -- 换手率，统一为百分比数值
    currency            TEXT,                            -- 价格和成交额币种
    source_provider     TEXT NOT NULL,                   -- 当前规范化记录的数据来源
    fetched_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 抓取/更新时间（UTC）
    PRIMARY KEY (instrument_id, trade_date, adjustment),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    CHECK (high >= low),
    CHECK (volume IS NULL OR volume >= 0),
    CHECK (turnover IS NULL OR turnover >= 0)
);

CREATE INDEX idx_kline_daily_date
    ON kline_daily(trade_date);

CREATE INDEX idx_kline_daily_latest
    ON kline_daily(instrument_id, adjustment, trade_date DESC);
```

规范化表每个标的、日期和复权方式只保留一条选定行情，`source_provider` 记录来源。
如果以后需要并行保留多源原始行情，应另建 source/raw 表，不能直接把 Provider 加入
该表主键后让业务层任意选择。

#### 6.2.5 行情同步任务与断点

```sql
CREATE TABLE market_sync_run (
    run_id              INTEGER PRIMARY KEY,            -- 行情同步任务 ID
    started_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 任务开始时间（UTC）
    finished_at         TEXT,                            -- 任务结束时间（UTC）
    status              TEXT NOT NULL
                        CHECK (status IN ('running', 'partial', 'succeeded', 'failed')), -- 状态
    requested_years     INTEGER NOT NULL CHECK (requested_years > 0), -- 请求回溯年数
    adjustment          TEXT NOT NULL,                   -- 本次同步使用的复权方式
    universe_codes_json TEXT NOT NULL,                   -- 本次涉及的股票池代码 JSON 数组
    total_count         INTEGER NOT NULL DEFAULT 0,      -- 待处理证券总数
    succeeded_count     INTEGER NOT NULL DEFAULT 0,      -- 成功证券数
    failed_count        INTEGER NOT NULL DEFAULT 0,      -- 失败证券数
    error_message       TEXT                             -- 任务级失败信息
);

CREATE TABLE market_sync_item (
    run_id              INTEGER NOT NULL,                -- 所属行情同步任务 ID
    instrument_id       INTEGER NOT NULL,                -- 当前处理的证券 ID
    provider            TEXT NOT NULL,                   -- 实际使用的行情数据源
    adjustment          TEXT NOT NULL,                   -- 复权方式
    requested_from      TEXT NOT NULL,                   -- 请求起始日（含）
    requested_to        TEXT NOT NULL,                   -- 请求结束日（含）
    completed_through   TEXT,                            -- 已成功同步到的最后交易日
    status              TEXT NOT NULL
                        CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'skipped')), -- 状态
    attempts            INTEGER NOT NULL DEFAULT 0,      -- 已尝试次数
    rows_written        INTEGER NOT NULL DEFAULT 0,      -- 本任务累计写入/更新行数
    error_message       TEXT,                            -- 最近一次失败原因
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 最近状态更新时间（UTC）
    PRIMARY KEY (run_id, instrument_id, adjustment),
    FOREIGN KEY (run_id) REFERENCES market_sync_run(run_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id)
);

CREATE INDEX idx_market_sync_item_resume
    ON market_sync_item(status, updated_at);
```

同步任务表只负责执行审计和断点恢复；实际行情是否完整仍以 `kline_daily` 和交易日历
缺口检查为准，不能只因为某次任务状态为成功就永久认为数据完整。

#### 6.2.6 股票池刷新事务

刷新采用“先抓取并验证，后单事务切换”：

```text
1. 创建 universe_refresh_run(status=running)
2. 在事务外完成全部分页抓取、规范化、去重和完整性校验
3. BEGIN IMMEDIATE
4. upsert instrument 与 instrument_provider_symbol
5. 插入 universe_snapshot 及全部 universe_snapshot_member（尚未激活）
6. 根据上一活动快照维护 universe_membership 的开启、延续和结束记录
7. 将旧快照 is_active=0，将新快照 is_active=1
8. 将 refresh run 标为 succeeded 并写入计数
9. COMMIT
```

步骤 4 至 8 任一步失败都必须整体回滚。抓取或校验失败只更新 refresh run 为
`failed`，不得创建活动快照，也不得结束任何现有成员关系。

`kline_daily` 应逐步使用 `instrument_id`，并明确复权方式和来源。若允许同一标的保存
多种复权序列，主键至少包含 `(instrument_id, trade_date, adjustment)`。旧
`Symbol` 主键通过映射表和兼容查询逐步迁移，不直接重建或覆盖历史表。

三种成分数据不能塞进单个反复覆盖的“当前股票池表”。完整快照用于回答“某次刷新
实际取得了什么”，成员有效期用于回答“某个历史时点哪些证券属于该指数”。前者便于
审计和重新计算差异，后者便于高效 PIT 查询。

默认不提交 `var/`、可重建解析结果、本地训练模型、密钥和机器相关配置。可以提交
源码、文档、无密钥示例配置、小型稳定测试夹具，以及明确作为发布基线且带版本元
数据的产物。历史大文件是否使用 Git LFS、Release artifact 或外部数据目录，需要
在迁移前单独确认；重构不能直接删除原文件。

## 7. 配置、异常与资源管理

- `pyproject.toml` 声明 Python 版本、依赖、测试配置和命令入口；
- Provider 的非敏感配置放在 `config/providers`；
- 密钥只来自环境变量或本地未跟踪配置；
- `core.paths` 统一解析数据、模型和日志目录，测试可覆盖为临时目录；
- Provider 将第三方异常转换为统一 `ProviderError`；
- “不支持”“无数据”“请求失败”使用不同语义；
- Repository 使用上下文管理器并明确事务边界；
- import 模块时不创建数据库连接、不访问网络、不写日志文件；
- Futu 等长连接由工厂或应用生命周期显式关闭。

业务错误、部分结果和传输失败的分类见第 18.3 节；常驻服务的资源生命周期与调用限制
见第 18.6 节。框架异常应在入口层映射，不能反向进入领域模型。

## 8. 测试与质量门槛

测试分为：

- `unit`：指标、模型、映射和隔离的应用逻辑；
- `contract/providers`：所有行情 Provider 共用的行为契约；
- `integration`：SQLite、真实 PDF 样本和可选外部 API；
- `application`：临时数据库与假 Provider 驱动完整用例；
- `e2e`：少量 CLI/Web 冒烟测试。

增加架构检查，保证：

- `trader.core` 不导入其它业务包；
- 领域包不导入 `trader.application` 或 `tools`；
- `tools` 不导入 features、signals、backtesting 等内部实现；
- `indicators` 不导入数据库、网络客户端和文件系统模块；
- Provider 的测试不再放在源码目录。

重构前必须固定以下回归样本：

- 至少一个 A 股、港股和美股的行情标准化结果；
- 三个指数的成分股标准化、增删差异和空/部分响应保护；
- 成分退出后历史成员关系及 K 线仍然存在；
- 新成分首次回填十年、已有成分断点续传和内部缺口修复；
- 前复权、后复权、不复权行为；
- 一组指标及特征数值快照；
- 一组信号触发与未触发结果；
- 固定截止日期的回测统计；
- 固定报告期的财报解析结果；
- 一份完整股票分析报告的结构化结果。

浮点值使用明确容差，时间相关测试固定日期，不依赖运行当天。

跨项目契约与故障场景补充见第 18.8 节。阶段 0 先记录实际行为和已知偏差；确认缺陷后
用独立回归用例证明修复，再记录基线变更原因。不得仅更新快照使错误行为成为验收标准。

## 9. 现有文件迁移映射

| 当前路径 | 目标路径或处理方式 |
|---|---|
| `config.py` | `src/trader/core/config.py`，旧模块临时 re-export |
| `utils/logger.py` | `src/trader/core/logging.py` |
| `utils/stock_updater.py` | `application/update_market_data.py` |
| `utils/ratio.py` | `quantitative/analysis/ratio.py` 或独立研究工具 |
| `utils/data_types.py` | 类型移动到实际拥有它的领域 |
| `infrastructure/sqlite.py` | `src/trader/infrastructure/sqlite.py` |
| `quote_api/quote_base.py` | 拆为 `market_data/quotes/models.py` 与 `quotes/provider.py` |
| `quote_api/stock_meta.py` | 静态内容迁入 `instrument` 表作为初始种子，调用接口转为 `market_data/instruments/repository.py`；兼容期结束后删除静态字典 |
| `quote_api/futu,sina,tencent` | `market_data/quotes/providers/` |
| `quote_api/quote_factory.py` | `market_data/quotes/factory.py` |
| `quote_api/cached_api.py` | `market_data/quotes/cache.py` |
| `quote_api/repository.py` | `market_data/quotes/repository.py` |
| `quote_api/db_api.py` | 本地读取适配器，或由 Repository 查询替代 |
| `quantitative/*` | 对应迁入 `src/trader/quantitative` |
| `quantitative/features/materialization.py` | `application/materialize_features.py` |
| `quantitative/backtesting/signal_statistics.json` | `artifacts/backtesting/` |
| `database/*.db` | 验证与备份后迁入 `var/database/` |
| `database/*.npz` | 验证后迁入 `artifacts/models/` |
| `tools/financial_fetcher/*/*.pdf` | `data/raw/financial_reports/` |
| `tools/financial_fetcher/parsed/*.json` | `data/processed/financial_reports/` |
| `tools/stock_advisor` 业务编排 | `application/build_stock_report.py` |
| `tools/stock_advisor/web_api.py` 业务编排 | 按列表、走势、报告用例移入 `application`，原模块保留 JSON 协议适配与兼容入口 |
| `tools/stock_widget` 行情获取编排 | 移入 `application` 的最新报价用例，工具保留窗口、定时器和线程适配 |

迁移优先使用 `git mv` 保留历史。每批移动后立即修复 import、运行测试并单独提交，
不夹带无关格式化。

## 10. 兼容策略

- 原 `quote_api`、`quantitative`、`financial_reports` 公共入口短期 re-export 新包；
- `python -m quantitative.cli` 等旧命令暂时转发到新入口；
- 保留 Website 调用的 `python -m tools.stock_advisor.web_api` 命令、参数及 JSON 契约，
  直到对应调用方完成迁移；新增 HTTP 服务不直接移除现有子进程桥接；
- 内部代码先切换为 `trader.*`，确认没有旧 import 后再删除兼容层；
- 数据库先继续读取旧路径，显式迁移成功后才改变默认路径；
- 数据迁移前创建备份，校验表、行数、日期范围和关键字段；
- 兼容层只转发，不保留第二套实现。

兼容策略主要保护有效调用的命令、参数和结果。第 18 节涉及的隐式写入、错误分类、
无效数值降级和公共 `db` 参数等行为调整，应单独记录影响、调用方迁移与验收结果；
需要时在旧适配层暂时保留已明确的行为，新接口采用修正后的契约。兼容不要求永久保留缺陷。

## 11. 分阶段实施计划

### 阶段 0：冻结基线

- 记录 Python 版本、依赖、命令和公共 API；
- 运行完整离线测试；
- 补齐第 8 节的行为基线；
- 为第 18 节的查询副作用、历史产物选择、错误传播和页面请求竞争建立可复现样例，
  区分当前行为、目标行为与尚未验证的风险；
- 盘点数据库、PDF、JSON、模型和报告；
- 创建专用重构分支，确保无无关修改。

验收：当前测试稳定通过，关键输出可重复生成。

### 阶段 1：建立工程骨架

- 添加 `pyproject.toml`；
- 建立 `src/trader`、基础目录和新测试目录；
- 配置 editable install、测试发现和依赖检查；
- 暂不迁移业务实现。

验收：旧命令仍可运行，新包可以正常导入。

### 阶段 2：基础设施与行情域

- 迁移配置、日志和 SQLite；
- 建立 `instrument`、Provider symbol、`universe`、membership 和刷新审计模型；
- 拆分行情模型、行情 Provider、成分 Provider 契约和适配器；
- 迁移 Repository、缓存和工厂，并导入原 `STOCK_META` 作为初始证券数据；
- 实现股票池差异计算、事务切换和 PIT 成员查询；
- 运行所有 Provider 契约测试；
- 建立旧 `quote_api` 兼容入口。

验收：三大指数能保存完整活动快照，成分变更可追溯；行情标准化结果与基线一致，
旧数据库内容不丢失。

### 阶段 3：量化域

- 依次迁移 indicators、features、signals、backtesting、ml、analysis；
- 将特征物化 I/O 移到应用层；
- 将模型和回测统计改为可配置产物路径；
- 不修改算法和统计口径。

模型与数据版本、历史产物选择的改进见第 18.2 节；先保留并验证已有版本字段，
涉及结果变化的修复与本阶段结构迁移分开，不能借迁移之机替换历史分析口径。

验收：固定样本的特征、信号、回测和分析结果在容差内一致。

### 阶段 4：财报域

- 迁移模型、解析器、字段映射、Repository 和分析；
- 将基本面类型归入该域；
- 原始财报路径改为配置；
- 不在本阶段清理 Git 历史文件。

验收：固定财报解析结果与 PIT 分析一致。

### 阶段 5：应用服务与工具瘦身

- 建立股票池刷新、十年行情同步、日常行情更新、特征物化、回测、分析和报告服务；
- CLI/Web 共享报告用例；
- 将 `web_api.py` 的列表、走势、报告编排和 `stock_widget` 的报价获取移入应用服务，
  保留本地历史查询与在线最新报价的语义差异；
- 删除 `tools` 中重复的业务编排；
- 保留兼容入口。

验收：CLI 与 Web 对相同输入产生相同结构化业务结果。
现有 Website 子进程调用契约保持兼容，桌面浮窗可独立运行；本阶段不要求启动
OpenWorkspace、引入 Vue 或部署 FastAPI。
按第 18 节提取查询/准备边界、入口错误映射和客户端适配；旧入口行为的修正按第 10 节
单独迁移。跨仓库页面与宿主修改在所属仓库实施，使用同一份契约样例联调。

下次重构待办：按第 19 节补充成分股查询用例与接口契约，HTTP 路由和持久化任务接入
随服务化阶段实施。本次仅记录方案，不要求当前阶段提前部署 API。
按第 20 节实现独立行情缓存、预测补拉和周期合入，复用现有行情更新与特征物化用例；
个人单机串行执行即可，不以并发调度或常驻服务为前提。

### 阶段 6：运行数据整理

- 在验证备份后迁移数据库、模型、财报和报告目录；
- 更新 `.gitignore`、示例配置和数据准备说明；
- 将主库和行情缓存库排除出 Git，保留配置、建表迁移和数据准备说明；已有跟踪文件
  在保留本地数据并验证备份后单独取消跟踪，本次不改写 Git 历史；
- 其他大型产物的存储策略另行确定，暂不开展数据库分片或远端增量同步。

验收：全新 clone 不依赖开发者机器绝对路径即可安装并运行离线测试。

### 阶段 7：移除兼容层

- 清除旧 import；
- 确认外部脚本已迁移；
- 移除旧顶层包和弃用命令；
- 更新 README、架构文档与模块手册。

验收：仓库仅使用 `trader.*` 命名空间，无重复实现，全部测试通过。

## 12. 每阶段操作规则

1. 一次提交只处理一个可解释的结构变化；
2. 文件移动和行为修改分开提交；
3. 先添加新实现与兼容层，再切换调用方，最后删除旧实现；
4. 数据迁移与代码迁移分开；
5. 每次提交运行受影响测试，每阶段结束运行完整离线测试；
6. 出现行为差异时先停止并解释，不更新快照掩盖问题；
7. 未验证备份前不删除或覆盖数据库、模型、PDF 和解析结果。

## 13. 风险与回滚

| 风险 | 防护措施 | 回滚方式 |
|---|---|---|
| 大量 import 同时失效 | 分域迁移、临时 re-export | 回退该域提交 |
| 新路径读取到空数据库 | 显式配置、迁移前行数校验 | 恢复旧默认路径 |
| Provider 行为变化 | 统一契约与响应夹具 | 恢复旧适配器 |
| 指标或回测结果漂移 | 固定日期黄金样本 | 回退行为修改提交 |
| CLI/Web 输出不一致 | 共享应用服务和 DTO | 暂时保留旧入口 |
| 大文件迁移丢失 | 复制、校验、备份后再切换 | 从备份恢复 |

## 14. Go/No-Go 清单

以下项目全部完成后才开始阶段 1：

- [ ] 本方案经过确认，目标目录和命名无重大分歧；
- [ ] 当前完整离线测试通过；
- [ ] 三个市场的行情回归基线已建立；
- [ ] 已选定并验证沪深 300、恒指、标普 500 的成分数据源及使用许可；
- [ ] 已确认白银代表 `SLV`、`XAG/USD` 还是沪银期货，并定义其行情口径；
- [ ] 已确认是否需要导入历史指数成分以支持无幸存者偏差回测；
- [ ] 已确认退出成分只停止活动更新，不删除历史行情和成员历史；
- [ ] 指标、信号、回测、财报和报告基线已建立；
- [ ] 所有 CLI、Web、桌面入口及调用方式已盘点；
- [ ] 数据库、财报、解析数据、模型与报告已完成文件清单；
- [ ] SQLite 已创建并验证可恢复备份；
- [ ] 已决定历史大文件继续跟踪、Git LFS 或移出 Git；
- [ ] 已确认包名使用 `trader`，行情域使用 `market_data`；
- [ ] 已确认兼容窗口和旧入口移除条件；
- [ ] 已创建重构分支，工作树无无关修改。

任一关键基线、备份或兼容范围不明确时，结论为 No-Go：只补准备工作，不移动
生产代码。

## 15. 完成定义

只有同时满足以下条件，重构才算完成：

- 核心代码全部位于 `src/trader`；
- 依赖方向符合本文档并有自动检查；
- `utils` 不再承载业务逻辑；
- `tools` 只处理参数、协议和展示；
- CLI 与 Web 共用应用服务；
- 行情、量化和财报各自拥有模型与 Repository；
- 三大指数股票池可以安全刷新，成分变更有有效期和审计记录；
- 新增成分可回填十年行情，已有成分可断点增量同步，退出成分的历史仍可查询；
- 原始数据、运行数据、模型产物和源码边界清晰；
- 固定输入下的指标、信号、回测和报告与迁移前一致；
- 所有离线测试、应用测试和选定集成测试通过；
- 旧入口按计划兼容或移除；
- README、架构文档、数据说明和模块手册与实现一致；
- 数据备份和回滚步骤经过实际验证。

第 18 节中本轮实际纳入的修复需有独立验收及基线变更记录；未纳入的后续扩展保持待办。
“与迁移前一致”针对结构迁移，已独立验证的正确性修复以修正后的明确契约为准。

## 16. 后续扩展

未来新增舆情可建立 `sentiment` 域，组合和持仓可在模型稳定后建立 `portfolio` 域。
新领域通过应用层参与综合分析，不把自身数据塞进行情表或量化特征表，也不依赖
`tools`。

## 17. UI 与 OpenWorkspace 整合方案

### 17.1 选型结论与依据

采用“共享 Python 核心、多种入口”的结构：

| 部分 | 选型 | 职责 |
|---|---|---|
| 业务核心 | Python `trader.application` 与各业务域 | 行情、指标、特征、分析、回测、训练及业务编排 |
| 对外接口 | 后续按需增加 FastAPI | 将完整应用用例暴露为 HTTP API |
| Web 入口 | 保留 OpenWorkspace 的 Astro；复杂交互模块优先 Vue 3 + TypeScript | 走势、筛选、分析详情、参数配置与任务状态 |
| 图表 | 现有 ECharts 继续使用；专业 K 线交互优先评估 Lightweight Charts | 展示后端提供的数值序列和信号标记 |
| 本地工具 | PySide6 | `stock_widget` 等浮窗、托盘和本机快捷操作 |
| 自动化入口 | Python CLI | 数据维护、批量分析与任务执行 |

Python 的优势主要来自 NumPy 等数值计算库、统计与机器学习生态，以及项目已有的
算法和回归基线。高性能数值运算应利用向量化及底层编译实现，不能把 Python 语言
本身视为性能保证。没有必要仅为与 Web 统一语言而迁移应用层或计算核心。

Vue 与 PySide6 分别服务网页和桌面需求，共享业务实现与数据契约。当前不同时引入
Vue 和 React；若以后存在明确的 React 团队或组件资产，再单独评估选型变更。

### 17.2 现状与仓库职责

方案编写时的工作区已有以下接入路径，尚未部署本节描述的目标架构：

- `OpenWorkspace/` 使用 Astro 生成静态页面，可选 Node API 宿主加载工作区服务；
- `Website/modules/tools/content/stock_analysis.html` 使用 HTML + ECharts 展示分析；
- `Website/services/stock-analysis/index.mjs` 注册 `/api/stock/list`、`trend`、`report`，
  通过子进程执行 `python -m tools.stock_advisor.web_api` 并读取 JSON；
- `Trader/tools/stock_widget` 使用 PySide6，当前直接通过行情工厂获取报价。

这些是当前工作区的仓库名称与路径示例，部署时通过配置定位，不硬编码开发机路径。

职责划分：

- **Trader** 拥有行情、业务算法、应用服务、数据库、模型产物及 Python 入口；
- **Website** 拥有股票页面、实例级接口适配与部署配置；
- **OpenWorkspace** 拥有通用布局、导航、内容加载和 API 宿主，不承载 Trader 算法。

Trader 数据库与模型继续按第 6 节管理，不复制到网页静态产物中，也不由 Node 服务
直接读写业务表。Node 适配层处理参数、站点认证接入及响应转换，不重新实现指标或
拆分编排底层计算。公开站点接入写操作时必须具备服务端认证，隐藏导航不构成权限控制。

### 17.3 目标调用关系

```text
OpenWorkspace 中的股票页面
  → Website 服务适配层
  → Trader HTTP API（FastAPI，后续增加）
  → trader.application
  → 行情 / 量化 / 财报领域

PySide6 小工具 / Python CLI
  → trader.application（本地直接调用）
  或 → Trader HTTP API（需要共享常驻服务时）
```

HTTP API 暂定放在后续新增的 `src/trader/interfaces/http/`，与 `tools` 同属入口层。
FastAPI、PySide6 等依赖按入口拆成可选依赖组；安装计算核心不应强制安装桌面或 Web
服务依赖。该目录是后续扩展，不要求在第 3 节的重构目标目录中提前创建空实现。

对外暴露完整用例，例如“一次请求返回某标的的分析结果”；读取行情、计算特征、
汇总信号等步骤在 Python 内完成。核心包不依赖 Website 或 OpenWorkspace。

### 17.4 Web 页面与图表演进

1. 简单走势与分析继续使用现有 HTML + ECharts。
2. 出现多图联动、复杂筛选、参数面板等需求时，在 Website 股票模块引入 Vue 3。
3. 优先把 Vue 构建为 JS/CSS 资源，由模块 HTML 加载并沿用现有 iframe 展示机制；
   构建时处理资源路径，验证沙箱、CSP 和 API 访问兼容性。
4. 若需要更紧密的页面整合，再为 OpenWorkspace 增加通用 Astro/Vue 构建接入；
   当前内容扫描机制不会自动编译放入工作区的 `.vue` 文件。

图表与 UI 框架分开选型。Lightweight Charts 用于 K 线、成交量、指标副图和信号
标记；ECharts 用于财务趋势、收益分布等统计图。已有图表满足需求时无需替换。
复杂画线、历史回放及联动需要单独验证或开发，不能把图表库视为完整交易终端。
采用图表库时按其许可证和署名要求集成。

指标与信号的正式计算保留在 Python，前端负责渲染、视图范围和交互状态。
Web 首版范围建议为股票列表、走势图与信号、分析详情、任务进度四部分。

### 17.5 本地小工具的两种运行方式

| 方式 | 使用条件 | 运行边界 |
|---|---|---|
| 直接调用 Python 应用服务 | 独立浮窗、简单本机工具 | 无需启动网站或 HTTP 服务；各进程拥有自己的连接与缓存 |
| 调用 Trader 常驻 API | 多工具共享订阅、缓存、模型或任务 | 由服务集中管理资源；客户端处理超时、不可用和恢复 |

`stock_widget` 默认先采用直接调用方式。UI 保留定时器、线程、窗口与渲染，把 Provider
选择和获取流程交给应用服务；网络请求和耗时计算不阻塞 UI 线程。

共享 Python 代码不意味着共享进程内缓存或行情连接。出现重复订阅或需要集中管理
任务时，再启用常驻服务模式。服务不可用时明确展示状态与数据时间，不静默启动另一套
行情连接或写入任务。独立模式下，小工具不依赖 OpenWorkspace 的运行状态。

### 17.6 应用用例与数据契约

先从现有 Web 和桌面入口提取证券列表、历史走势、报告和最新报价用例；后续按 UI
需求补充指标序列、信号标记、回测结果和任务查询接口。

- 历史查询与最新报价使用独立用例。离线分析不隐式回源，在线报价明确 Provider、
  行情时间和获取时间，不把日 K 的最后收盘值默认解释为实时价格；
- 图表 DTO 明确证券 ID、周期、交易日期或时间戳、适用时区、复权方式、数据来源、
  数据截至时间和更新时间；日 K 使用交易日期，盘中数据使用带明确时区语义的时间戳；
- K 线、指标和信号按同一时间与复权口径对齐，缺失值不伪装为零；
- PIT 分析显式传入截止时间，响应保留该时间，避免混入之后才能获知的数据；
- DTO 为结构化数据，UI 不解析 Markdown 来恢复业务结果；Markdown 是单独的渲染输出；
- JSON 适配明确日期、枚举和数值的序列化规则，不能输出非法 JSON 的 NaN/Infinity；
- 新 HTTP API 使用版本化路径（例如 `/api/v1/...`），稳定错误语义；Website 旧路由
  可在适配层保持兼容，内部数据库路径不作为对外业务参数。

成分股查询、刷新、快照与任务接口作为首批候选业务 API，具体契约和数据源选择见第 19 节。

本机与远端若运行独立 Trader 实例，复用的是代码与契约，不会自动共享数据。需要一致
数据时应连接同一服务，或另行设计数据同步，不能依靠多台机器共享 SQLite 文件实现。

### 17.7 耗时任务与通信

同步历史行情、批量回测、模型训练等操作采用“提交任务 → 返回任务 ID → 查询状态与
结果”的接口。任务记录包含状态、进度、错误和结果引用；重复提交策略及可否取消应
明确，进程重启后应能识别中断任务并按任务能力恢复或重试。

起步采用单机执行进程与 SQLite 任务记录。CPU 密集计算在独立执行进程中运行，不放在
HTTP 请求处理或 UI 线程里；单纯使用 FastAPI 的后台回调不能替代持久化任务机制。
写入使用短事务并控制并发，不因 UI 接入立即引入分布式队列或更换数据库。

日 K 查询先使用 HTTP，任务进度先轮询。需要服务端单向推送时评估 SSE，需要实时
订阅等双向通信时再评估 WebSocket；通信协议不改变数据源本身的实时能力。

### 17.8 实施顺序与验收

| 时机 | 工作 | 验收重点 |
|---|---|---|
| 本轮重构阶段 5 | 提取现有入口的应用服务，保留 Python 子进程桥接和独立浮窗 | 同一用例、同一数据与配置下结果一致；现有命令和 JSON 契约兼容 |
| 后续 Web 交互扩展 | 按需引入 Vue 和图表组件 | 图表时间与指标对齐；空数据、失败与过期数据可辨识；原有页面接入有效 |
| 出现频繁查询或资源共享需求 | 增加常驻 FastAPI，由 Website 适配层切换调用 | 新旧通道结果一致；减少重复初始化；超时、错误和资源关闭行为明确 |
| 增加耗时操作或多客户端 | 持久化任务执行与状态查询，按需提供桌面 API 模式 | 重复提交、重启与多客户端访问符合既定语义，UI 不被阻塞 |

新增通道先做相同输入的结构化结果对照，再切换调用方；确认迁移完成后才移除旧入口。
本轮重构的完成定义仍以第 15 节为准，后续 UI 和服务部署按本节独立验收。
在引入新框架前，优先按第 18 节处理查询副作用与错误传播，复现并修复页面请求竞争，
验证历史产物的可用时间边界。具体优先级、负责仓库与阶段映射见第 18.9 节。

实盘下单、撤单、订单状态和成交回报属于后续交易域，持仓属于组合域，通过应用服务
接入。UI 只提交操作意图并展示后端确认状态，不能用新增按钮代替交易业务实现。

### 17.9 技术参考

- [Astro 前端框架集成](https://docs.astro.build/en/guides/framework-components/)
- [FastAPI 功能与 OpenAPI 支持](https://fastapi.tiangolo.com/features/)
- [FastAPI 后台任务及重计算边界](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Lightweight Charts 文档](https://tradingview.github.io/lightweight-charts/)
- [Qt WebEngine：需要在桌面嵌入 Web 图表时使用](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html)
- [NumPy 的数组与向量化计算](https://numpy.org/doc/stable/user/whatisnumpy.html)

## 18. 正确性、接口边界与运行能力的进一步重构

本节基于当前代码的静态检查，记录八个改进方向及其验收依据，不表示已经完成实现或
运行验证。代码路径描述的是检查时状态；迁移后同步更新。第 17 节负责技术选型与接入
结构，本节补充为何重构、需要改变的行为及如何确认改进有效。

### 18.1 分离查询与数据准备

**现状证据：** Website 服务注释声明只读且不重算因子，但报告入口调用
[`_load_or_build()`](../tools/stock_advisor/stock_advisor.py)，在特征最新日期落后于
行情时调用 `materialize_symbol()`；后者会保存特征。因此当前报告查询存在隐式写入路径。

目标用例分工：

| 用例 | 行为 |
|---|---|
| 查询历史走势、读取已生成报告 | 读取准备好的数据或产物，不隐式启动物化；返回数据可用性与新鲜度 |
| 准备分析数据 | 显式补齐或重建特征，记录执行结果；耗时情况下采用第 17.7 节任务机制 |
| 在线预测（见第 20 节） | 显式允许 Provider 补拉并写行情缓存，在内存计算预测特征；不修改研究主库 |
| 生成复杂报告 | 显式执行分析并生成产物，之后可重复读取；不由查询接口隐藏触发 |

CLI 若需保留“准备后分析”的便利，可在应用层显式组合用例。旧 Web 行为通过兼容迁移
调整，前端能够展示“需要准备数据”，而不是自动把用户查询转成写入操作。

验收：以特征缺失和落后的临时数据库验证，纯查询不修改业务表、不调用物化服务；
显式准备完成后可以查询，重复准备符合既定幂等规则，失败不会留下被误认为有效的半成品。

### 18.2 数据、特征与模型产物版本及 PIT 边界

**现状证据：** [`web_api.py`](../tools/stock_advisor/web_api.py) 的历史走势按日期截断
行情，但每次请求加载同一份回测统计产物。
[`BacktestArtifact`](../quantitative/backtesting/models.py) 已有 `model_version`、
`generated_at`、`data_cutoff`，而当前 Repository 的 `load()` 不按分析日期选择产物。

**待验证风险：** 若该产物利用分析时点之后的数据生成，历史结果可能带入未来信息。
需要结合实际产物的训练范围和使用链路复现，不能仅凭静态检查断言所有结果都有泄漏。

改进要求：

- 明确区分“用当前模型解释历史”与“还原当时可获得的判断”，在结果元数据中记录模式；
- 沿用已有版本字段，增加稳定产物 ID、实际可用时间及数据/特征版本关联；
- 严格 PIT 模式按分析时间选择当时可用且训练数据截止符合要求的产物；
  训练标签所依赖的未来观察窗口也必须落在允许范围内；
- 缺少合格历史产物时返回不可用状态，不自动使用最新产物冒充当时结果；
- 分析结果记录证券、复权口径、数据版本、特征定义版本、产物 ID、截止时间和参数，
  相同版本输入可重现结果；历史产物保留，不覆盖后再声称能够复现。

验收：构造截止时间前后各一份产物，严格 PIT 查询只能选择前者；新增未来产物不改变
已固定版本的历史结果。历史解释模式明确标注使用当前模型；缺少产物时有确定错误语义。

### 18.3 业务错误、部分结果与异常降级

**现状证据：** Python 将业务失败写入 stdout JSON 并返回非零退出码，但
[`runWebApi()`](../../Website/services/stock-analysis/index.mjs) 遇非零退出码先抛错，
没有解析该 JSON。宿主随后返回通用 500，丢失“未登记股票”“无行情”等业务原因。
走势计算与报告部分分析还存在宽泛的 `except Exception`，将异常转换为中性值、
基准概率或 `None`，可能混淆数据不足和程序错误。

改进要求：

- 应用层统一错误类型或错误码，区分输入无效、无数据、数据未准备、Provider 失败与内部异常；
- 整体结果与各分析分项记录 `complete`、`partial`、`unavailable` 等可用性状态；
- 预期的数据不足允许显式降级，缺失概率使用空值及原因，不伪装成真实的 50% 判断；
- 意外异常保留诊断日志；可继续的独立分项标为部分结果，核心失败不能宣称完整成功；
- Node 解析符合契约的业务失败结果，再映射状态码；进程启动失败、非法输出、连接失败
  与超时使用不同传输错误；对外响应不泄露堆栈或内部路径；
- 请求 ID 从 Website 传到 Trader，关联日志、耗时和后续任务 ID。

验收：业务无数据不会退化为无法解释的通用 500；模拟分析分项异常后，页面能区分部分
结果和真实中性；意外异常可通过请求 ID 定位，合法数值与原公式保持一致。

### 18.4 稳定 API 契约与参数边界

**现状证据：** 股票服务接受 `name_key`/`stock` 别名，使用 `parseInt()` 宽松解析
`days`，并把请求中的 `db` 转发为 Python 数据库路径。页面还兼容多套概率字段并自行
推导替代值，接口语义分散在多个位置。

以第 17.6 节 DTO 为基础：

- 公共接口使用稳定证券 ID，旧名称与参数别名集中放在兼容适配器；
- 严格校验日期、查询区间、周期和长度上限，区分缺省值与非法值；
- 数据库路径来自服务配置；确需多数据集时使用受控数据集 ID，不能由公网请求指定路径；
- 契约明确数值单位、空值、可用性、新鲜度、时间与版本元数据；逐步移除前端猜测字段的逻辑；
- FastAPI 接入后从 OpenAPI 生成 TypeScript 客户端，并在构建中检查契约变化；
  HTTP schema 与应用 DTO 之间由适配层转换，不让核心依赖 Web 框架；
- 对有意改变的错误结构、字段与行为记录版本或兼容窗口，而不是以新接口覆盖旧接口。

验收：非法数字、越界区间和无效日期返回约定错误；公共接口不能选择任意数据库路径；
旧别名仍能在约定窗口内正确映射；Python 与 TypeScript 使用同一份有效/无效响应样例验证。

### 18.5 前端状态、请求竞争与渲染分离

**现状证据：** [`stock_analysis.html`](../../Website/modules/tools/content/stock_analysis.html)
使用全局 `currentStock`、`currentSeries`，请求返回后没有检查是否仍对应当前选择。
报告下载结束时也读取当前股票变量，因此请求乱序时可能覆盖新图表或产生错误文件名。
这是代码路径支持的风险，具体交互表现需用可控响应顺序复现。

先在现有 HTML 页面提取 API 客户端、页面状态、图表渲染和报告下载模块，无需等待 Vue：

- 每次请求固定证券、日期与请求序号，仅接受仍属于当前选择的响应；
- 可取消旧请求，但同时保留响应归属检查；前端取消不等于后台任务已经取消；
- 切换、失败和空数据时明确清理旧内容，或保留并标注所属证券及过期状态；
- 报告内容、预览标题和下载文件名绑定请求快照，不读取已变化的全局选择；
- 无效数值显示缺口或原因，图表不把空值转换成零或中性；视图卸载时释放图表和监听器。

验收：让 A 请求晚于 B 返回，选择 B 后仍只显示 B；下载 A 报告期间切到 B，文件内容与
名称仍对应 A，B 的预览不被旧响应覆盖；加载失败和空数据不会被当作新选择的有效结果。

### 18.6 TraderClient、资源生命周期与调用限制

**现状证据：** 现有子进程桥接未显式设置调用超时、stdout/stderr 大小上限和并发上限。
OpenWorkspace service 目前只约定 `createRoutes()`，未提供统一的服务资源释放约定。

在 Website 的股票适配代码中先抽取小型 `TraderClient`，以列表、走势、报告等完整
用例为接口。子进程实现与后续 HTTP 实现遵循同一份结果和错误契约；仅在多个服务实际
复用时，再把通用通信能力提取到 OpenWorkspace，避免预先建设通用代理框架。

- 子进程调用限制并发和输出量，超时需终止并回收子进程，不只是停止等待 Promise；
- HTTP 实现配置地址、超时和错误映射，不能把重试直接应用到可能产生副作用的操作；
- Python 在启动或明确的延迟加载阶段初始化模型与 Provider，关闭时显式释放；
- 数据库连接遵守线程/进程与事务边界，不把一个 Repository 无限制共享给所有请求；
- 明确每个 worker 的缓存、模型副本和订阅范围；需要唯一订阅或任务执行者时单独管理；
- 实际出现服务级长期资源时，为 OpenWorkspace 增加初始化、关闭及就绪检查约定，
  保持已有 `createRoutes()` 服务兼容。

验收：使用假子进程/假 HTTP 服务验证超时、超量输出、进程退出和并发限制；请求结束或
服务关闭后资源正确回收。切换传输实现不改变正常业务结果和约定的业务错误。

### 18.7 按版本失效的计算缓存与重复任务合并

**现状证据：** 走势请求会读取历史数据、重新计算特征并逐日分析；`_load_or_build()`
主要通过行情与特征的最新日期是否相等判断是否需要重建。相同日期不能识别历史行情
修订或特征定义变化。具体性能瓶颈尚未测量，不预设缓存一定是首要优化。

先记录数据读取、特征计算、逐日分析与报告生成的耗时和内存，再决定缓存位置：

- 新鲜度判断加入输入数据修订信息与特征定义版本，不能只依赖最新交易日；
- 缓存键包含证券、时间范围、复权方式、数据版本、特征版本、模型/统计产物版本与参数；
- 数据或算法变化使受影响结果失效，过期结果若继续展示必须带明确标识；
- 对相同有效输入的分析任务复用已有执行或完成结果；强制重算、失败重试与取消规则独立定义；
- 缓存与任务合并先在单机实现，只有测量和运行规模证明有必要时才增加 Redis 或分布式队列。

验收：历史数据修订但最新日期未变时仍触发必要重算；特征或模型版本切换不命中旧缓存；
相同输入的并发请求不会重复启动约定可合并的任务。用同一数据集比较优化前后的结果与耗时。

### 18.8 跨项目契约测试与运行可观测性

现有测试包含 OpenWorkspace API 宿主测试；本次定向检索未发现直接覆盖 Trader Web
桥接与 Website 股票服务完整链路的测试，这不等同于已证明所有外部测试均不存在。
现有 `/health` 只确认 Node 宿主响应，不证明 Trader 可用。

补充与真实边界对应的验证：

| 负责仓库 | 验证重点 |
|---|---|
| Trader | 纯查询副作用、PIT 产物选择、缺失与异常分类、固定版本结果复现 |
| Website | Python 业务失败传播、参数校验、假下游超时、页面乱序响应和下载归属 |
| OpenWorkspace | 服务注册兼容、通用错误边界，以及实际引入后的生命周期和就绪检查 |
| 跨项目联调 | CLI、子进程与 HTTP 对相同输入的结果一致；正常、部分结果与失败样例兼容 |

保留轻量存活检查，另设按依赖区分的就绪状态；Trader 失败不应使无关静态页面或其他
服务一律不可用。就绪检查使用有时限的轻量探测，不在探测中启动训练或重建数据。
日志记录请求/任务 ID、调用阶段、耗时、错误码和数据/产物版本，不记录密钥或完整敏感载荷。

验收：可区分 Node 未启动、Trader 不可达、必要资源缺失与业务无数据；一个请求的
跨进程失败可关联定位。联调使用临时数据库和受控下游，避免依赖实时行情与开发机路径。

### 18.9 优先级、阶段映射与变更规则

| 优先级 | 方向 | 负责范围 | 与现有计划的关系 |
|---|---|---|---|
| 第一批：正确性 | 查询副作用、PIT 产物边界、错误降级、页面请求竞争 | Trader + Website | 阶段 0 建样例并验证；已确认缺陷独立修复，先于相关新接口或 UI 发布 |
| 第二批：接口维护 | 查询/准备用例、稳定契约、TraderClient、跨项目测试 | Trader + Website | 结合阶段 3/5 提取边界；行为调整与结构迁移分开交付 |
| 第三批：常驻运行与性能 | FastAPI、资源生命周期、持久化任务、版本缓存与就绪检查 | Trader + Website；通用能力按需进入 OpenWorkspace | 按第 17 节需求触发，缓存以前置测量为依据 |
| 第四批：界面扩展 | Vue 工作台、专业 K 线交互、多工具共享服务 | Website + Trader；必要时扩展 OpenWorkspace 构建 | 使用已稳定的用例与契约，不重复实现业务算法 |

执行规则：

1. 本节全部为计划项；纳入文档不代表已经修复，也不代表立即实施跨仓库代码修改。
2. 先复现、分类和确认目标行为，再独立修复；PIT 等待验证风险不得直接改写历史结果。
3. 结构迁移继续保持算法与统计口径；有意的结果变化记录旧值、新值、原因和回归用例。
4. 有效调用的兼容与缺陷修复按第 10 节协调；前后端契约变化需关联各仓库的迁移记录。
5. 本轮只验收实际纳入的方向；常驻部署、Vue、模型历史重建与分布式能力不自动成为
   第 14 节 Go/No-Go 的新增前置条件。影响本轮迁移正确性的未决问题应记录并先解决。

补充参考：[FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)、
[从 OpenAPI 生成客户端](https://fastapi.tiangolo.com/advanced/generate-clients/)。

## 19. 指数成分股 API（下次重构待实现）

> 状态：已纳入后续方案，尚未实现。当前只更新文档；不部署服务、不建立生产刷新任务、
> 不把实测名单写入业务数据库。下次重构先完成应用用例和契约，再随第 17 节服务化接入。

### 19.1 目标与调用边界

将沪深 300、恒生指数、标普 500 的成分获取与维护能力提供给 OpenWorkspace、CLI 和
本地小工具。对外分为“查询已有成分”和“显式刷新成分”两类操作：

```text
Website 指数页面 / TraderClient
  → OpenWorkspace service 适配层
  → Trader FastAPI
      GET  → QueryUniversesService → UniverseRepository
      POST → 持久化任务 → RefreshUniversesService → ConstituentProvider
                          → 校验、快照与成员事务 → UniverseRepository

CLI / 本地 Python 工具 → 同一组 application 用例
```

GET 不回源、不物化、不隐式写入；第一次尚无快照时返回明确的“数据未准备”错误，
由有权限的用户或调度器提交刷新。Provider、SQL、差异计算与完整性校验留在 Trader。
外部下载地址、数据库路径与鉴权配置由服务端控制，不接受客户端指定任意 URL 或文件路径。

### 19.2 候选 HTTP 契约

以下路由为设计草案，待实现时通过 OpenAPI 固化；指数 ID 使用 `CSI300`、`HSI`、`SP500`。

| 方法 | 路径 | 行为 |
|---|---|---|
| GET | `/api/v1/universes` | 列出支持的指数、来源能力、当前快照和刷新状态 |
| GET | `/api/v1/universes/{id}/constituents` | 查询当前活动快照；可用 `snapshot_id` 查询指定快照，或用 `as_of` 查询有依据的历史成员 |
| GET | `/api/v1/universes/{id}/snapshots` | 分页查询成功快照及其来源、日期、成员数和校验元数据 |
| POST | `/api/v1/universes/{id}/refresh` | 校验权限与参数后持久化刷新任务，返回 HTTP 202、`task_id` 与状态查询地址 |
| GET | `/api/v1/tasks/{task_id}` | 查询排队、运行、成功或失败状态，以及快照、增删数量和错误信息 |

刷新接口仅获取当前名单，不接受任意历史日期冒充 Provider 的历史查询能力。历史调整表
导入属于独立用例，在有效期语义和完整性验证后再开放；首次不增加批量刷新或任意数据源选择参数。

刷新请求支持调用方提供幂等键。同一调用方、指数和参数的相同幂等键返回同一任务；
同键不同参数返回冲突；同一指数已有刷新在运行时复用任务或返回约定冲突，避免重复抓取与切换。
任务 ID 与第 6 节的 `universe_refresh_run.run_id` 建立明确关联，不创建两套互相矛盾的状态。

候选错误语义：未知指数/快照为 404，参数无效为 422，未准备快照或不支持的历史范围为
409；提交任务时执行器不可用为 503。任务受理后的源端超时或校验失败记录在任务中，
不把 HTTP 202 解释为刷新已经成功。鉴权失败使用 401/403，并沿用第 18.3 节统一错误结构。

### 19.3 返回数据与时间语义

成分结果至少包含：

- 指数 ID、查询模式、快照 ID、成员总数和分页信息；
- 来源标识、源端数据日期 `source_as_of`、下载时间 `fetched_at`、最近成功刷新时间，
  以及过期/来源时间未知等质量状态；
- 每项的证券 ID、代码、名称、市场/交易所与 Provider 代码映射；权重仅在源端真实提供时返回；
- 快照校验摘要与内容校验和；第三方文件可补充提交 SHA，便于追踪实际采用的内容。

`snapshot_id` 与 `as_of` 查询参数互斥。分页时首响应固定快照 ID，后续页沿用该 ID，
避免刷新切换后把两份名单拼在一起；如提供分页历史查询，同样固定其底层数据版本。

源端文件日期、文件提交时间、抓取时间和成员真实生效日期不是同一概念。已知真实生效日
时记录其依据；只有当前名单时从首次观测日起记录成员，并标明 `observed` 时间依据。
`as_of` 不支持的历史范围返回明确错误，不能回退为当前名单。第 6 节的快照与成员模型在
实现时需承载这一时间依据，不能把首次抓取时间伪造为历史正式生效时间。

### 19.4 数据源实测依据与初始选择

2026-09-12 已在当前 Windows/Python 环境执行真实 HTTP 下载和解析，结果如下。
这是一次技术可获取性验证，不是长期可用性保证，也未完成官方数据再分发许可确认。

| 指数/来源 | 实测结果 | 接入决定 |
|---|---|---|
| 沪深 300：中证官方 Excel | 300 个唯一代码，表内日期 2026-09-11，包含名称与交易所；首次超时，重试成功 | 当前名单优先主源，设置有上限的重试 |
| 沪深 300：新浪 `hs300` | 四页合计 300 只，但与官方仅 239 只相同，双方各有 61 只独有证券 | 只用于差异诊断，原因未核实前不作为自动替补 |
| 恒生指数：官方 JSON | 95 个唯一代码，源端时间 2026-09-11 16:09:18；主指数数量、中英文代码集合与子指数并集一致 | 当前名单优先主源，只读取主指数成员数组 |
| 标普 500：datasets CSV | 503 个证券代码、500 个不同 CIK；CSV 最近提交 2026-09-05，未获得官方完整名单独立核对 | 研究阶段候选源，显式标记第三方来源与时间未知情况 |
| 标普官网 / Wikipedia 网页 | 本机直接请求均返回 403 | 本次未验证可直接接入，不把网页可浏览等同脚本可抓取 |
| 恒生官方历史 XLSX | 解析 114 条调整记录，日期范围 2008-10-08 至 2026-09-07 | 作为独立历史导入候选，尚未验证完整历史重建结果 |

来源地址：

- [沪深 300 官方成分 Excel](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/autofile/cons/000300cons.xls)
- [AKShare 中证/新浪成分抓取实现参考](https://github.com/akfamily/akshare/blob/main/akshare/index/index_cons.py)
- [恒生官方中文 JSON](https://www.hsi.com.hk/data/chi/rt/index-series/hsi/constituents.do)
- [恒生官方英文 JSON](https://www.hsi.com.hk/data/eng/rt/index-series/hsi/constituents.do)
- [标普 500 CSV](https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv)
- [标普 CSV 来源及许可说明](https://github.com/datasets/s-and-p-500-companies)
- [本次观察的 CSV 提交](https://github.com/datasets/s-and-p-500-companies/commit/3b2bb60e6269439cd75541eded6281c48e7681d1)
- [恒生历史成分调整 XLSX](https://www.hsi.com.hk/static/uploads/contents/en/indexes/hisConstituent/hsi/hist_hsi.xlsx)

中证旧的 `www.csindex.com.cn/csindex-home/uploads/...` 下载路径本次返回 404，采用上述
`oss-ch.csindex.com.cn` 路径。AKShare 是接口封装参考，本次直接下载源端数据，未执行
AKShare 库调用测试。标普 CSV 项目说明来源于 Wikipedia；提交日期不等于成分生效日。

95 和 503 是本次观察值，不作为永久硬编码数量。正式实现结合源端声明数量、配置的合理
范围与历史差异校验；S&P 500 按证券保留多个股票类别，不按 CIK 去重为 500 条。

### 19.5 刷新、快照切换与行情回填

刷新沿用第 5.1、6.2.6 节的事务模型：抓取全部数据 → 规范化 → 验证 → 保存完整快照
并切换活动版本。数量、唯一性、必填字段、指数身份、源端日期及异常变更比例都必须校验。
先完成验证，再允许任何成员退出或新快照激活。

- 任一分页失败、空名单、日期异常或未解释的大幅变更均失败，保留上次成功快照；
- 源端未给日期时保留未知值，并按该来源的明确新鲜度策略处理，不能用抓取日期填充；
- 新源首次激活或主备源切换需独立对照；不能因为备用源也返回 300 只就认定等价；
- 上游结构变化、超时、403/404 等保留可诊断错误，重试有上限，不无限循环；
- 股票池退出只结束成员关系并停止相应日常更新，不删除证券、历史成员或行情；
- 股票池成功刷新与十年行情回填是不同结果。按第 5.2 节策略为新增成分建立关联回填任务，
  返回关联任务 ID；回填失败可独立重试，不回滚已验证的成分快照；
- 快照提交与回填调度之间的失败需要可恢复：记录待调度状态或扫描成功刷新中的新增成员补排，
  保证不漏回填且不会重复创建等价任务。

### 19.6 OpenWorkspace 接入与下次重构验收

Website 可在现有 `stock-analysis` service 中增加成分列表与刷新适配，需求独立后再拆分
服务。浏览器继续走同源 API，Node 调用 TraderClient；刷新按钮需要服务端权限检查。
如扩展现有 OpenWorkspace 宿主以接收 POST JSON，应补充请求体大小限制与解析错误处理。
刷新后页面轮询任务，成功后重新获取指定快照；刷新失败时显示错误和仍在使用的旧快照时间。

下次实施待办：

- [ ] 建立三个 `ConstituentProvider`，保留原始响应校验和、解析器版本及数据时间；
- [ ] 完成 `QueryUniversesService` 与 `RefreshUniversesService`，CLI/API 共享结果；
- [ ] 实现候选 HTTP 路由、持久化任务、幂等与写操作鉴权；
- [ ] 完成主源选择、数据使用范围确认和快照质量策略；
- [ ] 完成 Website 页面/服务接入与关联回填任务状态展示；
- [ ] 使用固定样例与假 Provider 验证正常刷新、源端失败、重复代码、分页缺失、异常差异及旧快照保留；
- [ ] 验证重复提交、并发刷新、进程重启和回填调度失败后的恢复行为；
- [ ] 验证 GET 不回源、不写库，分页固定版本，未知历史范围不返回当前名单；
- [ ] 实施时重新运行在线冒烟检查，避免把本次能下载视为永久可用。

本节列为下次重构及服务化的候选交付，不改变当前 Go/No-Go 状态；一次下载成功不自动
勾选第 14 节“数据源及使用许可已验证”。当前不执行上述待办。

## 20. 研究主库与行情缓存库（下次重构待实现）

> 状态：已确定采用独立 SQLite 行情缓存的方向，尚未实现。本次仅更新方案，不创建、
> 迁移或修改数据库，不启动定时任务。暂不考虑按市场、年份或股票分文件存储研究数据，
> 也不引入远端快照/增量文件同步。

### 20.1 使用场景与存储边界

- 个人工具、单机使用，按串行执行设计，不把多用户并发作为本方案需求，不引入 Redis、
  分布式队列或额外数据库服务；第 17/18 节的服务扩展能力仍按实际需求触发。
- 研究主库主要供回测、机器学习使用，每一至两周或每月正式更新一次，可手动更新。
- 预测需要近期数据时调用外部行情 Provider 的 API 补齐，FastAPI 只作为可选入口。
- 股票池成员与历史行情是不同数据：本节缓存行情，不缓存或切换指数成分快照；成员
  刷新继续遵循第 19 节，不因一次预测请求改变股票池。

| 存储 | 目标路径 | 内容与写入边界 |
|---|---|---|
| 研究主库 | `var/database/stock_data.db` | 证券、股票池成员历史、正式历史行情、物化特征等；通过显式研究数据更新用例写入 |
| 行情缓存库 | `var/cache/market_cache.db` | 预测按需补拉的日 K 线及来源、抓取时间、数据口径和质量信息；重启后可继续复用 |

现有主库在目录迁移前保持原路径，通过配置注入主库与缓存路径，不要求先搬迁数据才能
实现缓存。两个文件都属于运行数据，不提交 Git；本次只记录忽略与迁移要求，不修改
`.gitignore`、文件跟踪或仓库历史。独立缓存的目的是复用补拉数据、隔离研究更新，不能
依靠新增缓存库解决已经入库的大型 Git 文件历史问题。

### 20.2 预测读取与补拉流程

```text
ForecastStockService（显式预测用例）
  → 确定证券、预测截止时间、复权口径、模型版本与所需历史窗口
  → 读取研究主库窗口内的行情
  → 读取行情缓存，按质量与来源规则合并重叠记录
  → 按交易日历检查尾部及内部缺口
  → QuoteProvider 仅补拉缺少或需要重新校验的区间
  → 校验成功后写入行情缓存，形成完整预测输入
  → 内存计算指标/特征 → 使用指定已训练模型预测
  → 返回结果、行情截止时间、数据来源及完整性状态
```

预测窗口包含指标与模型所需的预热历史，不能只按页面显示天数取数。预测不会自动训练
模型、物化主库特征或把缓存合入主库；缓存首期只保存行情和必要元数据，不维护第二套
持久化指标表。回测与训练默认只读正式研究数据，不自动混入预测缓存或在线补拉数据。

纯历史查询仍遵循第 18.1 节的只读约定；需要回源并写缓存时调用显式预测/数据准备
用例，CLI、桌面工具和后续 HTTP 入口共用该用例。结果记录研究数据版本、所用缓存
数据修订标识及特征/模型版本，避免把不同输入的预测误认为同一版本。

### 20.3 缓存一致性与失败语义

- 缓存采用第 6.2.4 节的规范化行情口径，以证券、交易日、复权方式唯一标识记录，
  另记来源、抓取时间和修订/复权依据。证券身份复用主库的映射，由应用层验证关联，
  不假定 SQLite 能用跨文件外键约束缓存。
- 重叠记录按明确的来源优先级、质量和修订依据选择，不能简单按“缓存优先”或抓取
  时间最新覆盖。同名复权方式也可能有不同基准；发生除权除息或历史修订时，需重新
  校验并按 Provider 能力补拉受影响历史，不能把不同复权基准的片段直接拼接。
- 日线预测默认使用已收盘且有效的日 K 线。盘中报价继续服务于即时展示，不混入正式
  收盘日线。交易日、时区、停牌和上市日期用于判断缺口，不把所有自然日都当成缺失。
- API 失败、数据过期或窗口不完整时，返回明确失败或带截止时间的可用性状态；未满足
  模型输入要求时不输出正常预测，不能将旧数据或默认概率冒充最新成功结果。
- 缓存设置可配置容量/保留期，默认优先清理已合入的数据。尚未合入的有效记录不因一次
  更新失败自动删除；需要额外淘汰时，明确其可回源重建和可能增加 API 请求的代价。

### 20.4 周期合入研究主库

复用 `update_market_data` 与 `materialize_features`，由应用层串行编排正式更新：

1. 固定本次股票池快照和各市场目标截止日，检查全池及手工固定标的的实际行情覆盖；
   缓存只包含预测用过的证券，不能把“缓存全部导入”当作“股票池更新完成”。
2. 优先读取符合口径的缓存，再通过 Provider 补齐剩余缺口，并按策略检查历史修订；
   新增成分的十年回填继续使用第 5.2 节规则。
3. 校验后按证券/批次事务幂等写入主库，记录成功范围、失败项及数据修订信息。单只
   失败不回滚其他证券，也不将全池任务标记为完整成功。
4. 重算受影响区间及其后续依赖的特征；递推指标按算法要求扩展范围。若行情已提交而
   特征计算失败，保留“特征待更新”状态供重试，不能将旧特征宣称为新数据版本。
5. 主库确认提交并记录合入结果后，再清理已归档的对应缓存记录。主库提交与缓存清理
   不假定存在跨文件原子事务；中断后允许重复合入，依靠唯一键、修订信息和进度恢复。
6. 记录本次研究数据版本、各证券覆盖范围及特征状态。需要复现实验时保留对应输入
   快照或可恢复备份，仅记录版本号不足以重建已被覆盖的历史值。

周期任务先提供可手动执行的命令，再由本机任务计划按一至两周或每月触发。电脑关机
错过调度时，下次执行按实际缺口补齐；不要求全天运行，也不依赖部署 FastAPI。

### 20.5 职责与下次重构验收

缓存 Repository 归 `market_data.quotes`，仅负责缓存读写；Provider 负责下载与规范化；
主库/缓存/API 组合、更新与清理顺序由 `application` 编排。第 18.7 节的计算结果缓存是
独立优化项，不与本节持久化行情缓存混为一套实现。

- [ ] 增加可配置缓存路径与 Repository；既有主库可继续使用，首次按需初始化缓存。
- [ ] 实现预测窗口合并、缺口补拉与内存特征计算；重复有效请求复用缓存，重启后仍可命中。
- [ ] 用临时数据库验证预测不写研究主库，回测/训练不自动读取缓存，纯历史查询不回源。
- [ ] 用假 Provider 验证内部缺口、预热窗口、停牌、未收盘日线、API 失败及复权/来源冲突。
- [ ] 验证全池周期更新、缓存未覆盖证券的补拉，以及修订行情触发受影响特征重算。
- [ ] 验证重复合入、主库提交后清理前中断、单只失败及特征计算失败后的可恢复执行。
- [ ] 补充更新命令、调度配置、缓存清理和本地备份恢复说明；运行数据库不进入 Git。

以上均为后续实施与验收项；本次不执行建库、业务代码改动、定时更新或数据迁移。
