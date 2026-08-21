"""Indicator-pattern detection and directional signals."""

from .base import SignalContext, SignalResult, SignalRule
from .engine import SignalEngine
from .registry import RULE_TYPES

__all__ = ["SignalContext", "SignalEngine", "SignalResult", "SignalRule", "RULE_TYPES"]
