"""Orchestrate market data, features, signals, statistics, and reporting."""

from __future__ import annotations

from collections.abc import Sequence

from quote_api.quote_base import DailyQuote, QuoteAPI
from quote_api.stock_meta import get_meta
from quantitative.backtesting import BacktestArtifactRepository
from quantitative.features import FeatureCalculator, FeatureRepository
from quantitative.signals import SignalContext, SignalEngine

from .aggregation import aggregate_signals
from .models import QuantitativeReport
from .report import render_summary


class QuantitativeAnalysisService:
    """The sole application-level orchestrator for quantitative analysis."""

    def __init__(
        self,
        quote_api: QuoteAPI,
        *,
        feature_repository: FeatureRepository | None = None,
        artifact_repository: BacktestArtifactRepository | None = None,
        calculator: FeatureCalculator | None = None,
        signal_engine: SignalEngine | None = None,
    ) -> None:
        self.quote_api = quote_api
        self.feature_repository = feature_repository
        self.artifact_repository = artifact_repository or BacktestArtifactRepository()
        self.calculator = calculator or FeatureCalculator()
        self.signal_engine = signal_engine or SignalEngine()

    def analyze(
        self,
        symbol: str,
        *,
        anchor_date: str | None = None,
        lookback: int = 500,
    ) -> QuantitativeReport | None:
        quotes = self.quote_api.get_klines(
            symbol, end_date=anchor_date, limit=lookback
        )
        return self.analyze_quotes(symbol, quotes, anchor_date=anchor_date)

    def analyze_quotes(
        self,
        symbol: str,
        quotes: Sequence[DailyQuote],
        *,
        anchor_date: str | None = None,
        persist_features: bool = False,
    ) -> QuantitativeReport | None:
        ordered = sorted(quotes, key=lambda quote: quote.date)
        if anchor_date:
            ordered = [quote for quote in ordered if quote.date <= anchor_date]
        if not ordered:
            return None
        features = self.calculator.compute(symbol, ordered)
        if persist_features and self.feature_repository is not None:
            self.feature_repository.save_many(features)
        context = SignalContext(symbol=symbol, quotes=ordered, features=features)
        signals = self.signal_engine.evaluate(context)
        artifact = self.artifact_repository.load()
        meta = get_meta(symbol)
        report = QuantitativeReport(
            symbol=symbol,
            name=meta.name if meta else symbol,
            anchor_date=ordered[-1].date,
            anchor_price=float(ordered[-1].close),
            data_source=getattr(self.quote_api, "SOURCE", "unknown"),
            data_days=len(ordered),
            signals=signals,
            horizons=aggregate_signals(signals, artifact, symbol=symbol),
        )
        report.summary = render_summary(report)
        return report

    def materialize(self, symbol: str, quotes: Sequence[DailyQuote]) -> int:
        if self.feature_repository is None:
            raise RuntimeError("feature_repository is required for materialization")
        features = self.calculator.compute(symbol, quotes)
        self.feature_repository.save_many(features)
        return len(features)


__all__ = ["QuantitativeAnalysisService"]
