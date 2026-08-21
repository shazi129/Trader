# Trader

Trader 是一个按业务域组织的个人交易研究项目，覆盖行情获取、技术特征、
指标形态、无未来函数回测、时点分析和财报分析。

## 架构

```text
quote_api                 行情 API、标准模型、K 线仓储与缓存
quantitative
├─ indicators             纯数学指标算法
├─ features               从 K 线计算并物化特征
├─ signals                金叉、背离、超买超卖等形态
├─ backtesting            形态的成功率、样本量与权重
└─ analysis               某标的某时点的统一量化分析
financial_reports         财报解析、仓储与 PIT 基本面分析
infrastructure            通用 SQLite 连接和 SQL 能力
tools                     CLI、桌面和 Web 适配器
```

数据库不是独立业务模块。每个领域拥有自己的 Repository 和数据表：

- `MarketDataRepository` 管理 `kline_daily`；
- `FeatureRepository` 管理 `quant_feature_daily`；
- `FinancialReportRepository` 管理 `financial_report`；
- `infrastructure.sqlite` 只提供通用 SQLite 能力，不知道任何业务字段。

详细的依赖规则和数据流见 [架构文档](docs/architecture.md)，表结构见
[数据文档](docs/data_schema.md)。

各模块使用手册：

- [行情 API](docs/modules/quote_api.md)
- [量化特征](docs/modules/quantitative_features.md)
- [形态信号](docs/modules/quantitative_signals.md)
- [形态回测](docs/modules/quantitative_backtesting.md)
- [时点分析](docs/modules/quantitative_analysis.md)
- [财报与基本面](docs/modules/financial_reports.md)
- [SQLite 基础设施](docs/modules/infrastructure.md)

## 从基础 K 线到分析结果

```text
DailyQuote
  → FeatureCalculator
  → FeatureSnapshot
  → SignalEngine
  → SignalResult
  → SignalBacktester 生成历史统计
  → QuantitativeAnalysisService 聚合 5/20/60 日概率
```

这条链路明确区分五个概念：

- indicator：SMA、RSI、MACD 等纯算法；
- feature：某标的某日的指标数值；
- signal：金叉、背离等已触发或未触发的形态；
- metric：某形态在历史上的成功率、样本量和权重；
- analysis：当前时点的多周期概率和解释。

特征清单的唯一来源是 `quantitative/features/catalog.py`。新增特征时无需再维护
数据库字段映射副本。

## 安装

需要 Python 3.10 或更高版本。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 快速开始

先拉取行情并同步物化特征：

```powershell
python tools/kline_fetcher/kline_fetcher.py run
```

也可以对单个标的直接使用量化域 CLI：

```powershell
python -m quantitative.cli features Tencent --api futu
python -m quantitative.cli backtest
python -m quantitative.cli backtest --stocks Tencent,Alibaba
python -m quantitative.cli analyze Tencent
python -m quantitative.cli analyze Tencent --date 2026-08-20
```

`backtest` 不传 `--stocks` 时会回测 `STOCK_META` 中全部具备足够本地 K 线的
标的；传入时只回测指定标的。命令会把实际标的池、数据截止日及 5、20、60 日
的形态统计写入版本化的
`quantitative/backtesting/signal_statistics.json`。未生成统计时，分析服务会使用
低置信度的中性先验，不会把未经回测的规则伪装成可靠概率。
控制台会同时按形态输出 5、20、60 日的方向成功率、样本量和权重。

生成综合 Markdown 报告：

```powershell
python -m tools.stock_advisor.stock_advisor Tencent
python -m tools.stock_advisor.stock_advisor Tencent --rebuild-signal-stats
```

`stock_advisor` 严格使用本地数据库，不会在生成报告时连接线上行情源。特征缺失时
只基于本地 K 线重建；行情更新由 `kline_fetcher` 独立负责。

其它工具：

- [kline_fetcher](tools/kline_fetcher/README.md)：增量行情抓取和特征物化；
- [stock_advisor](tools/stock_advisor/README.md)：量化、历史相似态和基本面报告；
- [financial_fetcher](tools/financial_fetcher/README.md)：财报 PDF 解析与入库；
- [stock_widget](tools/stock_widget/readme.md)：桌面实时行情；
- [fund_holdings](tools/fund_holdings/README.md)：基金持仓研究。

## 扩展方式

新增技术特征：

1. 在 `quantitative/indicators/` 添加或复用纯函数；
2. 在 `quantitative/features/catalog.py` 注册特征；
3. 在 `FeatureCalculator` 中计算该序列；
4. 添加计算与仓储测试。

新增形态规则：

1. 在 `quantitative/signals/` 实现 `SignalRule`；
2. 把规则类加入 `RULE_TYPES` 显式注册表；
3. 用 `quantitative.cli backtest` 重建成功率和权重。

新增行情源：实现 `QuoteAPI`，然后在 `QuoteAPIFactory` 注册。业务层只依赖统一的
`DailyQuote`，不依赖具体 provider。

新增财报字段：更新 `financial_reports/field_mapping.py` 中的 `UNIFIED_FIELDS` 和
市场映射；`FinancialReportRepository` 会自动补齐数据库列。

## 测试

```powershell
pytest
pytest -m integration
```

默认测试只运行离线用例；`integration` 标记的真实外部服务测试需显式执行。

## 免责声明

本项目仅用于个人研究和学习，不构成投资建议。基于项目输出做出的交易决策，
风险由使用者自行承担。
