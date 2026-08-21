"""Explicit signal registry.

Filesystem auto-discovery is intentionally avoided: registration order is
stable, duplicate IDs fail fast, and importing research scripts has no side
effects.
"""

from __future__ import annotations

from .momentum import (
    CCIOverboughtExit,
    CCIOversoldExit,
    CCITrendBreakoutDown,
    CCITrendBreakoutUp,
    KDJOverboughtDeathCross,
    KDJOversoldGoldenCross,
    MFIOverboughtExit,
    MFIOversoldExit,
    NegativeMomentum,
    PositiveMomentum,
    RSIOverbought,
    RSIOverboughtExit,
    RSIOversold,
    RSIOversoldExit,
    WilliamsROverboughtExit,
    WilliamsROversoldExit,
)
from .patterns import (
    DoubleBottom,
    DoubleTop,
    MACDBottomDivergence,
    MACDTopDivergence,
    MFIBottomDivergence,
    MFITopDivergence,
    OBVBottomDivergence,
    OBVTopDivergence,
    RSIBottomDivergence,
    RSITopDivergence,
)
from .trend import (
    BearishMAAlignment,
    BollingerLowerReentry,
    BollingerLowerTouch,
    BollingerSqueezeBreakoutDown,
    BollingerSqueezeBreakoutUp,
    BollingerUpperReentry,
    BollingerUpperTouch,
    BullishMAAlignment,
    DMIBearishCross,
    DMIBullishCross,
    MACDBearishHistogramReexpand,
    MACDBullishHistogramReexpand,
    MACDDeathCross,
    MACDGoldenCross,
    MACDZeroCrossDown,
    MACDZeroCrossUp,
    MADeathCross,
    MAGoldenCross,
    MALongTermDeathCross,
    MALongTermGoldenCross,
    PriceMA20CrossDown,
    PriceMA20CrossUp,
)
from .volume_risk import (
    BearishPriceVolumeDivergence,
    BearishVolumeExpansion,
    VolatilityContraction,
    VolumeExpansion,
)

RULE_TYPES = (
    BullishMAAlignment,
    BearishMAAlignment,
    MAGoldenCross,
    MADeathCross,
    PriceMA20CrossUp,
    PriceMA20CrossDown,
    MALongTermGoldenCross,
    MALongTermDeathCross,
    MACDGoldenCross,
    MACDDeathCross,
    MACDZeroCrossUp,
    MACDZeroCrossDown,
    MACDBullishHistogramReexpand,
    MACDBearishHistogramReexpand,
    DMIBullishCross,
    DMIBearishCross,
    BollingerLowerTouch,
    BollingerUpperTouch,
    BollingerSqueezeBreakoutUp,
    BollingerSqueezeBreakoutDown,
    BollingerLowerReentry,
    BollingerUpperReentry,
    RSIOversold,
    RSIOverbought,
    RSIOversoldExit,
    RSIOverboughtExit,
    KDJOversoldGoldenCross,
    KDJOverboughtDeathCross,
    PositiveMomentum,
    NegativeMomentum,
    CCITrendBreakoutUp,
    CCITrendBreakoutDown,
    CCIOversoldExit,
    CCIOverboughtExit,
    WilliamsROversoldExit,
    WilliamsROverboughtExit,
    MFIOversoldExit,
    MFIOverboughtExit,
    VolumeExpansion,
    BearishVolumeExpansion,
    BearishPriceVolumeDivergence,
    VolatilityContraction,
    MACDTopDivergence,
    MACDBottomDivergence,
    RSITopDivergence,
    RSIBottomDivergence,
    MFITopDivergence,
    MFIBottomDivergence,
    OBVTopDivergence,
    OBVBottomDivergence,
    DoubleTop,
    DoubleBottom,
)

_ids = [rule.signal_id for rule in RULE_TYPES]
if len(_ids) != len(set(_ids)):
    raise RuntimeError("duplicate signal_id in RULE_TYPES")

__all__ = ["RULE_TYPES"]
