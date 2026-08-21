"""Build a complete feature series from normalized daily quotes."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from quote_api.quote_base import DailyQuote
from quantitative.indicators.liquidity import (
    amihud_illiquidity_series,
    amount_ma,
    amount_ratio,
    illiquidity_rank_series,
    money_flow_strength,
    turnover_rate_ma,
    turnover_rate_zscore,
    vol_price_corr,
)
from quantitative.indicators.momentum import cci, kdj, momentum_pct, rsi, williams_r
from quantitative.indicators.primitives import ema, sma
from quantitative.indicators.risk import (
    historical_volatility_series,
    max_drawdown_series,
    rolling_sharpe_sortino_calmar,
    rolling_skew_kurt,
)
from quantitative.indicators.trend import adx, atr, bollinger, macd
from quantitative.indicators.volume import (
    adl,
    chaikin_oscillator,
    force_index,
    mfi,
    obv,
    vpt,
)

from .catalog import FEATURE_KEYS
from .models import FeatureSnapshot


class FeatureCalculator:
    """Pure feature materializer: quotes in, feature snapshots out."""

    MA_PERIODS = (5, 10, 20, 30, 60, 120, 200, 250)
    MOMENTUM_PERIODS = (5, 10, 20, 63, 126, 189, 252)

    def compute(
        self, symbol: str, quotes: Sequence[DailyQuote]
    ) -> list[FeatureSnapshot]:
        if not quotes:
            return []
        ordered = sorted(quotes, key=lambda quote: quote.date)
        closes = [float(q.close) for q in ordered]
        highs = [float(q.high) for q in ordered]
        lows = [float(q.low) for q in ordered]
        volumes = [float(q.volume) for q in ordered]
        amounts = [float(q.turnover) for q in ordered]
        turnover_rates = [float(getattr(q, "turnover_rate", 0.0)) for q in ordered]
        snapshots = [
            FeatureSnapshot(
                symbol=symbol,
                date=q.date,
                values={key: None for key in FEATURE_KEYS},
            )
            for q in ordered
        ]

        for period in self.MA_PERIODS:
            self._assign(snapshots, f"ma_{period}", sma(closes, period), period - 1)
        self._assign(snapshots, "ma_150", sma(closes, 150), 149)
        self._assign(snapshots, "ma_375", sma(closes, 375), 374)

        self._assign(snapshots, "ema_12", ema(closes, 12), 0)
        self._assign(snapshots, "ema_26", ema(closes, 26), 0)
        self._assign(snapshots, "ema_50", ema(closes, 50), 0)
        for index, snapshot in enumerate(snapshots):
            for period in (5, 10, 20, 60, 200):
                average = snapshot.get(f"ma_{period}")
                if average not in (None, 0):
                    snapshot.values[f"price_to_ma_{period}"] = closes[index] / average
            ma150 = snapshot.get("ma_150")
            ma375 = snapshot.get("ma_375")
            if ma150 not in (None, 0) and ma375 not in (None, 0):
                snapshot.values["ma_150_to_375"] = ma150 / ma375
            if index >= 24 and ma150 not in (None, 0):
                ma25 = sum(closes[index - 24:index + 1]) / 25
                snapshot.values["ma_25_to_150"] = ma25 / ma150

        bands = bollinger(closes, period=20, k=2.0)
        self._assign(snapshots, "boll_middle", bands.middle, 19)
        self._assign(snapshots, "boll_upper", bands.upper, 19)
        self._assign(snapshots, "boll_lower", bands.lower, 19)
        for index, snapshot in enumerate(snapshots):
            middle = snapshot.get("boll_middle")
            upper = snapshot.get("boll_upper")
            lower = snapshot.get("boll_lower")
            if None in (middle, upper, lower) or middle == 0 or upper == lower:
                continue
            snapshot.values["boll_width"] = (upper - lower) / middle
            snapshot.values["boll_percent_b"] = (closes[index] - lower) / (upper - lower)

        macd_result = macd(closes, fast=12, slow=26, signal=9)
        self._assign(snapshots, "macd_dif", macd_result.dif, 0)
        self._assign(snapshots, "macd_dea", macd_result.dea, 0)
        self._assign(snapshots, "macd_hist", macd_result.hist, 0)

        atr_result = atr(highs, lows, closes, period=14)
        self._assign(snapshots, "tr", atr_result.tr, 1)
        self._assign(snapshots, "atr_14", atr_result.atr, 13)
        self._assign(snapshots, "atr_pct_14", atr_result.atr_pct, 13)
        adx_result = adx(highs, lows, closes, period=14)
        self._assign(snapshots, "adx_14", adx_result.adx, 27)
        self._assign(snapshots, "plus_di_14", adx_result.plus_di, 13)
        self._assign(snapshots, "minus_di_14", adx_result.minus_di, 13)

        for period in (6, 12, 14, 24):
            self._assign(
                snapshots,
                f"rsi_{period}",
                rsi(closes, period=period),
                period,
            )
        kdj_result = kdj(highs, lows, closes, period=9)
        self._assign(snapshots, "kdj_k", kdj_result.k, 8)
        self._assign(snapshots, "kdj_d", kdj_result.d, 8)
        self._assign(snapshots, "kdj_j", kdj_result.j, 8)
        for period in self.MOMENTUM_PERIODS:
            self._assign(
                snapshots,
                f"momentum_{period}",
                momentum_pct(closes, period),
                period,
            )
        self._assign(snapshots, "cci_20", cci(highs, lows, closes, 20), 19)
        self._assign(
            snapshots,
            "williams_r_14",
            williams_r(highs, lows, closes, 14),
            13,
        )

        self._assign(snapshots, "obv", obv(closes, volumes), 0)
        self._assign(snapshots, "vpt", vpt(closes, volumes), 1)
        self._assign(snapshots, "adl", adl(highs, lows, closes, volumes), 0)
        self._assign(snapshots, "mfi_14", mfi(highs, lows, closes, volumes, 14), 14)
        for period in (1, 13, 21):
            self._assign(
                snapshots,
                f"force_index_{period}",
                force_index(closes, volumes, period),
                1 if period == 1 else period,
            )
        self._assign(
            snapshots,
            "chaikin_osc",
            chaikin_oscillator(highs, lows, closes, volumes),
            9,
        )
        volume_ma20 = sma(volumes, 20)
        self._assign(snapshots, "volume_ma_20", volume_ma20, 19)
        for index, snapshot in enumerate(snapshots):
            average = snapshot.get("volume_ma_20")
            if average not in (None, 0):
                snapshot.values["volume_ratio_20"] = volumes[index] / average

        hv20 = historical_volatility_series(closes, 20)
        hv60 = historical_volatility_series(closes, 60)
        drawdown = max_drawdown_series(closes)
        sharpe, sortino, calmar = rolling_sharpe_sortino_calmar(
            closes, drawdown, period=252
        )
        skewness, kurtosis = rolling_skew_kurt(closes, period=252)
        self._assign(snapshots, "historical_volatility_20", hv20, 20)
        self._assign(snapshots, "historical_volatility_60", hv60, 60)
        self._assign(snapshots, "max_drawdown", drawdown, 0)
        self._assign(snapshots, "sharpe_252", sharpe, 252)
        self._assign(snapshots, "sortino_252", sortino, 252)
        self._assign(snapshots, "calmar_252", calmar, 252)
        self._assign(snapshots, "skewness_252", skewness, 252)
        self._assign(snapshots, "kurtosis_252", kurtosis, 252)

        liquidity = {
            "turnover_rate": turnover_rates,
            "turnover_rate_ma_5": turnover_rate_ma(turnover_rates, 5),
            "turnover_rate_ma_20": turnover_rate_ma(turnover_rates, 20),
            "turnover_rate_z_20": turnover_rate_zscore(turnover_rates, 20),
            "amount_ma_5": amount_ma(amounts, 5),
            "amount_ma_20": amount_ma(amounts, 20),
            "amount_ratio_5_20": amount_ratio(amounts, 5, 20),
            "amihud_20": amihud_illiquidity_series(closes, amounts, 20),
        }
        liquidity["illiquidity_rank_252"] = illiquidity_rank_series(
            liquidity["amihud_20"], 252
        )
        liquidity["volume_price_corr_20"] = vol_price_corr(closes, amounts, 20)
        liquidity["money_flow_strength_20"] = money_flow_strength(
            closes, amounts, 20
        )
        warmups = {
            "turnover_rate": 0,
            "turnover_rate_ma_5": 4,
            "turnover_rate_ma_20": 19,
            "turnover_rate_z_20": 19,
            "amount_ma_5": 4,
            "amount_ma_20": 19,
            "amount_ratio_5_20": 19,
            "amihud_20": 20,
            "illiquidity_rank_252": 251,
            "volume_price_corr_20": 20,
            "money_flow_strength_20": 20,
        }
        for key, values in liquidity.items():
            self._assign(snapshots, key, values, warmups[key])
        return snapshots

    @staticmethod
    def latest(symbol: str, quotes: Sequence[DailyQuote]) -> FeatureSnapshot | None:
        snapshots = FeatureCalculator().compute(symbol, quotes)
        return snapshots[-1] if snapshots else None

    @staticmethod
    def _assign(
        snapshots: Sequence[FeatureSnapshot],
        key: str,
        values: Iterable[float],
        warmup: int,
    ) -> None:
        for index, value in enumerate(values):
            if index < warmup:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(number):
                continue
            snapshots[index].values[key] = number


__all__ = ["FeatureCalculator"]
