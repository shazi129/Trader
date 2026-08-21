"""Offline data-loading contracts for stock_advisor."""

from quote_api.quote_base import DailyQuote
from quote_api.repository import MarketDataRepository
from quantitative.analysis.models import HorizonAnalysis, QuantitativeReport
from quantitative.backtesting.models import BacktestArtifact, SignalMetric
from quantitative.signals import SignalResult
from tools.stock_advisor.backtester import HorizonForecast, MultiHorizonForecast
from tools.stock_advisor.fusion import fuse_forecasts
from tools.stock_advisor.stock_advisor import _build_markdown, _load_or_build


def _quote(index: int) -> DailyQuote:
    quote = DailyQuote()
    quote.date = f"2025-{index // 28 + 1:02d}-{index % 28 + 1:02d}"
    quote.open = 100 + index
    quote.close = 100.5 + index
    quote.high = 101 + index
    quote.low = 99 + index
    quote.volume = 1000 + index
    quote.turnover = quote.volume * quote.close
    quote.turnover_rate = 1.0
    return quote


def test_load_or_build_materializes_features_from_local_quotes(tmp_path):
    db_path = tmp_path / "trader.db"
    source_quotes = [_quote(index) for index in range(90)]
    with MarketDataRepository(db_path) as repository:
        repository.save_many("Example", source_quotes)

    quotes, features = _load_or_build("Example", str(db_path))

    assert len(quotes) == len(source_quotes)
    assert len(features) == len(source_quotes)
    assert features[-1].date == quotes[-1].date


def test_load_or_build_does_not_fetch_when_local_quotes_are_missing(tmp_path):
    quotes, features = _load_or_build("Example", str(tmp_path / "empty.db"))

    assert quotes == []
    assert features == []


def test_report_groups_active_bullish_and_bearish_signals():
    report = QuantitativeReport(
        symbol="Example",
        name="示例股票",
        anchor_date="2025-01-02",
        anchor_price=100.0,
        data_source="db",
        data_days=200,
        signals=[
            SignalResult(
                "bull",
                "RSI离开超卖区",
                "reversal",
                True,
                1,
                description="RSI向上穿越30",
            ),
            SignalResult(
                "bear",
                "MACD死叉",
                "crossover",
                True,
                -1,
                description="DIF向下穿越DEA",
            ),
            SignalResult(
                "inactive",
                "未触发形态",
                "test",
                False,
                0,
            ),
        ],
        horizons={20: HorizonAnalysis(20, 0.60, 0.40, 0.1, 2, 0.5)},
    )
    artifact = BacktestArtifact(
        universe=("Example",),
        data_cutoff="2025-01-01",
        baselines={"Example": {"20": 0.5}},
        pooled_baselines={"20": 0.5},
        metrics={
            "bull": {"20": SignalMetric(
                1_000_000, 600_000, 0.6, 0.4,
                baseline_success_rate=0.5,
                excess_success_rate=0.1,
                direction_multiplier=1,
            )},
            "bear": {"20": SignalMetric(
                1_000_000, 400_000, 0.4, 0.6,
                baseline_success_rate=0.5,
                excess_success_rate=-0.1,
                direction_multiplier=-1,
                oos_samples=10_000,
                oos_excess_success_rate=0.1,
                oos_positive_folds=3,
                oos_total_folds=3,
            )},
        },
    )
    forecast = MultiHorizonForecast(
        short=None,
        medium=HorizonForecast(
            horizon_days=20,
            label="中期(20日)",
            prob_up=0.30,
            expected_return=-0.01,
            sample_size=50,
            avg_positive=0.05,
            avg_negative=-0.03,
            reason="历史相似态偏空",
            raw_prob_up=0.25,
            effective_sample_size=40.0,
            calibration_samples=40,
            calibration_brier=0.20,
            calibration_skill=0.20,
            confidence=0.20,
        ),
        long=None,
        top_similar_dates=[],
        feature_contribution={},
    )
    fused = fuse_forecasts(report, forecast)

    markdown = _build_markdown(
        report,
        forecast,
        "Example",
        signal_artifact=artifact,
        fused_forecast=fused,
    )

    assert "当前触发：**看多 1 个 / 看空 1 个**" in markdown
    assert "### 3.1 看多指标形态（1）" in markdown
    assert "| RSI离开超卖区 | `reversal` | RSI向上穿越30 |" in markdown
    assert "### 3.2 看空指标形态（1）" in markdown
    assert "| MACD死叉 | `crossover` | DIF向下穿越DEA |" in markdown
    assert "### 3.3 回测后的有效方向与概率贡献" in markdown
    assert "**有效看多（反向）**" in markdown
    assert "只有单侧 95% 显著优于基准时才获得权重" in markdown
    assert "命中率低于基准不会自动反转" in markdown
    assert "60.0% / 50.0%" in markdown
    assert "因此上涨概率为 **60.0%**" in markdown
    assert "### 1.1 综合概率（可靠性加权融合）" in markdown
    assert "| [-] 20日 | **40.0%** | 60.0% | 偏空" in markdown
    assert "### 两个子模型对照" in markdown
    assert "| 20日 | 60.0%（偏多） | 30.0%（偏空） | +30.0 个百分点 | **方向相反** |" in markdown
    assert "未触发形态" not in markdown
