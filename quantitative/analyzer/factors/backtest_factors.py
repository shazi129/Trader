# -*- coding: utf-8 -*-
"""因子回测脚本：统计各因子在 5/30/60 日周期的预测命中率，写入 accuracy.json。

运行方式::

    cd Trader
    python quantitative/analyzer/factors/backtest_factors.py                 # 回测全部股票
    python quantitative/analyzer/factors/backtest_factors.py --stocks Tencent,Meituan
    python quantitative/analyzer/factors/backtest_factors.py --min-history 250 --api futu

原理
----
对每个股票、历史每个 anchor_date（要求其后至少有 60 个交易日以免未来泄漏）：
  1. 用 FactorManager 预读数据并构造 FactorContext；
  2. 运行所有因子，得到每个因子的 forecast=(5日涨?,30日涨?,60日涨?)；
  3. 用 ctx.future_close(h) 取得真实未来价，判断 forecast[h] == (真实涨)；
  4. 分因子×周期累计 命中数 / 样本数 → 命中率。

命中率写入 quantitative/analyzer/factors/accuracy.json，
后续 FactorManager.analyze 会按准确率对 forecast 加权。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict

import numpy as np

# 保证中文日志可读（部分终端默认非 UTF-8）
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 将项目根目录（Trader/）加入模块搜索路径，确保无论从哪个目录运行
# 都能找到 quote_api / quantitative / config / utils 等包。
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import config  # noqa: E402
from quantitative.analyzer.factors.manager import FactorManager, _ACCURACY_FILE  # noqa: E402
from quantitative.analyzer.factors.registry import instantiate_all  # noqa: E402
from quantitative.analyzer.factors.base import FactorContext, FORECAST_HORIZONS  # noqa: E402
from utils.logger import get_logger  # noqa: E402

_log = get_logger(__name__)

# 累计结构: hit[name][h], total[name][h]（跨股票汇总）
hit: Dict[str, Dict[int, int]] = defaultdict(lambda: {h: 0 for h in FORECAST_HORIZONS})
total: Dict[str, Dict[int, int]] = defaultdict(lambda: {h: 0 for h in FORECAST_HORIZONS})

# 每只股票独立的累计: hit_by_stock[name][stock][h]
hit_by_stock: Dict[str, Dict[str, Dict[int, int]]] = defaultdict(
    lambda: defaultdict(lambda: {h: 0 for h in FORECAST_HORIZONS})
)
total_by_stock: Dict[str, Dict[str, Dict[int, int]]] = defaultdict(
    lambda: defaultdict(lambda: {h: 0 for h in FORECAST_HORIZONS})
)


def backtest_stock(mgr: FactorManager, name_key: str, min_history: int) -> None:
    """对单只股票滚动回测所有因子。"""
    # 取整段历史；多取 60 日作为未来验证窗口
    quotes = mgr.impl.get_klines(name_key, limit=2000)
    if not quotes:
        _log.warning("[%s] 无数据，跳过", name_key)
        return

    # 构造完整的 full_df（含未来），用于 future_close
    rows = [q.__dict__ for q in quotes]
    import pandas as pd
    df = pd.DataFrame(rows)
    for col in ("date", "open", "high", "low", "close", "volume", "amount"):
        if col not in df.columns:
            for alias in (col.upper(), col.capitalize()):
                if alias in df.columns:
                    df[col] = df[alias]
                    break
    df = df.sort_values("date").reset_index(drop=True)
    df["close"] = df["close"].astype(float)

    # ---- 数据有效性校验：过滤 cached_api 在底层失败时生成的占位假数据 ----
    if len(df) == 0:
        _log.warning("[%s] 无数据，跳过", name_key)
        return
    closes = df["close"].to_numpy(dtype=float)
    # 占位数据常表现为收盘价恒定或日收益全 0
    if closes.std() < 1e-9 or (np.diff(closes) == 0).all():
        _log.warning("[%s] 检测到疑似占位假数据（价格无波动），跳过", name_key)
        return
    # 日期应单调递增且为交易日序列
    if df["date"].nunique() != len(df):
        _log.warning("[%s] 日期存在重复，疑似伪造数据，跳过", name_key)
        return

    n_total = len(df)
    # 要求之后至少有 max(horizon)=60 日，且之前至少有 min_history 日
    max_h = max(FORECAST_HORIZONS)
    last_anchor = n_total - 1 - max_h
    if last_anchor < min_history:
        _log.warning("[%s] 数据不足 (%d 条)，跳过", name_key, n_total)
        return

    factors = instantiate_all()
    # 预计算各因子的 MACD 等重指标会很慢；这里每次重建 context 即可（因子内部按需算）

    for i in range(min_history, last_anchor + 1):
        anchor_date = df["date"].iloc[i]
        lookback_window = df.iloc[max(0, i - 250): i + 1].reset_index(drop=True)
        full_window = df.iloc[max(0, i - 250):].reset_index(drop=True)
        ctx = FactorContext(
            name_key=name_key,
            anchor_date=anchor_date,
            df=lookback_window,
            full_df=full_window,
        )
        # 真实未来价（与因子内部 future_close 走同一数据源，避免索引错位）
        real_future = {}
        for h in FORECAST_HORIZONS:
            real_future[h] = ctx.future_close(h)

        if any(v is None for v in real_future.values()):
            continue

        for f in factors:
            try:
                out = f.detect(ctx)
            except Exception as e:  # pragma: no cover
                _log.warning("[%s] 因子 %s 失败: %s", name_key, f.name, e)
                continue
            # 只统计因子真正触发的 anchor 点，未触发（中性）样本不参与，
            # 否则会把未触发误记为"预测下跌"，系统性压低命中率。
            if not out.triggered:
                continue
            for idx, h in enumerate(FORECAST_HORIZONS):
                fc = out.forecast[idx]
                if fc is None:
                    continue
                real_up = real_future[h] > ctx.anchor_price
                if fc == real_up:
                    hit[f.name][h] += 1
                    hit_by_stock[f.name][name_key][h] += 1
                total[f.name][h] += 1
                total_by_stock[f.name][name_key][h] += 1

    # ---- 实时打印：本只股票每个因子的成功率 ----
    print(f"\n===== 股票 {name_key} 各因子回测结果 =====")
    for factor_name in sorted(hit_by_stock):
        by_stock = hit_by_stock[factor_name].get(name_key)
        if not by_stock:
            continue
        parts = []
        for h in FORECAST_HORIZONS:
            t = total_by_stock[factor_name][name_key][h]
            rate = (hit_by_stock[factor_name][name_key][h] / t) if t > 0 else 0.0
            parts.append(f"{h}日={rate*100:5.1f}%(n={t})")
        print(f"  {factor_name:14s} " + "  ".join(parts))

    _log.info("[%s] 回测完成 (%d 个 anchor 点)", name_key, last_anchor - min_history + 1)


def merge_accuracy(out_path: str, overwrite: bool) -> None:
    """把累计命中率合并写入 accuracy.json。"""
    existing: Dict[str, Dict[str, float]] = {}
    if os.path.exists(out_path) and not overwrite:
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            existing.pop("_comment", None)
        except Exception:
            existing = {}

    # 组装新结果
    new_acc: Dict[str, Dict[str, float]] = {}
    for name in hit:
        new_acc[name] = {}
        for h in FORECAST_HORIZONS:
            t = total[name][h]
            new_acc[name][str(h)] = round(hit[name][h] / t, 4) if t > 0 else 0.5

    # 合并：overwrite 时直接用新值；否则保留旧值并向后兼容
    merged = dict(existing)
    for name, d in new_acc.items():
        if overwrite or name not in merged:
            merged[name] = d
        else:
            # 取两者中样本更多 / 已存在则保留旧（回测是增量累积，本脚本一次性算全）
            merged[name] = d

    # 确保 registry 中出现的因子都有记录
    for f in instantiate_all():
        merged.setdefault(f.name, {"5": 0.5, "30": 0.5, "60": 0.5})

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    _log.info("命中率已写入 %s", out_path)

    # ---- 汇总：所有股票合并后的因子成功率 ----
    print("\n\n########## 回测汇总（全部股票合并） ##########")
    for name in sorted(new_acc):
        d = new_acc[name]
        n_total = total[name][5]
        print(f"  {name:14s} 5日={d['5']*100:5.1f}%  30日={d['30']*100:5.1f}%  "
              f"60日={d['60']*100:5.1f}%   (样本数 n={n_total})")


def main() -> None:
    parser = argparse.ArgumentParser(description="因子命中率回测")
    parser.add_argument("--api", default="db", help="数据源 (默认 db: 仅读本地数据库，不联网)")
    parser.add_argument("--stocks", default="", help="逗号分隔的 name_key，默认全部")
    parser.add_argument("--min-history", type=int, default=120,
                        help="每个 anchor 点往前至少需要的回看天数")
    parser.add_argument("--out", default=_ACCURACY_FILE, help="accuracy.json 输出路径")
    parser.add_argument("--overwrite", action=argparse.BooleanOptionalAction, default=True,
                        help="是否覆盖已有 accuracy.json（默认覆盖；--no-overwrite 仅补充缺失项）")
    args = parser.parse_args()

    if args.stocks:
        stocks = [s.strip() for s in args.stocks.split(",") if s.strip()]
    else:
        stocks = list(config.global_stock_list.keys())

    mgr = FactorManager(api=args.api, use_cache=True)
    for name_key in stocks:
        if name_key not in config.global_stock_list:
            _log.warning("%s 不在 global_stock_list，尝试直接回测", name_key)
        backtest_stock(mgr, name_key, args.min_history)

    merge_accuracy(args.out, args.overwrite)


if __name__ == "__main__":
    main()
