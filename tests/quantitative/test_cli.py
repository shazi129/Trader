"""Command-line contracts for the quantitative adapter."""

from quote_api.stock_meta import all_keys
from quantitative.backtesting import BacktestArtifact, SignalMetric
from quantitative.cli import (
    _render_backtest_results,
    _resolve_backtest_symbols,
    build_parser,
)


def test_backtest_defaults_to_registered_stock_pool():
    args = build_parser().parse_args(["backtest"])

    assert args.stocks is None
    assert _resolve_backtest_symbols(args.stocks) == all_keys()


def test_backtest_explicit_symbols_are_trimmed_and_deduplicated():
    assert _resolve_backtest_symbols("Tencent, Alibaba,Tencent, ") == [
        "Tencent",
        "Alibaba",
    ]


def test_backtest_result_render_includes_rate_samples_and_weight():
    artifact = BacktestArtifact(
        horizons=(5, 20),
        universe=("Tencent",),
        data_cutoff="2026-08-20",
        metrics={
            "test_signal": {
                "5": SignalMetric(100, 60, 0.6, 0.25),
                "20": SignalMetric(80, 44, 0.55, 0.1),
            }
        },
    )

    output = _render_backtest_results(artifact, {"test_signal": "测试形态"})

    assert "测试形态 (`test_signal`)" in output
    assert "60.0% / 100 / 0.250" in output
    assert "55.0% / 80 / 0.100" in output
    assert "截止日: 2026-08-20" in output
