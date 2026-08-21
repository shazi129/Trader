# stock_advisor

为单个标的生成综合 Markdown 报告。它是工具层编排器，不定义指标公式、形态规则
或数据库 schema。

## 报告组成

1. 统一量化分析：当前实际触发的形态，以及基于历史统计聚合出的 5/20/60 日概率；
2. 历史相似态：在标准化特征空间寻找 top-K 相似交易日并统计后续收益；
3. PIT 基本面快照：只使用分析时点之前已经公告的财报；
4. 长期财务趋势和估值辅助信息；
5. 风险提示。

形态统计与相似态是两种不同证据：前者回答“这个形态历史上是否有效”，后者回答
“当前完整特征状态在历史上更像哪些日期”。二者不必给出相同方向。

## 用法

推荐在项目根目录运行：

```powershell
python -m tools.stock_advisor.stock_advisor Tencent
python -m tools.stock_advisor.stock_advisor Alibaba --top-k 80
python -m tools.stock_advisor.stock_advisor Tencent --no-write
python -m tools.stock_advisor.stock_advisor Tencent --force-refresh
python -m tools.stock_advisor.stock_advisor Tencent --rebuild-signal-stats
python -m tools.stock_advisor.stock_advisor Tencent --db path/to/trader.db
```

- `--force-refresh`：重新从线上 provider 拉取行情并物化特征；
- `--rebuild-signal-stats`：先对股票池回测全部形态，重建成功率、样本量和权重；
- `--no-write`：只打印，不保存 Markdown；
- `--report-dir`：指定报告目录；
- `--api`：选择缺失行情的线上来源。

也可以从本目录直接执行 `python stock_advisor.py Tencent`。使用 `-m` 时必须从
项目根目录运行，并提供完整模块名。

## 数据一致性

工具分别比较 `MarketDataRepository.latest_date()` 和
`FeatureRepository.latest_date()`。若行情为空、特征落后，或显式要求刷新，便
调用量化域的 `materialize_symbol()`；它不会直接操作业务表。

基本面快照由 `financial_reports.analysis.build_snapshot()` 生成，查询条件包含
`announce_date <= 分析时点`，避免读到当时尚未公告的财报。

## 历史相似态

当前实现选取 RSI、MACD 柱、KDJ、CCI、Williams %R、动量、均线比、ATR、
历史波动率和流动性等特征：

1. 按日期对齐行情与 `FeatureSnapshot`；
2. 对各维特征做 z-score；
3. 用欧氏距离选择 top-K 历史状态；
4. 排除没有完整 60 日未来验证窗口的日期；
5. 分别统计 5、20、60 日收益。

这是工具级辅助模型；形态成功率与权重的正式回测位于
`quantitative/backtesting/`。

## 限制

- 相似态通常至少需要约 160 个有效交易日；
- 基本面是低频信息，不混入日频技术特征；
- 历史概率不是确定性预测；
- 输出仅供研究，不构成投资建议。
