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
| `sync_market_history` | 对当前股票池及指定白银标的补齐最近十年日 K 线 |
| `update_market_data` | 选择 Provider、增量拉取并保存行情 |
| `materialize_features` | 读取行情、计算并保存特征 |
| `run_backtest` | 选择标的与截止点、执行回测、保存产物 |
| `analyze_stock` | 获取 PIT 行情和量化结果，返回应用 DTO |
| `build_stock_report` | 组合量化、基本面及展示数据 |

应用层不包含指标公式、SQL 或 PDF 解析规则。

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

### 5.3 日常行情更新与特征物化

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

迁移优先使用 `git mv` 保留历史。每批移动后立即修复 import、运行测试并单独提交，
不夹带无关格式化。

## 10. 兼容策略

- 原 `quote_api`、`quantitative`、`financial_reports` 公共入口短期 re-export 新包；
- `python -m quantitative.cli` 等旧命令暂时转发到新入口；
- 内部代码先切换为 `trader.*`，确认没有旧 import 后再删除兼容层；
- 数据库先继续读取旧路径，显式迁移成功后才改变默认路径；
- 数据迁移前创建备份，校验表、行数、日期范围和关键字段；
- 兼容层只转发，不保留第二套实现。

## 11. 分阶段实施计划

### 阶段 0：冻结基线

- 记录 Python 版本、依赖、命令和公共 API；
- 运行完整离线测试；
- 补齐第 8 节的行为基线；
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
- 删除 `tools` 中重复的业务编排；
- 保留兼容入口。

验收：CLI 与 Web 对相同输入产生相同结构化业务结果。

### 阶段 6：运行数据整理

- 在验证备份后迁移数据库、模型、财报和报告目录；
- 更新 `.gitignore`、示例配置和数据准备说明；
- 落实大型历史文件的 Git LFS 或外部存储策略。

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

## 16. 后续扩展

未来新增舆情可建立 `sentiment` 域，组合和持仓可在模型稳定后建立 `portfolio` 域。
新领域通过应用层参与综合分析，不把自身数据塞进行情表或量化特征表，也不依赖
`tools`。
