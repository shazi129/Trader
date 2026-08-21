"""Pure signal evaluation engine."""

from __future__ import annotations

from collections.abc import Iterable

from utils.logger import get_logger

from .base import SignalContext, SignalResult, SignalRule
from .registry import RULE_TYPES

_log = get_logger(__name__)


class SignalEngine:
    def __init__(self, rules: Iterable[SignalRule] | None = None) -> None:
        self.rules = list(rules) if rules is not None else [rule() for rule in RULE_TYPES]

    def evaluate(self, context: SignalContext) -> list[SignalResult]:
        results: list[SignalResult] = []
        for rule in self.rules:
            try:
                results.append(rule.evaluate(context))
            except Exception as exc:  # one rule must not break an analysis
                _log.warning("signal %s failed: %s", rule.signal_id, exc)
        return results


__all__ = ["SignalEngine"]
