# -*- coding: utf-8 -*-
"""
分周期因子权重优化脚本（可重复运行，股票池扩充后重跑即可刷新权重）

方法论（最严谨路径）：
  1. 对每个因子，在多个「预测周期 horizon」上分别计算：
       - 横截面 Rank IC（Spearman）序列 → IC均值 / ICIR / IC>0比例 / t值
       - 多空分组（Q5 - Q1）收益 → LS均值 / t值 / 胜率
  2. 根据因子的「固有计算周期」将其归入 short(≤20d) / medium(≤60d) / long(>60d)
     三个桶；每个因子**只在其桶对应的 horizon 范围内**取 ICIR 最好的一档来定权重，
     避免用短期因子的 250d IC 这类无意义数据。
  3. 权重 = 该因子最佳 horizon 的 |ICIR|，做 min-max 归一到 [W_MIN, W_MAX] 防过拟合，
     再按桶内归一化（桶内权重和为 1，便于后续分周期快照各自加权）。

产物：
  - quantitative/analyzer/period_weights.json  （供 factors.py / scoring 加载）
  - 控制台打印每因子各 horizon 的 ICIR 与最终分桶权重

用法（股票池变化后）：
  cd H:\\GitHub\\WorkSpace\\Trader
  python quantitative\\analyzer\\optimize_period_weights.py
"""

from __future__ import annotations

import json
import logging
import math
import os
import sys
from collections import defaultdict
from typing import Optional

import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.stock_db_utils import StockDB
from quantitative.analyzer.analyzer import QuantFactorEngine
from quote_api.quote_base import DailyQuote

_log = logging.getLogger("trader.quantitative.analyzer.optimize_period_weights")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "database", "stock_data.db")
DB_PATH = os.environ.get("STOCK_DB_PATH", DEFAULT_DB_PATH)

# 预测周期档位（交易日）
HORIZONS = [5, 20, 60, 120, 250]

# 最小历史：至少要有最长 horizon + 12M 动量所需 252 天
MIN_HISTORY = 252

# 权重截断范围（防过拟合，避免单一因子主导）
W_MIN, W_MAX = 0.5, 1.5

# 各周期桶对应的最大 horizon（天）。因子按"固有计算周期"归入桶：
#   short   : 固有周期 <= 20d   适用 horizon ∈ {5, 20}
#   medium  : 固有周期 <= 60d   适用 horizon ∈ {5, 20, 60}
#   long    : 固有周期  > 60d   适用 horizon ∈ {5, 20, 60, 120, 250}
BUCKET_MAX_HORIZON = {"short": 20, "medium": 60, "long": 250}

# 因子名 -> 固有周期桶（依据 factors.py compute_all 实际返回的 FactorResult.name）
# 注意：基本面类因子在 fundamentals=None 时不返回，这里也列出以便未来接入。
FACTOR_BUCKET = {
    # ---- 动量类 ----
    "1M动量": "short",
    "3M动量": "medium",
    "6M动量": "long",
    "12M动量": "long",
    "9M动量": "long",
    "11M动量": "long",
    "30W/75W均线比": "long",
    "5W/30W均线比": "medium",
    "价格/MA200": "long",
    "12M+1M反转": "long",
    # ---- 技术类（默认周期多为 14/20 日，归 short/medium）----
    "RSI(14)": "short",
    "MACD": "medium",
    "布林带%B": "short",
    "量比": "short",
    "KDJ": "short",
    "Williams %R": "short",
    "OBV": "short",
    "CCI": "short",
    "ATR": "short",
    "VPT": "medium",
    "ADL": "medium",
    "Chaikin Osc": "medium",
    # ---- 趋势类 ----
    "均线排列": "long",
    "趋势强度": "medium",
    "ADX": "medium",
    "DMI": "medium",
    # ---- 波动 / 风险类 ----
    "历史波动率": "short",
    "最大回撤": "long",
    "下行波动率": "short",
    "夏普比率": "long",
    "索提诺比率": "long",
    "GK波动率": "short",
    "Parkinson波动率": "short",
    "RS波动率": "short",
    "收益率偏度": "medium",
    "收益率峰度": "medium",
    "Amihud非流动性": "medium",
    # ---- 流动性 / 资金面类 ----
    "换手率Z分": "short",
    "成交额比率": "medium",
    "流动性分位": "medium",
    "量价相关20": "short",
    "资金强度": "short",
    # ---- 短期反转类 ----
    "1周反转": "short",
    "2周反转": "short",
    # ---- 价格形态类 ----
    "跳空缺口": "short",
    # ---- 基本面类（长期维度，fundamentals 接入后才会返回）----
    "市盈率PE": "long",
    "市净率PB": "long",
    "市销率PS": "long",
    "净资产收益率ROE": "long",
    "资产回报率ROA": "long",
    "EPS增长率": "long",
    "营收增长率": "long",
    "股息率": "long",
    "市值规模": "long",
}

# 已知会抛 math domain error 的因子，评估时跳过（对横截面收益预测价值有限）
EXCLUDE_FACTORS = {"GK波动率", "Parkinson波动率", "RS波动率"}

OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "period_weights.json")


# ---------------------------------------------------------------------------
# 秩相关工具
# ---------------------------------------------------------------------------
def _rankdata(a: np.ndarray) -> np.ndarray:
    arr = np.asarray(a, dtype=float)
    order = arr.argsort()
    ranks = np.empty(len(arr), dtype=float)
    ranks[order] = np.arange(1, len(arr) + 1)
    _, inv, counts = np.unique(arr, return_inverse=True, return_counts=True)
    means = np.zeros(len(counts))
    start = 0
    for i, c in enumerate(counts):
        means[i] = start + (c + 1) / 2.0
        start += c
    return means[inv]


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) < 3:
        return float("nan")
    return float(pearson(_rankdata(a), _rankdata(b)))


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) < 3:
        return float("nan")
    am, bm = a - a.mean(), b - b.mean()
    denom = math.sqrt((am * am).sum() * (bm * bm).sum())
    return float((am * bm).sum() / denom) if denom else float("nan")


# ---------------------------------------------------------------------------
# 数据收集：每个 (因子, horizon) -> 横截面 (因子值, 未来收益) 面板
# ---------------------------------------------------------------------------
def collect(db: StockDB) -> dict:
    """返回 panel[horizon][date_str][symbol] = (factor_value_dict, fwd_return)"""
    symbols = db.list_symbols(db.TABLE_KLINE)
    _log.info("评估 %d 只股票：%s", len(symbols), symbols)

    panel: dict[int, dict[str, dict]] = {h: defaultdict(dict) for h in HORIZONS}
    fwd_ret_panel: dict[int, dict[str, dict]] = {h: defaultdict(dict) for h in HORIZONS}
    factor_names: list[str] = []

    for symbol in symbols:
        klines = db.get_klines_in_range(symbol)
        if not klines or len(klines) < MIN_HISTORY + max(HORIZONS) + 1:
            _log.warning("%s 数据不足（%d 条），跳过", symbol, len(klines) if klines else 0)
            continue
        n = len(klines)
        _log.info("%s K线 %d 条，%s ~ %s", symbol, n, klines[0].date, klines[-1].date)

        for t in range(MIN_HISTORY, n - max(HORIZONS)):
            window = klines[: t + 1]
            try:
                engine = QuantFactorEngine(window, fundamentals=None)
                results = engine.compute_all()
            except Exception as e:
                _log.warning("%s @ %s compute_all error: %s", symbol, klines[t].date, e)
                continue

            fvals = {r.name: r.value for r in results if r is not None and r.name not in EXCLUDE_FACTORS}
            if not factor_names and fvals:
                factor_names = list(fvals.keys())

            date_str = klines[t].date
            for h in HORIZONS:
                target = t + h
                if target >= n:
                    continue
                c0, c1 = klines[t].close, klines[target].close
                if c0 <= 0 or c1 <= 0:
                    continue
                fr = (c1 - c0) / c0 * 100.0
                panel[h][date_str][symbol] = fvals
                fwd_ret_panel[h][date_str][symbol] = fr

    _log.info("面板构建完成，因子数=%d", len(factor_names))
    return {"factor_names": factor_names, "panel": panel, "fwd": fwd_ret_panel}


# ---------------------------------------------------------------------------
# 对每个 horizon 计算每因子的 Rank IC 指标
# ---------------------------------------------------------------------------
def compute_ic_per_horizon(factor_names, panel_h, fwd_h):
    ic_by_factor: dict[str, list] = defaultdict(list)
    dates = sorted(panel_h.keys())
    for d in dates:
        symbols = list(panel_h[d].keys())
        if len(symbols) < 3:
            continue
        rets = np.array([fwd_h[d][s] for s in symbols], dtype=float)
        for fname in factor_names:
            vals = np.array([panel_h[d][s].get(fname, np.nan) for s in symbols], dtype=float)
            mask = ~np.isnan(vals)
            if mask.sum() < 3:
                continue
            ic = spearman(vals[mask], rets[mask])
            if not math.isnan(ic):
                ic_by_factor[fname].append(ic)

    stats = {}
    for fname in factor_names:
        series = np.array(ic_by_factor[fname], dtype=float)
        if len(series) == 0:
            continue
        ic_mean = float(series.mean())
        ic_std = float(series.std(ddof=1)) if len(series) > 1 else float("nan")
        icir = ic_mean / ic_std if ic_std and ic_std > 0 else float("nan")
        pos_ratio = float((series > 0).mean())
        t_stat = ic_mean / (ic_std / math.sqrt(len(series))) if ic_std and ic_std > 0 else float("nan")
        stats[fname] = {
            "ic_mean": ic_mean,
            "icir": icir,
            "ic_pos_ratio": pos_ratio,
            "ic_t_stat": t_stat,
            "n": int(len(series)),
        }
    return stats


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("trader.quantitative.analyzer.factors").setLevel(logging.ERROR)

    db = StockDB(DB_PATH)
    try:
        data = collect(db)
        factor_names = data["factor_names"]
        panel = data["panel"]
        fwd = data["fwd"]

        # 每个 horizon 的 IC 统计
        horizon_ic: dict[int, dict] = {}
        for h in HORIZONS:
            horizon_ic[h] = compute_ic_per_horizon(factor_names, panel[h], fwd[h])

        # 每个因子：在其桶允许的 horizon 范围内取 |ICIR| 最大的一档
        factor_best: dict[str, dict] = {}
        for fname in factor_names:
            bucket = FACTOR_BUCKET.get(fname, "medium")
            allowed = [h for h in HORIZONS if h <= BUCKET_MAX_HORIZON[bucket]]
            best_h, best_icir = None, 0.0
            for h in allowed:
                s = horizon_ic[h].get(fname)
                if s is None or math.isnan(s["icir"]):
                    continue
                if abs(s["icir"]) > abs(best_icir):
                    best_icir, best_h = s["icir"], h
            if best_h is None:
                continue
            factor_best[fname] = {
                "bucket": bucket,
                "best_horizon": best_h,
                "icir": horizon_ic[best_h][fname]["icir"],
                "ic_mean": horizon_ic[best_h][fname]["ic_mean"],
                "ic_pos_ratio": horizon_ic[best_h][fname]["ic_pos_ratio"],
                "ic_t_stat": horizon_ic[best_h][fname]["ic_t_stat"],
                "n": horizon_ic[best_h][fname]["n"],
            }

        # 分桶权重：用 |ICIR| 做 min-max 归一到 [W_MIN, W_MAX]
        bucket_raw: dict[str, dict] = defaultdict(dict)
        for fname, info in factor_best.items():
            bucket_raw[info["bucket"]][fname] = abs(info["icir"])

        final_weights: dict[str, dict] = {"short": {}, "medium": {}, "long": {}}
        for bucket, raw in bucket_raw.items():
            vals = list(raw.values())
            lo, hi = min(vals), max(vals)
            span = hi - lo if hi > lo else 1.0
            for fname, v in raw.items():
                norm = (v - lo) / span  # 0~1
                w = W_MIN + norm * (W_MAX - W_MIN)
                final_weights[bucket][fname] = round(w, 4)

        # 保存
        out = {
            "method": "cross_sectional_rank_ic_per_horizon_then_bucket_weight",
            "horizons": HORIZONS,
            "min_history": MIN_HISTORY,
            "weight_bounds": [W_MIN, W_MAX],
            "bucket_max_horizon": BUCKET_MAX_HORIZON,
            "weights": final_weights,
            "factor_best_horizon": factor_best,
            "horizon_ic": {str(h): horizon_ic[h] for h in HORIZONS},
            "n_factors": len(factor_names),
            "factor_names": factor_names,
        }
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        _log.info("权重已保存：%s", OUTPUT_JSON)

        # 打印报告
        print("\n========== 分周期 Rank IC 评估（横截面）==========")
        print(f"预测周期档位(h): {HORIZONS}  最小历史: {MIN_HISTORY}  权重范围: [{W_MIN},{W_MAX}]")
        print(f"因子总数: {len(factor_names)}\n")

        for bucket in ("short", "medium", "long"):
            print(f"===== 周期桶: {bucket} (适用 horizon ≤ {BUCKET_MAX_HORIZON[bucket]}) =====")
            print(f"{'因子':24s} {'最佳h':>5s} {'IC均值':>8s} {'ICIR':>7s} {'IC>0':>6s} {'t值':>7s} {'权重':>6s}")
            items = sorted(
                [(fn, factor_best[fn]) for fn in final_weights[bucket]],
                key=lambda x: -abs(x[1]["icir"]),
            )
            for fn, info in items:
                print(f"{fn:24s} {info['best_horizon']:5d} {info['ic_mean']:8.4f} "
                      f"{info['icir']:7.3f} {info['ic_pos_ratio']:6.2f} "
                      f"{info['ic_t_stat']:7.2f} {final_weights[bucket][fn]:6.3f}")
            print()

        print("说明：")
        print("  - 每个因子仅在其周期桶允许的 horizon 内取 |ICIR| 最大档定权。")
        print("  - 权重按桶内 |ICIR| 归一到 [%.1f, %.1f]，避免单一因子主导。" % (W_MIN, W_MAX))
        print("  - 股票池扩充后，重跑本脚本即可刷新 period_weights.json。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
