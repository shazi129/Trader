"""Contracts for similarity weighting, calibration, and model fusion."""

from __future__ import annotations

import datetime
import math

from quote_api.quote_base import DailyQuote
from quantitative.analysis.models import HorizonAnalysis, QuantitativeReport
from quantitative.features.models import FeatureSnapshot
from tools.stock_advisor.backtester import (
    _FEATURES,
    HorizonBacktester,
    _kernel_weights,
)
from tools.stock_advisor.fusion import fuse_forecasts


def _series(size: int = 260):
    start = datetime.date(2024, 1, 1)
    quotes: list[DailyQuote] = []
    features: list[FeatureSnapshot] = []
    for index in range(size):
        phase = 2.0 * math.pi * (index % 30) / 30.0
        close = 100.0 + index * 0.01 + 5.0 * math.sin(phase)
        quote = DailyQuote()
        quote.date = str(start + datetime.timedelta(days=index))
        quote.open = close
        quote.high = close + 1.0
        quote.low = close - 1.0
        quote.close = close
        quote.volume = 1_000.0
        quotes.append(quote)
        values = {
            key: math.sin(phase + dimension * 0.07)
            for dimension, (key, _) in enumerate(_FEATURES)
        }
        features.append(FeatureSnapshot("Example", quote.date, values))
    return quotes, features


def test_kernel_weights_favor_nearer_states():
    weights = _kernel_weights([0.5, 1.0, 2.0])
    assert weights[0] > weights[1] > weights[2] > 0.0


def test_similarity_forecast_is_weighted_shrunk_calibrated_and_point_in_time():
    quotes, features = _series()
    forecast = HorizonBacktester(quotes, features).run(
        horizons=(5, 20),
        top_k=10,
    )

    assert forecast is not None
    assert forecast.short is not None
    assert forecast.medium is not None
    for item in (forecast.short, forecast.medium):
        assert item.sample_size == 10
        assert 0.0 <= item.raw_prob_up <= 1.0
        assert 0.0 <= item.prob_up <= 1.0
        assert 0.0 < item.effective_sample_size <= item.sample_size
        assert item.calibration_samples > 0
        assert item.calibration_brier is not None
        assert 0.0 <= item.calibration_skill <= 1.0
        assert 0.0 <= item.confidence <= 1.0

        latest_allowed = quotes[-1 - item.horizon_days].date
        assert all(
            date <= latest_allowed
            for date in forecast.similar_dates_by_horizon[item.horizon_days]
        )


def test_fusion_ignores_similarity_without_positive_calibration_weight():
    quotes, features = _series()
    similarity = HorizonBacktester(quotes, features).run(
        horizons=(20,),
        top_k=10,
    )
    assert similarity is not None and similarity.medium is not None
    similarity.medium.confidence = 0.0
    report = QuantitativeReport(
        symbol="Example",
        name="Example",
        anchor_date=quotes[-1].date,
        anchor_price=quotes[-1].close,
        data_source="db",
        data_days=len(quotes),
        horizons={20: HorizonAnalysis(20, 0.58, 0.42, 0.2, 3)},
    )

    fused = fuse_forecasts(report, similarity).get(20)

    assert fused is not None
    assert fused.probability_up == 0.58
    assert fused.signal_weight_share == 1.0
    assert fused.similarity_weight_share == 0.0
