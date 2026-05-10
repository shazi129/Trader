# stock_advisor 综合分析工具

对单只股票出多周期涨跌预测报告。

## 用法

两种入口方式，效果一样，按你当前 shell 所在目录二选一：

### A. 从项目根目录运行（推荐）

```bash
cd D:\GitHub\Trader

# 基本用法（落盘 markdown 到 reports/）
python -m tools.stock_advisor.stock_advisor Tencent

# 自定义参数
python -m tools.stock_advisor.stock_advisor Alibaba --api eastmoney --top-k 80

# 只看不落盘
python -m tools.stock_advisor.stock_advisor Tencent --no-write

# 强制重算（忽略 DB 缓存）
python -m tools.stock_advisor.stock_advisor Tencent --force-refresh
```

### B. 从当前目录（`tools\stock_advisor`）直接运行脚本

必须**直接跑 `.py` 文件**，不要加 `-m`（否则相对 import 会报
`attempted relative import with no known parent package`）：

```bash
cd D:\GitHub\Trader\tools\stock_advisor

python stock_advisor.py Tencent
python stock_advisor.py Alibaba --api eastmoney --top-k 80
python stock_advisor.py Tencent --no-write
python stock_advisor.py Tencent --force-refresh
```

脚本顶部会自动把项目根加进 `sys.path`，所以 `database` / `quantitative`
等顶层包都能正常 import。

### 常见错误

- `ModuleNotFoundError: No module named 'tools'`
  → 你在 `tools\stock_advisor` 子目录里跑了 `-m tools.stock_advisor.xxx`。
  用方案 A（回根目录）或方案 B（直接跑文件）。
- `attempted relative import with no known parent package`
  → 你在子目录里跑了 `python -m stock_advisor`。
  同样改用方案 A 或 B。
- `python -m stock_advisor.py ...`
  → `-m` 后面跟的是**模块名**不是文件名，不能带 `.py` 后缀。

## 流程

1. **数据加载**：先查 DB；若 K 线最新日 ≠ 因子表最新日，触发
   `compute_and_save_factors` 重算并写回。
2. **多因子打分**：复用 `QuantFactorEngine` + `compute_probability`，
   给出"当前"多空力量加权概率。
3. **历史相似态回测**：`HorizonBacktester` 在 z-scored 因子空间里找
   `top_k` 个最相似的历史日，统计它们 5/20/60 日后的涨跌频率作为预测概率。
4. **报告**：markdown 落盘到 `reports/{stock}_{timestamp}.md`，控制台同步打印。

## 报告结构

- `1. 当前状态评分`：单点多因子加权 → **此刻**多空力量快照（非预测）
- `2. 多周期涨跌预测`：短(5日) / 中(20日) / 长(60日) 三档历史相似态频率
- `3. 因子明细`：每个因子的具体读数与信号
- `4. 风险提示`

> 第 1 节与第 2 节方向相反是正常的：
> 比如当前超卖（第 1 节偏空），但历史上每次跌到此位后多数反弹（第 2 节偏多），
> 这是均值回归现象。

## 历史相似态算法（核心）

特征向量（K=12 维）：

```
RSI, MACD柱, KDJ_K, CCI, Williams%R,
1M动量, 3M动量,
Price/MA5, Price/MA20, Price/MA200,
ATR%, 20日HV
```

步骤：

1. 用全历史数据算每维 mean/std，把所有日期的特征都转 z-score；
2. 当前 `v_now` 对历史每一日 `v_t` 算欧氏距离，取 top_k 个最近邻；
3. 历史样本必须距今 ≥ `max(horizons)=60` 天，避免未来函数；
4. 对这些"相似日"看 5/20/60 天后的真实收益分布 → 上涨概率 = 正样本占比。

## 限制

- 至少需要 ~160 个有效交易日才能跑历史回测；
- 完全量价驱动，不含基本面 / 资金面 / 情绪面；
- 除权日附近因子值波动较大，相似匹配可能失真；
- 仅供研究，不构成投资建议。
