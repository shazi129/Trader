"""Unit tests for indicator-pattern rules built from existing features."""

from __future__ import annotations

import pytest

from quote_api.quote_base import DailyQuote
from quantitative.features.models import FeatureSnapshot
from quantitative.signals import RULE_TYPES, SignalContext


RULES = {rule.signal_id: rule() for rule in RULE_TYPES}


def _context(
    values: list[dict[str, float | None]],
    closes: list[float] | None = None,
) -> SignalContext:
    closes = closes or [100.0] * len(values)
    quotes: list[DailyQuote] = []
    features: list[FeatureSnapshot] = []
    for index, (close, snapshot_values) in enumerate(zip(closes, values)):
        quote = DailyQuote()
        quote.date = f"2025-{index // 28 + 1:02d}-{index % 28 + 1:02d}"
        quote.open = close
        quote.high = close + 1.0
        quote.low = close - 1.0
        quote.close = close
        quote.volume = 1_000.0
        quotes.append(quote)
        features.append(
            FeatureSnapshot("Example", quote.date, dict(snapshot_values))
        )
    return SignalContext("Example", quotes, features)


@pytest.mark.parametrize(
    ("signal_id", "previous", "current", "direction"),
    (
        ("price_ma_20_cross_up", {"price_to_ma_20": 0.99}, {"price_to_ma_20": 1.01}, 1),
        ("price_ma_20_cross_down", {"price_to_ma_20": 1.01}, {"price_to_ma_20": 0.99}, -1),
        ("ma_60_200_golden_cross", {"ma_60": 99, "ma_200": 100}, {"ma_60": 101, "ma_200": 100}, 1),
        ("ma_60_200_death_cross", {"ma_60": 101, "ma_200": 100}, {"ma_60": 99, "ma_200": 100}, -1),
        ("macd_zero_cross_up", {"macd_dif": -0.1}, {"macd_dif": 0.1}, 1),
        ("macd_zero_cross_down", {"macd_dif": 0.1}, {"macd_dif": -0.1}, -1),
        ("kdj_oversold_golden_cross", {"kdj_k": 18, "kdj_d": 19}, {"kdj_k": 22, "kdj_d": 20}, 1),
        ("kdj_overbought_death_cross", {"kdj_k": 82, "kdj_d": 81}, {"kdj_k": 78, "kdj_d": 80}, -1),
        ("rsi_14_oversold_exit", {"rsi_14": 29}, {"rsi_14": 31}, 1),
        ("rsi_14_overbought_exit", {"rsi_14": 71}, {"rsi_14": 69}, -1),
        ("mfi_14_oversold_exit", {"mfi_14": 19}, {"mfi_14": 21}, 1),
        ("mfi_14_overbought_exit", {"mfi_14": 81}, {"mfi_14": 79}, -1),
        ("cci_20_breakout_up", {"cci_20": 99}, {"cci_20": 101}, 1),
        ("cci_20_breakout_down", {"cci_20": -99}, {"cci_20": -101}, -1),
        ("cci_20_oversold_exit", {"cci_20": -101}, {"cci_20": -99}, 1),
        ("cci_20_overbought_exit", {"cci_20": 101}, {"cci_20": 99}, -1),
        ("williams_r_14_oversold_exit", {"williams_r_14": -81}, {"williams_r_14": -79}, 1),
        ("williams_r_14_overbought_exit", {"williams_r_14": -19}, {"williams_r_14": -21}, -1),
    ),
)
def test_two_bar_event_rules_trigger(
    signal_id: str,
    previous: dict[str, float],
    current: dict[str, float],
    direction: int,
):
    result = RULES[signal_id].evaluate(_context([previous, current]))
    assert result.active
    assert result.direction == direction


@pytest.mark.parametrize(
    ("signal_id", "previous", "current"),
    (
        ("rsi_14_oversold_exit", {"rsi_14": 31}, {"rsi_14": 35}),
        ("mfi_14_overbought_exit", {"mfi_14": 79}, {"mfi_14": 75}),
        ("cci_20_breakout_up", {"cci_20": 101}, {"cci_20": 110}),
        ("price_ma_20_cross_down", {"price_to_ma_20": 0.99}, {"price_to_ma_20": 0.98}),
    ),
)
def test_event_rules_do_not_remain_active(
    signal_id: str,
    previous: dict[str, float],
    current: dict[str, float],
):
    result = RULES[signal_id].evaluate(_context([previous, current]))
    assert not result.active
    assert result.direction == 0


@pytest.mark.parametrize(
    ("signal_id", "previous", "current", "direction"),
    (
        (
            "dmi_bullish_cross",
            {"plus_di_14": 18, "minus_di_14": 20, "adx_14": 24 * 14},
            {"plus_di_14": 23, "minus_di_14": 19, "adx_14": 26 * 14},
            1,
        ),
        (
            "dmi_bearish_cross",
            {"plus_di_14": 20, "minus_di_14": 18, "adx_14": 25 * 14},
            {"plus_di_14": 19, "minus_di_14": 23, "adx_14": 27 * 14},
            -1,
        ),
    ),
)
def test_dmi_cross_requires_adx_confirmation(
    signal_id: str,
    previous: dict[str, float],
    current: dict[str, float],
    direction: int,
):
    result = RULES[signal_id].evaluate(_context([previous, current]))
    assert result.active
    assert result.direction == direction

    current["adx_14"] = 20 * 14
    assert not RULES[signal_id].evaluate(_context([previous, current])).active


@pytest.mark.parametrize(
    ("signal_id", "histogram", "direction"),
    (
        ("macd_hist_bullish_reexpand", [0.4, 0.2, 0.3], 1),
        ("macd_hist_bearish_reexpand", [-0.4, -0.2, -0.3], -1),
    ),
)
def test_macd_histogram_reexpansion(
    signal_id: str,
    histogram: list[float],
    direction: int,
):
    context = _context([{"macd_hist": value} for value in histogram])
    result = RULES[signal_id].evaluate(context)
    assert result.active
    assert result.direction == direction


@pytest.mark.parametrize(
    ("signal_id", "band_key", "previous_close", "current_close", "direction"),
    (
        ("bollinger_squeeze_breakout_up", "boll_upper", 100.0, 103.0, 1),
        ("bollinger_squeeze_breakout_down", "boll_lower", 100.0, 97.0, -1),
    ),
)
def test_bollinger_squeeze_breakout_uses_prior_low_bandwidth(
    signal_id: str,
    band_key: str,
    previous_close: float,
    current_close: float,
    direction: int,
):
    values = [
        {"boll_width": 0.10, "boll_upper": 101.0, "boll_lower": 99.0}
        for _ in range(23)
    ]
    values[-2]["boll_width"] = 0.05
    values[-1]["boll_width"] = 0.08
    values[-1][band_key] = 102.0 if direction > 0 else 98.0
    closes = [100.0] * 21 + [previous_close, current_close]
    result = RULES[signal_id].evaluate(_context(values, closes))
    assert result.active
    assert result.direction == direction


@pytest.mark.parametrize(
    ("signal_id", "band_key", "closes", "direction"),
    (
        ("bollinger_lower_reentry", "boll_lower", [97.0, 100.0], 1),
        ("bollinger_upper_reentry", "boll_upper", [103.0, 100.0], -1),
    ),
)
def test_bollinger_false_breakout_reentry(
    signal_id: str,
    band_key: str,
    closes: list[float],
    direction: int,
):
    level = 98.0 if direction > 0 else 102.0
    values = [{band_key: level}, {band_key: level}]
    result = RULES[signal_id].evaluate(_context(values, closes))
    assert result.active
    assert result.direction == direction


def _bottom_prices() -> list[float]:
    return [
        110, 108, 106, 104, 102, 100, 98, 96, 90, 96, 98,
        100, 102, 104, 106, 108, 106, 104, 102, 100, 98, 96,
        94, 85, 94, 96, 98, 100, 102, 104, 106, 108,
    ]


@pytest.mark.parametrize(
    ("signal_id", "feature_key"),
    (
        ("rsi_bottom_divergence", "rsi_14"),
        ("mfi_bottom_divergence", "mfi_14"),
        ("obv_bottom_divergence", "obv"),
    ),
)
def test_indicator_bottom_divergence(signal_id: str, feature_key: str):
    closes = _bottom_prices()
    indicator = [50.0] * len(closes)
    indicator[8] = 20.0
    indicator[23] = 30.0
    values = [{feature_key: value} for value in indicator]
    result = RULES[signal_id].evaluate(_context(values, closes))
    assert result.active
    assert result.direction == 1


@pytest.mark.parametrize(
    ("signal_id", "feature_key"),
    (
        ("rsi_top_divergence", "rsi_14"),
        ("mfi_top_divergence", "mfi_14"),
        ("obv_top_divergence", "obv"),
    ),
)
def test_indicator_top_divergence(signal_id: str, feature_key: str):
    closes = [200.0 - value for value in _bottom_prices()]
    indicator = [50.0] * len(closes)
    indicator[8] = 80.0
    indicator[23] = 70.0
    values = [{feature_key: value} for value in indicator]
    result = RULES[signal_id].evaluate(_context(values, closes))
    assert result.active
    assert result.direction == -1


@pytest.mark.parametrize(
    ("signal_id", "momentum", "volume_ratio"),
    (
        ("bearish_price_volume_divergence", 3.0, 0.7),
        ("bearish_volume_expansion", -3.0, 1.3),
    ),
)
def test_bearish_volume_patterns(
    signal_id: str,
    momentum: float,
    volume_ratio: float,
):
    context = _context([
        {"momentum_5": momentum, "volume_ratio_20": volume_ratio}
    ])
    result = RULES[signal_id].evaluate(context)
    assert result.active
    assert result.direction == -1


def test_registry_is_unique_and_all_rules_tolerate_missing_warmup_data():
    assert len(RULE_TYPES) == 52
    assert len(RULES) == len(RULE_TYPES)
    empty_context = _context([{}])
    for rule in RULES.values():
        result = rule.evaluate(empty_context)
        assert not result.active, rule.signal_id
        assert result.direction == 0, rule.signal_id
