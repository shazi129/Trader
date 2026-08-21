"""Explicit signal registry.

Filesystem auto-discovery is intentionally avoided: registration order is
stable, duplicate IDs fail fast, and importing research scripts has no side
effects.
"""

from __future__ import annotations

from .momentum import NegativeMomentum, PositiveMomentum, RSIOverbought, RSIOversold
from .patterns import DoubleBottom, DoubleTop, MACDBottomDivergence, MACDTopDivergence
from .trend import (
    BearishMAAlignment,
    BollingerLowerTouch,
    BollingerUpperTouch,
    BullishMAAlignment,
    MACDDeathCross,
    MACDGoldenCross,
    MADeathCross,
    MAGoldenCross,
)
from .volume_risk import VolatilityContraction, VolumeExpansion

RULE_TYPES = (
    BullishMAAlignment,
    BearishMAAlignment,
    MAGoldenCross,
    MADeathCross,
    MACDGoldenCross,
    MACDDeathCross,
    BollingerLowerTouch,
    BollingerUpperTouch,
    RSIOversold,
    RSIOverbought,
    PositiveMomentum,
    NegativeMomentum,
    VolumeExpansion,
    VolatilityContraction,
    MACDTopDivergence,
    MACDBottomDivergence,
    DoubleTop,
    DoubleBottom,
)

_ids = [rule.signal_id for rule in RULE_TYPES]
if len(_ids) != len(set(_ids)):
    raise RuntimeError("duplicate signal_id in RULE_TYPES")

__all__ = ["RULE_TYPES"]
