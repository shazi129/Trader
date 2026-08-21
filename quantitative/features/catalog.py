"""Single source of truth for materialized quantitative features."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSpec:
    key: str
    group: str
    description: str


def _spec(group: str, *items: tuple[str, str]) -> list[FeatureSpec]:
    return [FeatureSpec(key, group, description) for key, description in items]


FEATURE_SPECS: tuple[FeatureSpec, ...] = tuple(
    _spec(
        "trend",
        ("ma_5", "5日简单移动平均"),
        ("ma_10", "10日简单移动平均"),
        ("ma_20", "20日简单移动平均"),
        ("ma_30", "30日简单移动平均"),
        ("ma_60", "60日简单移动平均"),
        ("ma_120", "120日简单移动平均"),
        ("ma_200", "200日简单移动平均"),
        ("ma_250", "250日简单移动平均"),
        ("ema_12", "12日指数移动平均"),
        ("ema_26", "26日指数移动平均"),
        ("ema_50", "50日指数移动平均"),
        ("price_to_ma_5", "收盘价/MA5"),
        ("price_to_ma_10", "收盘价/MA10"),
        ("price_to_ma_20", "收盘价/MA20"),
        ("price_to_ma_60", "收盘价/MA60"),
        ("price_to_ma_200", "收盘价/MA200"),
        ("ma_150", "约30周移动平均"),
        ("ma_375", "约75周移动平均"),
        ("ma_150_to_375", "MA150/MA375"),
        ("ma_25_to_150", "MA25/MA150"),
        ("boll_middle", "布林带中轨"),
        ("boll_upper", "布林带上轨"),
        ("boll_lower", "布林带下轨"),
        ("boll_width", "布林带宽度"),
        ("boll_percent_b", "布林带%B"),
        ("macd_dif", "MACD DIF"),
        ("macd_dea", "MACD DEA"),
        ("macd_hist", "MACD柱"),
        ("tr", "真实波幅"),
        ("atr_14", "14日ATR"),
        ("atr_pct_14", "14日ATR占价格比例"),
        ("adx_14", "14日ADX"),
        ("plus_di_14", "14日+DI"),
        ("minus_di_14", "14日-DI"),
    )
    + _spec(
        "momentum",
        ("rsi_6", "6日RSI"),
        ("rsi_12", "12日RSI"),
        ("rsi_14", "14日RSI"),
        ("rsi_24", "24日RSI"),
        ("kdj_k", "KDJ K"),
        ("kdj_d", "KDJ D"),
        ("kdj_j", "KDJ J"),
        ("momentum_5", "5日收益动量"),
        ("momentum_10", "10日收益动量"),
        ("momentum_20", "20日收益动量"),
        ("momentum_63", "63日收益动量"),
        ("momentum_126", "126日收益动量"),
        ("momentum_189", "189日收益动量"),
        ("momentum_252", "252日收益动量"),
        ("cci_20", "20日CCI"),
        ("williams_r_14", "14日Williams %R"),
    )
    + _spec(
        "volume",
        ("obv", "能量潮"),
        ("vpt", "量价趋势"),
        ("adl", "累积派发线"),
        ("mfi_14", "14日资金流量指数"),
        ("force_index_1", "1日Force Index"),
        ("force_index_13", "13日Force Index"),
        ("force_index_21", "21日Force Index"),
        ("chaikin_osc", "Chaikin Oscillator"),
        ("volume_ma_20", "20日平均成交量"),
        ("volume_ratio_20", "成交量/20日均量"),
    )
    + _spec(
        "risk",
        ("historical_volatility_20", "20日年化历史波动率"),
        ("historical_volatility_60", "60日年化历史波动率"),
        ("max_drawdown", "截至当日最大回撤"),
        ("sharpe_252", "252日滚动夏普"),
        ("sortino_252", "252日滚动索提诺"),
        ("calmar_252", "252日滚动卡玛"),
        ("skewness_252", "252日收益偏度"),
        ("kurtosis_252", "252日收益超额峰度"),
    )
    + _spec(
        "liquidity",
        ("turnover_rate", "当日换手率"),
        ("turnover_rate_ma_5", "5日平均换手率"),
        ("turnover_rate_ma_20", "20日平均换手率"),
        ("turnover_rate_z_20", "20日换手率Z分"),
        ("amount_ma_5", "5日平均成交额"),
        ("amount_ma_20", "20日平均成交额"),
        ("amount_ratio_5_20", "5日/20日平均成交额"),
        ("amihud_20", "20日Amihud非流动性"),
        ("illiquidity_rank_252", "252日非流动性分位"),
        ("volume_price_corr_20", "20日量价相关"),
        ("money_flow_strength_20", "20日资金强度"),
    )
)

FEATURE_KEYS = tuple(spec.key for spec in FEATURE_SPECS)
FEATURE_BY_KEY = {spec.key: spec for spec in FEATURE_SPECS}

__all__ = ["FeatureSpec", "FEATURE_SPECS", "FEATURE_KEYS", "FEATURE_BY_KEY"]
