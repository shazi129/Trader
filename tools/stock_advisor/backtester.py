# -*- coding: utf-8 -*-
"""多周期历史相似态回测。

核心思路
========
"当前特征向量 v_now 在历史上长什么样 → 那些历史日期 N 天后的涨跌" 即为预测。

具体做法（k-NN on z-scored feature vector）：

1. 选一组代表性特征（动量 / 均线比 / RSI / MACD柱 / ATR% / 布林带% ...），
   构成 K 维向量 v。这组特征要求同一时间点都有有效值且数值稳定。
2. 用整段历史序列算每个特征的均值 / 方差，把每一天的 v 归一化成 z 分数。
   ──这样不同量纲的特征能一起算距离。
3. 当前时刻 v_now 对历史每一天 v_hist[t] 求标准化欧氏距离 d[t]；每个 horizon
   只允许使用当时已经拥有未来结果的历史日期，避免未来函数。
4. 取 top_k 个相似日期并使用自适应 Gaussian kernel 按距离赋权；越相似的日期
   对上涨概率和期望收益贡献越大。
5. 用 Kish 有效样本量和“近邻距离相对全样本距离”的质量指标，把原始概率向
   50% 中性先验收缩。
6. 在互不重叠的历史锚点上逐时点重跑上述预测，以 Brier score 相对 50/50
   基准的技能决定该模型能否及以多大权重进入最终融合。

为什么不用 sklearn
------------------
- 项目零三方科学计算依赖（numpy/pandas 都没引），新加 sklearn 成本太大；
- K 维 + N 天的数据量很小（N ≤ 5000, K ≈ 10），纯 Python 算起来毫秒级。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from quantitative.features import FeatureSnapshot
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
    reason: str                 # 相似态摘要
    raw_prob_up: float = 0.5    # 距离加权但尚未收缩的上涨概率
    effective_sample_size: float = 0.0
    mean_distance: float = 0.0
    sample_confidence: float = 0.0
    calibration_samples: int = 0
    calibration_brier: Optional[float] = None
    calibration_skill: float = 0.0
    confidence: float = 0.0     # 进入模型融合的最终可靠性权重


@dataclass
class MultiHorizonForecast:
    """短/中/长期打包。"""
    short: Optional[HorizonForecast]
    medium: Optional[HorizonForecast]
    long: Optional[HorizonForecast]
    top_similar_dates: list[str]  # 命中了哪些历史日期（供报告引用）
    feature_contribution: dict[str, float]  # 特征 z 距离贡献度
    similar_dates_by_horizon: dict[int, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class _NeighborStats:
    probability_up: float
    raw_probability_up: float
    expected_return: float
    average_positive: float
    average_negative: float
    sample_size: int
    effective_sample_size: float
    mean_distance: float
    sample_confidence: float
    indices: tuple[int, ...]


@dataclass(frozen=True)
class _Calibration:
    samples: int = 0
    brier_score: Optional[float] = None
    skill: float = 0.0


# ===========================================================================
# 特征向量构造
# ===========================================================================

# (特征 key, 展示名)：key 必须在 quantitative.features.catalog 中注册。
_FEATURES: tuple[tuple[str, str], ...] = (
    ("rsi_14", "RSI"),
    ("macd_hist", "MACD柱"),
    ("kdj_k", "KDJ_K"),
    ("cci_20", "CCI"),
    ("williams_r_14", "Williams%R"),
    ("momentum_20", "1M动量"),
    ("momentum_63", "3M动量"),
    ("price_to_ma_5", "Price/MA5"),
    ("price_to_ma_20", "Price/MA20"),
    ("price_to_ma_200", "Price/MA200"),
    ("atr_pct_14", "ATR%"),
    ("historical_volatility_20", "20日HV"),
    # 流动性 / 资金面：挑 3 个最能刻画"资金面像谁"的特征
    ("turnover_rate_z_20", "换手率Z20"),
    ("money_flow_strength_20", "资金强度"),
    ("volume_price_corr_20", "量价相关20"),
)


def _extract_vector(ind: FeatureSnapshot) -> Optional[list[float]]:
    """从特征快照取向量；任一特征缺失/nan 返回 None。"""
    vec: list[float] = []
    for attr, _ in _FEATURES:
        v = ind.get(attr)
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

        bt = HorizonBacktester(quotes, features)
        forecast = bt.run(horizons=(5, 20, 60), top_k=50)
    """

    # 历史上这个位置之后要有足够的 future bar 才算"可用样本"
    # 避免用最近几天当历史样本（会出现 future leakage）
    _DEFAULT_HORIZONS = (5, 20, 60)
    _HORIZON_LABELS = {5: "短期(5日)", 20: "中期(20日)", 60: "长期(60日)"}

    def __init__(self, quotes: list[DailyQuote],
                 features: list[FeatureSnapshot]):
        # 按日期对齐行情与特征快照。
        ind_by_date = {snapshot.date: snapshot for snapshot in features if snapshot.date}
        aligned: list[tuple[DailyQuote, FeatureSnapshot]] = []
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

        # 2. 当前时点的归一化统计只使用截至当前的可见数据。
        feat_mean, feat_std = self._compute_feat_stats(vectors, valid_idx)

        # 3. 最后一根 K 线是 "now"；每个周期分别排除尚无未来结果的样本。
        now_idx = self.n - 1
        if vectors[now_idx] is None:
            _log.warning("最新 K 线的特征向量缺失，回测跳过")
            return None
        v_now_z = self._zscore(vectors[now_idx], feat_mean, feat_std)

        # 4. 每个周期分别执行距离加权、概率收缩和逐时点校准。
        horizon_result: dict[int, HorizonForecast] = {}
        dates_by_horizon: dict[int, list[str]] = {}
        for h in horizons:
            stats = self._neighbor_stats(
                vectors,
                valid_idx,
                anchor_idx=now_idx,
                horizon=h,
                top_k=top_k,
                std=feat_std,
            )
            if stats is None:
                continue
            calibration = self._calibrate(
                vectors,
                valid_idx,
                horizon=h,
                top_k=top_k,
                now_idx=now_idx,
            )
            calibration_size_factor = (
                calibration.samples / (calibration.samples + 20.0)
                if calibration.samples
                else 0.0
            )
            confidence = (
                stats.sample_confidence
                * calibration.skill
                * calibration_size_factor
            )
            horizon_result[h] = self._build_horizon_forecast(
                h,
                stats,
                calibration,
                confidence,
            )
            dates_by_horizon[h] = [
                self.aligned[index][0].date for index in stats.indices[:10]
            ]

        if not horizon_result:
            _log.warning("各周期均无足够的历史相似样本，回测跳过")
            return None

        # 5. 计算特征贡献度：v_now_z 绝对值 → 哪些特征更极端
        contrib: dict[str, float] = {}
        for idx, (_, disp) in enumerate(_FEATURES):
            contrib[disp] = round(abs(v_now_z[idx]), 3)

        primary_dates = dates_by_horizon.get(20)
        if primary_dates is None:
            primary_dates = next(iter(dates_by_horizon.values()), [])

        return MultiHorizonForecast(
            short=horizon_result.get(5),
            medium=horizon_result.get(20),
            long=horizon_result.get(60),
            top_similar_dates=primary_dates,
            feature_contribution=contrib,
            similar_dates_by_horizon=dates_by_horizon,
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

    def _neighbor_stats(
        self,
        vectors: list[Optional[list[float]]],
        valid_idx: list[int],
        *,
        anchor_idx: int,
        horizon: int,
        top_k: int,
        std: list[float],
    ) -> Optional[_NeighborStats]:
        """Build a distance-weighted, sample-shrunk forecast at one anchor."""
        anchor = vectors[anchor_idx]
        if anchor is None:
            return None
        history_pool = [
            index for index in valid_idx if index <= anchor_idx - horizon
        ]
        if len(history_pool) < top_k * 2:
            return None

        distances = [
            (_standardized_distance(anchor, vectors[index], std), index)
            for index in history_pool
            if vectors[index] is not None
        ]
        distances.sort(key=lambda item: item[0])
        selected = distances[:top_k]
        if not selected:
            return None
        weights = _kernel_weights([distance for distance, _ in selected])
        total_weight = sum(weights)
        if total_weight <= 0:
            return None

        weighted_returns: list[tuple[float, float]] = []
        for weight, (_, index) in zip(weights, selected):
            start_price = float(self.aligned[index][0].close)
            future_price = float(self.aligned[index + horizon][0].close)
            if start_price <= 0:
                continue
            weighted_returns.append((future_price / start_price - 1.0, weight))
        if not weighted_returns:
            return None

        total_weight = sum(weight for _, weight in weighted_returns)
        raw_probability_up = (
            sum(weight for value, weight in weighted_returns if value > 0)
            / total_weight
        )
        expected_return = sum(
            value * weight for value, weight in weighted_returns
        ) / total_weight
        positive = [(value, weight) for value, weight in weighted_returns if value > 0]
        negative = [(value, weight) for value, weight in weighted_returns if value < 0]
        positive_weight = sum(weight for _, weight in positive)
        negative_weight = sum(weight for _, weight in negative)
        average_positive = (
            sum(value * weight for value, weight in positive)
            / positive_weight
            if positive_weight > 0 else 0.0
        )
        average_negative = (
            sum(value * weight for value, weight in negative)
            / negative_weight
            if negative_weight > 0 else 0.0
        )
        effective_sample_size = (
            total_weight * total_weight
            / sum(weight * weight for _, weight in weighted_returns)
        )
        mean_distance = sum(distance for distance, _ in selected) / len(selected)
        pool_median = distances[len(distances) // 2][0]
        if pool_median <= 1e-12:
            similarity_quality = 1.0 if mean_distance <= 1e-12 else 0.0
        else:
            similarity_quality = max(
                0.0,
                min(1.0, 1.0 - mean_distance / pool_median),
            )
        sample_confidence = (
            effective_sample_size / (effective_sample_size + 20.0)
            * similarity_quality
        )
        probability_up = (
            0.5 + (raw_probability_up - 0.5) * sample_confidence
        )
        return _NeighborStats(
            probability_up=probability_up,
            raw_probability_up=raw_probability_up,
            expected_return=expected_return,
            average_positive=average_positive,
            average_negative=average_negative,
            sample_size=len(weighted_returns),
            effective_sample_size=effective_sample_size,
            mean_distance=mean_distance,
            sample_confidence=sample_confidence,
            indices=tuple(index for _, index in selected),
        )

    def _calibrate(
        self,
        vectors: list[Optional[list[float]]],
        valid_idx: list[int],
        *,
        horizon: int,
        top_k: int,
        now_idx: int,
        max_samples: int = 80,
    ) -> _Calibration:
        """Walk forward over non-overlapping anchors and calculate Brier skill."""
        anchors: list[int] = []
        last_anchor: Optional[int] = None
        for index in reversed(valid_idx):
            if index + horizon > now_idx:
                continue
            if last_anchor is not None and last_anchor - index < horizon:
                continue
            if sum(1 for candidate in valid_idx if candidate <= index - horizon) < top_k * 2:
                continue
            anchors.append(index)
            last_anchor = index
            if len(anchors) >= max_samples:
                break

        squared_errors: list[float] = []
        for anchor_idx in reversed(anchors):
            prefix_valid = [index for index in valid_idx if index <= anchor_idx]
            _, std = self._compute_feat_stats(vectors, prefix_valid)
            stats = self._neighbor_stats(
                vectors,
                prefix_valid,
                anchor_idx=anchor_idx,
                horizon=horizon,
                top_k=top_k,
                std=std,
            )
            if stats is None:
                continue
            actual_up = (
                float(self.aligned[anchor_idx + horizon][0].close)
                > float(self.aligned[anchor_idx][0].close)
            )
            actual = 1.0 if actual_up else 0.0
            squared_errors.append((stats.probability_up - actual) ** 2)

        if not squared_errors:
            return _Calibration()
        brier_score = sum(squared_errors) / len(squared_errors)
        # 0.25 is the Brier score of an uninformative 50/50 forecast.
        skill = max(0.0, min(1.0, 1.0 - brier_score / 0.25))
        return _Calibration(
            samples=len(squared_errors),
            brier_score=brier_score,
            skill=skill,
        )

    def _build_horizon_forecast(
        self,
        horizon: int,
        stats: _NeighborStats,
        calibration: _Calibration,
        confidence: float,
    ) -> HorizonForecast:
        if stats.probability_up >= 0.6:
            tag = "偏多"
        elif stats.probability_up <= 0.4:
            tag = "偏空"
        else:
            tag = "方向不明"
        calibration_text = (
            f"Brier={calibration.brier_score:.3f}, skill={calibration.skill:.1%}"
            if calibration.brier_score is not None
            else "校准样本不足"
        )
        reason = (
            f"{horizon}日后: {stats.sample_size} 个距离加权样本，"
            f"原始上涨概率 {stats.raw_probability_up:.1%}，"
            f"收缩后 {stats.probability_up:.1%}；"
            f"有效样本 {stats.effective_sample_size:.1f}，"
            f"{calibration_text}，融合置信度 {confidence:.1%}，{tag}"
        )
        return HorizonForecast(
            horizon_days=horizon,
            label=self._HORIZON_LABELS.get(horizon, f"{horizon}日"),
            prob_up=round(stats.probability_up, 4),
            expected_return=round(stats.expected_return, 4),
            sample_size=stats.sample_size,
            avg_positive=round(stats.average_positive, 4),
            avg_negative=round(stats.average_negative, 4),
            reason=reason,
            raw_prob_up=round(stats.raw_probability_up, 4),
            effective_sample_size=round(stats.effective_sample_size, 2),
            mean_distance=round(stats.mean_distance, 4),
            sample_confidence=round(stats.sample_confidence, 4),
            calibration_samples=calibration.samples,
            calibration_brier=(
                round(calibration.brier_score, 6)
                if calibration.brier_score is not None else None
            ),
            calibration_skill=round(calibration.skill, 4),
            confidence=round(confidence, 4),
        )


# ===========================================================================
# 纯算数工具
# ===========================================================================

def _standardized_distance(
    current: list[float],
    historical: Optional[list[float]],
    std: list[float],
) -> float:
    if historical is None:
        return float("inf")
    return math.sqrt(sum(
        ((current[index] - historical[index]) / std[index]) ** 2
        if std[index] > 0 else 0.0
        for index in range(len(current))
    ))


def _kernel_weights(distances: list[float]) -> list[float]:
    """Adaptive Gaussian weights; nearer states receive more influence."""
    if not distances:
        return []
    ordered = sorted(distances)
    scale = ordered[len(ordered) // 2]
    if scale <= 1e-12:
        return [1.0 if distance <= 1e-12 else 0.0 for distance in distances]
    return [math.exp(-0.5 * (distance / scale) ** 2) for distance in distances]
