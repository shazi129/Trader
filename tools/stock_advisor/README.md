# stock_advisor

为单个标的生成综合 Markdown 报告。它是工具层编排器，不定义指标公式、形态规则
或数据库 schema。

## 报告组成

1. 综合量化概率：按经过校准的可靠性权重融合形态模型与历史相似态模型；
2. 统一形态分析：把当前实际触发的形态明确分成看多、看空两组；
3. 历史相似态：寻找 top-K 相似交易日，按距离加权并执行逐时点校准；
4. PIT 基本面快照：只使用分析时点之前已经公告的财报；
5. 长期财务趋势和估值辅助信息；
6. 风险提示。

形态统计与相似态是两种不同证据：前者回答“这个形态历史上是否有效”，后者回答
“当前完整特征状态在历史上更像哪些日期”。二者不必给出相同方向。

报告会同时列出形态的“名义方向”和各周期的“回测有效方向”，以及命中率、匹配的
个股周期基准、超额命中率、事件样本数、模型权重和概率贡献。未确认背离只进入
中性/待确认风险提示，不参与概率。命中率低于基准不会自动反转；只有扩展窗口训练
后的多个走步样本外区间仍稳定、显著地支持反向关系，才标记为“有效反向”。

综合概率采用可靠性加权的凸组合。形态权重来自触发信号的平均历史可靠性；相似态
权重来自距离质量、Kish 有效样本量和非重叠历史锚点上的 Brier 技能。两个模型共享
技术输入，因此不使用假设证据独立的赔率相乘。趋势文字和图标统一使用 60%/40%
门槛。

## 用法

推荐在项目根目录运行：

```powershell
python -m tools.stock_advisor.stock_advisor Tencent
python -m tools.stock_advisor.stock_advisor Alibaba --top-k 80
python -m tools.stock_advisor.stock_advisor Tencent --no-write
python -m tools.stock_advisor.stock_advisor Tencent --rebuild-features
python -m tools.stock_advisor.stock_advisor Tencent --rebuild-signal-stats
python -m tools.stock_advisor.stock_advisor Tencent --db path/to/trader.db
```

- `--rebuild-features`：只使用本地 K 线强制重建量化特征；
- `--rebuild-signal-stats`：先对股票池回测全部形态，重建成功率、样本量和权重；
- `--no-write`：只打印，不保存 Markdown；
- `--report-dir`：指定报告目录。

`stock_advisor` 是严格离线工具：不会创建 Futu/Tencent/Sina 客户端，也不会补拉
当天行情。本地没有 K 线时会直接失败，请先单独运行 `kline_fetcher`。

也可以从本目录直接执行 `python stock_advisor.py Tencent`。使用 `-m` 时必须从
项目根目录运行，并提供完整模块名。

## 数据一致性

工具分别比较 `MarketDataRepository.latest_date()` 和
`FeatureRepository.latest_date()`。特征缺失或落后时，使用 `source="db"` 调用
量化域的 `materialize_symbol()`；本地行情为空时不会回源。

基本面快照由 `financial_reports.analysis.build_snapshot()` 生成，查询条件包含
`announce_date <= 分析时点`，避免读到当时尚未公告的财报。

## 历史相似态

当前实现选取 RSI、MACD 柱、KDJ、CCI、Williams %R、动量、均线比、ATR、
历史波动率和流动性等特征：

1. 按日期对齐行情与 `FeatureSnapshot`；
2. 对各维特征做 z-score；
3. 用标准化欧氏距离选择 top-K 历史状态，并用自适应 Gaussian kernel 赋权；
4. 每个预测周期分别排除尚无未来结果的日期；
5. 用有效样本量和近邻质量把原始概率向 50% 收缩；
6. 在互不重叠的历史锚点上逐时点校准，以 Brier skill 生成融合可靠性；
7. 只有校准技能为正的相似态结果才进入综合概率。

这是工具级辅助模型；形态成功率与权重的正式回测位于
`quantitative/backtesting/`。

## 限制

- 相似态通常至少需要约 160 个有效交易日；
- 校准技能为 0 时，相似态仍会展示，但综合权重为 0；
- 基本面是低频信息，不混入日频技术特征；
- 历史概率不是确定性预测；
- 输出仅供研究，不构成投资建议。
