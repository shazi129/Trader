# -*- coding: utf-8 -*-
"""多周期历史相似态回测。

核心思路
========
"当前因子组合 v_now 在历史上长什么样 → 那些历史日期 N 天后的涨跌" 即为预测。

具体做法（k-NN on z-scored factor vector）：

1. 选一组代表性因子（动量 / 均线比 / RSI / MACD柱 / ATR% / 布林带% ...），
   构成 K 维向量 v。这组因子要求同一时间点都能从 DB 读到且数值稳定。
2. 用整段历史序列算每个因子的均值 / 方差，把每一天的 v 归一化成 z 分数。
   ──这样不同量纲的因子能一起算距离。
3. 当前时刻 v_now 对历史每一天 v_hist[t] 求欧氏距离 d[t]；
   取 top_k 个最相似的日期（排除距今 ``max(horizons)`` 天内避免未来函数）。
4. 对这些"相似日"看未来 horizon 天后的收益 r_t = close[t+h]/close[t] - 1：
   - 上涨概率 P_up = mean( r_t > 0 )
   - 期望收益 E[r] = mean(r_t)
5. 同一组相似日对 5/20/60 三个 horizon 分别统计，得到三档预测。

为什么不用 sklearn
------------------
- 项目零三方科学计算依赖（numpy/pandas 都没引），新加 sklearn 成本太大；
- K 维 + N 天的数据量很小（N ≤ 5000, K ≈ 10），纯 Python 算起来毫秒级。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from quantitative.factor_data import KlineIndicator
from quote_api.quote_base import DailyQuote
from utils.logger import get_logger

_log = get_logger(__name__)


# ===========================================================================
# 数据结构
# ===========================================================================

@dataclass
class HorizonForecast:
    """单个 horizon（预测期限）的预测结果。"""
    horizon_days: int
    label: str                  # "短期(5日)" / "中期(20日)" / "长期(60日)"
    prob_up: float              # 上涨概率 [0, 1]
    expected_return: float      # 期望收益（小数，0.05 = +5%）
    sample_size: int            # 相似样本数
    avg_positive: float         # 相似样本中上涨样本的平均涨幅
    avg_negative: float         # 相似样本中下跌样本的平均跌幅
    reason: str                 # 触发信号摘要（哪几个因子最接近）


@dataclass
class MultiHorizonForecast:
    """短/中/长期打包。"""
    short: Optional[HorizonForecast]
    medium: Optional[HorizonForecast]
    long: Optional[HorizonForecast]
    top_similar_dates: list[str]  # 命中了哪些历史日期（供报告引用）
    feature_contribution: dict[str, float]  # 特征 z 距离贡献度


# ===========================================================================
# 特征向量构造
# ===========================================================================

# (读属性名, 展示名)：这些必须都存在于 KlineIndicator 上，且在 indicator/trend/
# momentum/ma_ratio/risk 等因子表里有写入。选的都是"单日可读、方向意义明确"的。
_FEATURES: tuple[tuple[str, str], ...] = (
    ("rsi1", "RSI"),
    ("macd_hist", "MACD柱"),
    ("k", "KDJ_K"),
    ("cci", "CCI"),
    ("williams_r", "Williams%R"),
    ("mom1m", "1M动量"),
    ("mom3m", "3M动量"),
    ("ma_ratio_5", "Price/MA5"),
    ("ma_ratio_20", "Price/MA20"),
    ("ma_ratio_200", "Price/MA200"),
    ("atr_pct", "ATR%"),
    ("hv20", "20日HV"),
)


def _extract_vector(ind: KlineIndicator) -> Optional[list[float]]:
    """从 KlineIndicator 取特征向量；任一因子缺失/nan 返回 None。"""
    vec: list[float] = []
    for attr, _ in _FEATURES:
        v = getattr(ind, attr, None)
        if v is None:
            return None
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return None
        if fv != fv:  # nan
            return None
        vec.append(fv)
    return vec


# ===========================================================================
# 回测器
# ===========================================================================

class HorizonBacktester:
    """基于历史相似态的多周期预测器。

    使用方式::

        bt = HorizonBacktester(quotes, indicators)
        forecast = bt.run(horizons=(5, 20, 60), top_k=50)
    """

    # 历史上这个位置之后要有足够的 future bar 才算"可用样本"
    # 避免用最近几天当历史样本（会出现 future leakage）
    _DEFAULT_HORIZONS = (5, 20, 60)
    _HORIZON_LABELS = {5: "短期(5日)", 20: "中期(20日)", 60: "长期(60日)"}

    def __init__(self, quotes: list[DailyQuote],
                 indicators: list[KlineIndicator]):
        # 按 date 对齐 quotes / indicators（indicator 可能比 quote 少一两天的前缀）
        ind_by_date = {i.date: i for i in indicators if i.date}
        aligned: list[tuple[DailyQuote, KlineIndicator]] = []
        dropped_nonpos = 0
        for q in quotes:
            ind = ind_by_date.get(q.date)
            if ind is None:
                continue
            # 过滤"脏数据"：前复权回溯到早期的负价 / 零价。
            # 场景：腾讯这类累计除权很重的股票，前复权后 2006 年附近
            # close 会出现负值（见 docs/ 讨论）。这类行不能参与：
            #   - z-score 统计会被拉偏；
            #   - horizon 收益率 c1/c0 符号翻转毫无意义。
            if q.close is None or q.close <= 0:
                dropped_nonpos += 1
                continue
            aligned.append((q, ind))
        if dropped_nonpos:
            _log.info("剔除非正收盘价 K 线 %d 条（前复权回溯溢出）", dropped_nonpos)
        self.aligned = aligned
        self.n = len(aligned)

    # -------------------------------------------------------------------
    # 主入口
    # -------------------------------------------------------------------
    def run(self, horizons: tuple[int, ...] = _DEFAULT_HORIZONS,
            top_k: int = 50) -> Optional[MultiHorizonForecast]:
        if self.n < max(horizons) + 100:
            _log.warning("数据太少（%d 条），回测跳过", self.n)
            return None

        # 1. 构造所有历史日的特征向量
        vectors: list[Optional[list[float]]] = [
            _extract_vector(ind) for _, ind in self.aligned
        ]
        valid_idx = [i for i, v in enumerate(vectors) if v is not None]
        if len(valid_idx) < max(horizons) + 100:
            _log.warning("有效样本太少（%d 条），回测跳过", len(valid_idx))
            return None

        # 2. 归一化：每维求全历史 mean/std，转 z-score
        feat_mean, feat_std = self._compute_feat_stats(vectors, valid_idx)

        # 3. 最后一根 K 线是 "now"；历史样本必须留出 max(horizons) 的未来空间
        now_idx = self.n - 1
        if vectors[now_idx] is None:
            _log.warning("最新 K 线的因子向量缺失，回测跳过")
            return None
        v_now_z = self._zscore(vectors[now_idx], feat_mean, feat_std)

        max_h = max(horizons)
        history_pool = [
            i for i in valid_idx if i <= now_idx - max_h
        ]
        if len(history_pool) < top_k * 2:
            _log.warning("可用历史样本 %d 少于 2×top_k=%d，回测跳过",
                         len(history_pool), 2 * top_k)
            return None

        # 4. 计算距离，取 top_k 最相似日
        dist_list: list[tuple[float, int]] = []
        for i in history_pool:
            v_z = self._zscore(vectors[i], feat_mean, feat_std)
            d = _euclid(v_now_z, v_z)
            dist_list.append((d, i))
        dist_list.sort(key=lambda x: x[0])
        top_similar = dist_list[:top_k]
        top_indices = [i for _, i in top_similar]
        top_dates = [self.aligned[i][0].date for i in top_indices]

        # 5. 每个 horizon 统计未来收益分布
        horizon_result: dict[int, HorizonForecast] = {}
        for h in horizons:
            fc = self._compute_horizon_forecast(top_indices, h, now_idx)
            if fc is not None:
                horizon_result[h] = fc

        # 6. 计算特征贡献度：v_now_z 绝对值 → 哪几个因子"极端"
        contrib: dict[str, float] = {}
        for idx, (_, disp) in enumerate(_FEATURES):
            contrib[disp] = round(abs(v_now_z[idx]), 3)

        return MultiHorizonForecast(
            short=horizon_result.get(5),
            medium=horizon_result.get(20),
            long=horizon_result.get(60),
            top_similar_dates=top_dates[:10],  # 报告里只展示 10 个够用
            feature_contribution=contrib,
        )

    # -------------------------------------------------------------------
    # 内部工具
    # -------------------------------------------------------------------
    @staticmethod
    def _compute_feat_stats(vectors: list[Optional[list[float]]],
                            valid_idx: list[int]
                            ) -> tuple[list[float], list[float]]:
        """按列求均值与标准差。"""
        dim = len(_FEATURES)
        n = len(valid_idx)
        means = [0.0] * dim
        for i in valid_idx:
            v = vectors[i]
            assert v is not None  # noqa: S101  # 由 valid_idx 保证
            for d in range(dim):
                means[d] += v[d]
        means = [m / n for m in means]
        var = [0.0] * dim
        for i in valid_idx:
            v = vectors[i]
            assert v is not None
            for d in range(dim):
                diff = v[d] - means[d]
                var[d] += diff * diff
        stds = [math.sqrt(var[d] / n) if var[d] > 0 else 1.0
                for d in range(dim)]
        return means, stds

    @staticmethod
    def _zscore(v: list[float], mean: list[float],
                std: list[float]) -> list[float]:
        return [(v[d] - mean[d]) / std[d] if std[d] > 0 else 0.0
                for d in range(len(v))]

    def _compute_horizon_forecast(self, indices: list[int], h: int,
                                   now_idx: int) -> Optional[HorizonForecast]:
        """对相似日集合统计 h 日后的收益分布。"""
        rets: list[float] = []
        for i in indices:
            if i + h >= self.n:
                continue
            c0 = self.aligned[i][0].close
            c1 = self.aligned[i + h][0].close
            if c0 <= 0:
                continue
            rets.append(c1 / c0 - 1)
        if not rets:
            return None

        pos = [r for r in rets if r > 0]
        neg = [r for r in rets if r < 0]
        prob_up = len(pos) / len(rets)
        exp_ret = sum(rets) / len(rets)
        avg_pos = sum(pos) / len(pos) if pos else 0.0
        avg_neg = sum(neg) / len(neg) if neg else 0.0

        # 把相似日中最突出的一条写进 reason（用当前因子最"极端"的方向）
        reason = self._build_reason(h, prob_up, exp_ret, len(rets))

        return HorizonForecast(
            horizon_days=h,
            label=self._HORIZON_LABELS.get(h, f"{h}日"),
            prob_up=round(prob_up, 3),
            expected_return=round(exp_ret, 4),
            sample_size=len(rets),
            avg_positive=round(avg_pos, 4),
            avg_negative=round(avg_neg, 4),
            reason=reason,
        )

    @staticmethod
    def _build_reason(h: int, prob_up: float, exp_ret: float,
                      n: int) -> str:
        if prob_up >= 0.6:
            tag = "偏多"
        elif prob_up <= 0.4:
            tag = "偏空"
        else:
            tag = "方向不明"
        return (f"{h}日后: 历史 {n} 个相似态中 {prob_up * 100:.1f}% 上涨，"
                f"平均收益 {exp_ret * 100:+.2f}%，{tag}")


# ===========================================================================
# 纯算数工具
# ===========================================================================

def _euclid(a: list[float], b: list[float]) -> float:
    s = 0.0
    for x, y in zip(a, b):
        diff = x - y
        s += diff * diff
    return math.sqrt(s)
