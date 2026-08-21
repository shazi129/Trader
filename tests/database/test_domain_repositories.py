"""Repository and quantitative-pipeline contract tests."""

from __future__ import annotations

import math

import pytest

from financial_reports import FinancialReport, FinancialReportRepository
from quote_api.db_api import DbQuoteAPI
from quote_api.quote_base import DailyQuote
from quote_api.repository import MarketDataRepository
from quantitative.analysis import QuantitativeAnalysisService
from quantitative.analysis.aggregation import aggregate_signals, signal_contributions
from quantitative.backtesting import BacktestArtifactRepository, SignalBacktester
from quantitative.backtesting.models import BacktestArtifact, SignalMetric
from quantitative.features import FeatureCalculator, FeatureRepository
from quantitative.signals import (
    SignalContext,
    SignalEngine,
    SignalResult,
    SignalRule,
)


def quote(day: int, close: float) -> DailyQuote:
    item = DailyQuote()
    item.date = f"2025-{day // 28 + 1:02d}-{day % 28 + 1:02d}"
    item.open = close - 0.5
    item.high = close + 1.0
    item.low = close - 1.0
    item.close = close
    item.volume = 1000 + day * 10
    item.turnover = item.volume * close
    item.turnover_rate = 1.0 + day / 100
    return item


def test_market_data_repository_owns_kline_table(tmp_path):
    path = tmp_path / "trader.db"
    quotes = [quote(1, 10.123456), quote(2, 11.234567)]
    with MarketDataRepository(path) as repository:
        repository.save_many("Example", quotes)
        assert repository.latest_date("Example") == quotes[-1].date
        loaded = repository.get_range("Example")
        assert [item.close for item in loaded] == [10.1235, 11.2346]
        assert repository.count("Example") == 2
        assert repository.list_symbols() == ["Example"]


def test_feature_calculator_and_repository_share_catalog(tmp_path):
    quotes = [quote(index, 100 + index * 0.2 + math.sin(index / 3)) for index in range(90)]
    snapshots = FeatureCalculator().compute("Example", quotes)
    assert len(snapshots) == len(quotes)
    assert snapshots[-1].get("ma_20") is not None
    assert snapshots[-1].get("rsi_14") is not None
    assert snapshots[5].get("ma_20") is None

    with FeatureRepository(tmp_path / "trader.db") as repository:
        repository.save_many(snapshots)
        loaded = repository.get_range("Example")
        assert len(loaded) == len(snapshots)
        assert loaded[-1].get("macd_hist") == pytest.approx(
            snapshots[-1].get("macd_hist"), abs=1e-8
        )


def test_financial_repository_owns_financial_table(tmp_path):
    report = FinancialReport(
        name_key="Example",
        period_end="2025-12-31",
        period_type="ANNUAL",
        announce_date="2026-03-01",
        currency="CNY",
        audited=True,
        source="test",
        source_file="example.pdf",
        fields={"Revenue": 123.0, "NetIncomeAttr": 20.0},
    )
    with FinancialReportRepository(tmp_path / "trader.db") as repository:
        repository.save(report)
        rows = repository.get_reports("Example")
        assert rows[0]["Revenue"] == 123.0
        assert repository.latest_period("Example") == "2025-12-31"

        # A partial re-parse updates supplied fields without erasing previously
        # extracted values from the same reporting period.
        repository.save(FinancialReport(
            name_key="Example",
            period_end="2025-12-31",
            period_type="ANNUAL",
            announce_date="2026-03-01",
            currency="CNY",
            audited=True,
            source="test",
            source_file="example.pdf",
            fields={"NetIncomeAttr": 25.0},
        ))
        updated = repository.get_reports("Example")[0]
        assert updated["Revenue"] == 123.0
        assert updated["NetIncomeAttr"] == 25.0


def test_signal_engine_has_stable_explicit_registry():
    quotes = [quote(index, 100 + index) for index in range(90)]
    features = FeatureCalculator().compute("Example", quotes)
    signals = SignalEngine().evaluate(SignalContext("Example", quotes, features))
    ids = [signal.signal_id for signal in signals]
    assert len(ids) == len(set(ids))
    assert "ma_alignment_bullish" in ids
    assert "ma_5_20_golden_cross" in ids


def test_aggregation_ignores_inactive_signals_and_respects_direction():
    artifact = BacktestArtifact(
        baselines={"Example": {"20": 0.55}},
        pooled_baselines={"20": 0.5},
        metrics={
            "bull": {"20": SignalMetric(
                100, 65, 0.65, 0.2,
                baseline_success_rate=0.55,
                excess_success_rate=0.10,
                direction_multiplier=1,
            )},
            "bear": {"20": SignalMetric(
                100, 65, 0.65, 0.2,
                baseline_success_rate=0.45,
                excess_success_rate=0.20,
                direction_multiplier=1,
            )},
        },
    )
    inactive = SignalResult("inactive", "inactive", "x", False, 0)
    bullish = SignalResult("bull", "bull", "x", True, 1)
    result = aggregate_signals(
        [inactive, bullish], artifact, horizons=(20,), symbol="Example"
    )[20]
    assert result.probability_up == 0.65
    assert result.baseline_probability_up == 0.55

    bearish = SignalResult("bear", "bear", "x", True, -1)
    result = aggregate_signals(
        [bearish], artifact, horizons=(20,), symbol="Example"
    )[20]
    assert result.probability_up == 0.35


def test_signal_contributions_only_reverse_when_artifact_validated_it():
    artifact = BacktestArtifact(
        pooled_baselines={"20": 0.5},
        metrics={
            "unvalidated": {"20": SignalMetric(
                100, 40, 0.4, 0.0,
                baseline_success_rate=0.5,
                excess_success_rate=-0.1,
                direction_multiplier=0,
            )},
            "validated": {"20": SignalMetric(
                100, 40, 0.4, 0.2,
                baseline_success_rate=0.5,
                excess_success_rate=-0.1,
                direction_multiplier=-1,
                oos_samples=30,
                oos_excess_success_rate=0.12,
                oos_positive_folds=3,
                oos_total_folds=3,
            )},
        },
    )
    unvalidated = SignalResult(
        "unvalidated", "unvalidated", "test", True, -1
    )
    validated = SignalResult("validated", "validated", "test", True, -1)

    assert signal_contributions([unvalidated], artifact, 20) == []
    contributions = signal_contributions([validated], artifact, 20)

    assert len(contributions) == 1
    assert contributions[0].effective_probability_up == pytest.approx(0.6)
    assert contributions[0].weight_share == pytest.approx(1.0)
    assert contributions[0].is_reversed
    assert contributions[0].effective_direction_text == "有效看多"


def test_signal_backtest_requires_edge_over_symbol_baseline():
    class AlwaysBullish(SignalRule):
        signal_id = "always_bullish"
        name = "Always bullish"
        category = "test"

        def evaluate(self, context):
            return self.result(True, 1)

    quotes = [
        quote(index, 100 if index % 2 == 0 else 110)
        for index in range(80)
    ]
    artifact = SignalBacktester(
        engine=SignalEngine([AlwaysBullish()]),
        horizons=(1,),
        min_history=5,
    ).run({"Example": quotes})
    metric = artifact.metric("always_bullish", 1)

    assert metric is not None
    assert metric.success_rate == pytest.approx(
        artifact.baseline_probability_up("Example", 1)
    )
    assert metric.direction_multiplier == 0
    assert metric.weight == 0.0


def test_signal_backtest_validates_reverse_direction_walk_forward():
    class BearishAtTheLow(SignalRule):
        signal_id = "bearish_at_low"
        name = "Bearish at the low"
        category = "test"

        def evaluate(self, context):
            return self.result(context.anchor_price < 105, -1)

    quotes = [
        quote(index, 100 if index % 2 == 0 else 110)
        for index in range(120)
    ]
    artifact = SignalBacktester(
        engine=SignalEngine([BearishAtTheLow()]),
        horizons=(1,),
        min_history=5,
    ).run({"Example": quotes})
    metric = artifact.metric("bearish_at_low", 1)

    assert metric is not None
    assert metric.success_rate == 0.0
    assert metric.direction_multiplier == -1
    assert metric.weight > 0
    assert metric.oos_positive_folds >= 2
    assert metric.oos_z_score > 0


def test_divergence_backtest_counts_one_continuous_window_as_one_event():
    class ContinuousDivergence(SignalRule):
        signal_id = "continuous_divergence"
        name = "Continuous divergence"
        category = "divergence"

        def evaluate(self, context):
            return self.result(True, -1)

    quotes = [
        quote(index, 100 if index % 2 == 0 else 110)
        for index in range(80)
    ]
    artifact = SignalBacktester(
        engine=SignalEngine([ContinuousDivergence()]),
        horizons=(1,),
        min_history=5,
    ).run({"Example": quotes})
    metric = artifact.metric("continuous_divergence", 1)

    assert metric is not None
    assert metric.samples == 1
    assert metric.weight == 0.0


def test_quantitative_analysis_service_runs_end_to_end(tmp_path):
    path = tmp_path / "trader.db"
    quotes = [
        quote(index, 100 + index * 0.2 + math.sin(index / 3))
        for index in range(90)
    ]
    repository = MarketDataRepository(path)
    repository.save_many("Example", quotes)
    api = DbQuoteAPI(repository=repository)
    service = QuantitativeAnalysisService(
        api,
        artifact_repository=BacktestArtifactRepository(
            tmp_path / "signal_statistics.json"
        ),
    )

    report = service.analyze("Example", anchor_date=quotes[-1].date)

    assert report is not None
    assert report.anchor_date == quotes[-1].date
    assert set(report.horizons) == {5, 20, 60}
    assert report.summary.startswith("[量化分析]")

    # The repository was injected, so the API must not take ownership of it.
    api.close()
    assert repository.count("Example") == len(quotes)
    repository.close()
