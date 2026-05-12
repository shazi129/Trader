# -*- coding: utf-8 -*-
"""单点因子计算引擎 `QuantFactorEngine`。

每个方法返回一个 `FactorResult`（包含 value / signal / description / weight），
代表"以最近一根 K 线为参考点"的因子读数。底层算法全部委托给
`quantitative.indicators.*`，与 `factor_batch.FactorSeriesEngine` 共享。
"""

from __future__ import annotations

from typing import Optional

from quote_api.quote_base import DailyQuote, StockFundamental

from quantitative.indicators import primitives as P
from quantitative.indicators.trend import macd as ti_macd, atr as ti_atr, adx as ti_adx
from quantitative.indicators.momentum import (
    rsi as ti_rsi,
    kdj as ti_kdj,
    cci as ti_cci,
    williams_r as ti_williams_r,
)
from quantitative.indicators.volume import (
    obv as ti_obv,
    vpt as ti_vpt,
    adl as ti_adl,
    chaikin_oscillator as ti_chaikin,
)
from quantitative.indicators.liquidity import (
    turnover_rate_zscore,
    amount_ratio,
    amihud_illiquidity_series,
    illiquidity_rank_series,
    vol_price_corr,
    money_flow_strength,
)
from quantitative.indicators import risk as R
from utils.logger import get_logger

from .scoring import FactorResult

_log = get_logger(__name__)


class QuantFactorEngine:
    """量化因子计算引擎（单点：用最后一根 K 线作判断）。"""

    # =====================================================================
    # 因子权重集中配置
    # =====================================================================
    # 所有因子的权重在此一处声明；每个因子方法构造 `FactorResult` 时
    # 通过 ``self._get_weight(<key>)`` 取值。调权 = 改这张表，无需动
    # 49 个方法实现。
    #
    # 命名约定：
    #   - 大多数 key 与 ``FactorResult.name`` 完全一致；
    #   - 动态名因子（如 ``"3M动量"``、``"RSI(14)"``）用一个固定 key
    #     代替（``"MomentumReturn"`` / ``"RSI"``），见 _get_weight。
    #
    # 权重档位（数值越大对最终概率影响越大）：
    #   1.5  核心        —— 均线排列
    #   1.2  重要        —— MACD / ADX / 30W/75W / 12M+1M反转
    #   1.0  标准        —— 动量、技术、流动性多数
    #   0.8  辅助        —— 量价系、短期反转、部分基本面
    #   0.6  弱信号      —— 股息率
    #   0.5  观察        —— 波动/风险类、跳空、市值
    # =====================================================================
    _WEIGHTS: dict[str, float] = {
        # ---- 动量类 ----
        "MomentumReturn":     1.0,   # 1M/3M/6M/9M/11M/12M 动量共用
        "30W/75W均线比":       1.2,
        "5W/30W均线比":        1.0,
        "价格/MA200":          1.0,
        "12M+1M反转":          1.2,

        # ---- 技术类 ----
        "RSI":                1.0,
        "MACD":               1.2,
        "布林带%B":            0.8,
        "量比":                0.8,
        "KDJ":                1.0,
        "Williams %R":        0.8,
        "OBV":                0.8,
        "CCI":                0.8,
        "VPT":                0.8,
        "ADL":                0.8,
        "Chaikin Osc":        0.8,
        "ATR":                0.5,

        # ---- 趋势类 ----
        "均线排列":             1.5,
        "趋势强度":             1.0,
        "ADX":                1.2,
        "DMI":                1.0,

        # ---- 波动 / 风险类 ----
        "历史波动率":           0.5,
        "最大回撤":             0.8,
        "下行波动率":           0.5,
        "夏普比率":             0.5,
        "索提诺比率":           0.5,
        "GK波动率":             0.5,
        "Parkinson波动率":      0.5,
        "RS波动率":             0.5,
        "收益率偏度":           0.5,
        "收益率峰度":           0.5,
        "Amihud非流动性":       0.5,

        # ---- 流动性 / 资金面类 ----
        "换手率Z分":            1.0,
        "成交额比率":           1.0,
        "流动性分位":           1.0,
        "量价相关20":           1.0,
        "资金强度":             1.0,

        # ---- 短期反转类 ----
        "1周反转":              0.8,
        "2周反转":              0.8,

        # ---- 价格形态类 ----
        "跳空缺口":             0.5,

        # ---- 基本面类 ----
        "市盈率PE":             1.0,
        "市净率PB":             1.0,
        "市销率PS":             0.8,
        "净资产收益率ROE":       1.0,
        "资产回报率ROA":         0.8,
        "EPS增长率":            1.0,
        "营收增长率":           0.8,
        "股息率":               0.6,
        "市值规模":             0.5,
    }

    #: 当 key 不在 `_WEIGHTS` 中时使用的默认权重（既不喧宾夺主也不归零）。
    _DEFAULT_WEIGHT: float = 1.0

    @classmethod
    def _get_weight(cls, key: str) -> float:
        """按 key 从 `_WEIGHTS` 取权重；缺失记日志一次性提示并回落默认值。"""
        w = cls._WEIGHTS.get(key)
        if w is None:
            _log.warning("factor weight key not found: %r, fallback to %s",
                         key, cls._DEFAULT_WEIGHT)
            return cls._DEFAULT_WEIGHT
        return w

    def __init__(self, quotes: list[DailyQuote],
                 fundamentals: Optional[StockFundamental] = None):
        self.quotes = quotes
        self.closes = [q.close for q in quotes]
        self.highs = [q.high for q in quotes]
        self.lows = [q.low for q in quotes]
        self.volumes = [q.volume for q in quotes]
        self.turnovers = [q.turnover for q in quotes]
        self.turnover_rates = [getattr(q, "turnover_rate", 0.0) for q in quotes]
        self.n = len(quotes)
        self.fundamentals = fundamentals

    # =====================================================================
    # 动量类
    # =====================================================================
    def momentum_return(self, months: int) -> Optional[FactorResult]:
        days = months * 21
        if self.n < days + 1:
            return None
        ret = (self.closes[-1] / self.closes[-days] - 1) * 100
        signal = 1 if ret > 5 else (-1 if ret < -5 else 0)
        return FactorResult(
            name=f"{months}M动量", category="momentum",
            value=round(ret, 2), signal=signal,
            weight=self._get_weight("MomentumReturn"),
            description=f"过去{months}个月涨跌幅: {ret:.2f}%",
        )

    def momentum_return_9m(self) -> Optional[FactorResult]:
        return self.momentum_return(9)

    def momentum_return_11m(self) -> Optional[FactorResult]:
        return self.momentum_return(11)

    def ma_ratio_30_75(self) -> Optional[FactorResult]:
        if self.n < 75 * 5:
            return None
        ma30w = sum(self.closes[-150:]) / 150
        ma75w = sum(self.closes[-375:]) / 375
        ratio = ma30w / ma75w if ma75w else 0.0
        signal = 1 if ratio > 1.02 else (-1 if ratio < 0.98 else 0)
        return FactorResult(
            name="30W/75W均线比", category="momentum",
            value=round(ratio, 4), signal=signal,
            weight=self._get_weight("30W/75W均线比"),
            description=f"30周均线/75周均线 = {ratio:.4f}，"
                        f"{'多头排列' if ratio > 1 else '空头排列'}",
        )

    def ma_ratio_5_30(self) -> Optional[FactorResult]:
        if self.n < 30 * 5:
            return None
        ma5w = sum(self.closes[-25:]) / 25
        ma30w = sum(self.closes[-150:]) / 150
        ratio = ma5w / ma30w if ma30w else 0.0
        signal = 1 if ratio > 1.02 else (-1 if ratio < 0.98 else 0)
        return FactorResult(
            name="5W/30W均线比", category="momentum",
            value=round(ratio, 4), signal=signal,
            weight=self._get_weight("5W/30W均线比"),
            description=f"5周均线/30周均线 = {ratio:.4f}，"
                        f"{'短期强于长期' if ratio > 1 else '短期弱于长期'}",
        )

    def price_to_ma200(self) -> Optional[FactorResult]:
        if self.n < 200:
            return None
        ma200 = sum(self.closes[-200:]) / 200
        pct = (self.closes[-1] / ma200 - 1) * 100 if ma200 else 0.0
        signal = 1 if pct > 3 else (-1 if pct < -3 else 0)
        return FactorResult(
            name="价格/MA200", category="momentum",
            value=round(pct, 2), signal=signal,
            weight=self._get_weight("价格/MA200"),
            description=f"当前价较200日均线 {'+' if pct > 0 else ''}{pct:.2f}%",
        )

    def reversal_12m_1m(self) -> Optional[FactorResult]:
        if self.n < 12 * 21 + 1:
            return None
        ret_12m = (self.closes[-1] / self.closes[-12 * 21] - 1) * 100
        ret_1m = (self.closes[-1] / self.closes[-21] - 1) * 100
        if ret_12m < -5 and ret_1m > 3:
            signal, desc = 1, f"12M={ret_12m:.1f}%(弱) + 1M={ret_1m:.1f}%(强)，底部反转信号"
        elif ret_12m > 5 and ret_1m < -3:
            signal, desc = -1, f"12M={ret_12m:.1f}%(强) + 1M={ret_1m:.1f}%(弱)，顶部反转信号"
        else:
            signal, desc = 0, f"12M={ret_12m:.1f}%, 1M={ret_1m:.1f}%，无明显反转"
        return FactorResult(
            name="12M+1M反转", category="momentum",
            value=round(ret_12m - ret_1m, 2), signal=signal,
            weight=self._get_weight("12M+1M反转"),
            description=desc,
        )

    # =====================================================================
    # 技术类
    # =====================================================================
    def rsi(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        seq = ti_rsi(self.closes, period=period)
        rsi_val = seq[-1]
        if rsi_val != rsi_val:  # nan
            return None
        if rsi_val > 70:
            signal, desc = -1, f"RSI={rsi_val:.1f}，超买区域，回调风险"
        elif rsi_val < 30:
            signal, desc = 1, f"RSI={rsi_val:.1f}，超卖区域，反弹机会"
        else:
            signal, desc = 0, f"RSI={rsi_val:.1f}，中性区域"
        return FactorResult(
            name=f"RSI({period})", category="technical",
            value=round(rsi_val, 2), signal=signal,
            weight=self._get_weight("RSI"),
            description=desc,
        )

    def macd(self) -> Optional[FactorResult]:
        if self.n < 35:
            return None
        res = ti_macd(self.closes)
        hist = res.dif[-1] - res.dea[-1]
        prev_hist = res.dif[-2] - res.dea[-2]
        if hist > 0 and prev_hist <= 0:
            signal, desc = 1, "MACD金叉，看涨信号"
        elif hist < 0 and prev_hist >= 0:
            signal, desc = -1, "MACD死叉，看跌信号"
        elif hist > 0:
            signal, desc = 1, f"MACD柱状={hist:.4f}，多头持续"
        else:
            signal, desc = -1, f"MACD柱状={hist:.4f}，空头持续"
        return FactorResult(
            name="MACD", category="technical",
            value=round(hist, 4), signal=signal,
            weight=self._get_weight("MACD"),
            description=desc,
        )

    def bollinger_position(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period:
            return None
        std_seq = P.rolling_std(self.closes, period)
        std = std_seq[-1]
        if std != std or std == 0:
            return None
        sma_val = sum(self.closes[-period:]) / period
        upper = sma_val + 2 * std
        lower = sma_val - 2 * std
        pct_b = (self.closes[-1] - lower) / (upper - lower)
        if pct_b > 0.8:
            signal, desc = -1, f"布林%B={pct_b:.2f}，接近上轨，回调压力"
        elif pct_b < 0.2:
            signal, desc = 1, f"布林%B={pct_b:.2f}，接近下轨，反弹支撑"
        else:
            signal, desc = 0, f"布林%B={pct_b:.2f}，通道中间"
        return FactorResult(
            name="布林带%B", category="technical",
            value=round(pct_b, 4), signal=signal,
            weight=self._get_weight("布林带%B"),
            description=desc,
        )

    def volume_trend(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period + 5:
            return None
        vol_avg = sum(self.volumes[-period - 5:-5]) / period
        vol_recent = sum(self.volumes[-5:]) / 5
        if vol_avg == 0:
            return None
        ratio = vol_recent / vol_avg
        price_change = self.closes[-1] / self.closes[-6] - 1
        if ratio > 1.5 and price_change > 0:
            signal, desc = 1, f"量比={ratio:.2f}，放量上涨，动能强"
        elif ratio > 1.5 and price_change < 0:
            signal, desc = -1, f"量比={ratio:.2f}，放量下跌，抛压重"
        else:
            signal, desc = 0, f"量比={ratio:.2f}，成交平稳"
        return FactorResult(
            name="量比", category="technical",
            value=round(ratio, 2), signal=signal,
            weight=self._get_weight("量比"),
            description=desc,
        )

    def kdj(self, period: int = 9) -> Optional[FactorResult]:
        if self.n < period + 3:
            return None
        res = ti_kdj(self.highs, self.lows, self.closes, period=period)
        j_val = res.j[-1]
        if j_val < 20:
            signal, desc = 1, f"KDJ J值={j_val:.1f}，超卖区域，反弹机会"
        elif j_val > 80:
            signal, desc = -1, f"KDJ J值={j_val:.1f}，超买区域，回调风险"
        else:
            signal, desc = 0, f"KDJ J值={j_val:.1f}，中性区域"
        return FactorResult(
            name="KDJ", category="technical",
            value=round(j_val, 2), signal=signal,
            weight=self._get_weight("KDJ"),
            description=desc,
        )

    def williams_r(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period:
            return None
        wr_val = ti_williams_r(self.highs, self.lows, self.closes, period=period)[-1]
        if wr_val > -20:
            signal, desc = -1, f"Williams %R={wr_val:.1f}，超买区域，回调风险"
        elif wr_val < -80:
            signal, desc = 1, f"Williams %R={wr_val:.1f}，超卖区域，反弹机会"
        else:
            signal, desc = 0, f"Williams %R={wr_val:.1f}，中性区域"
        return FactorResult(
            name="Williams %R", category="technical",
            value=round(wr_val, 2), signal=signal,
            weight=self._get_weight("Williams %R"),
            description=desc,
        )

    def obv(self) -> Optional[FactorResult]:
        if self.n < 6:
            return None
        obv_seq = ti_obv(self.closes, self.volumes)
        slope = (obv_seq[-1] - obv_seq[-5]) / 5
        price_up = self.closes[-1] > self.closes[-6]
        if slope > 0 and price_up:
            signal, desc = 1, "OBV上升且价格上升，量价配合"
        elif slope < 0 and price_up:
            signal, desc = -1, "OBV下降但价格上升，顶背离，警惕"
        elif slope > 0 and not price_up:
            signal, desc = 1, "OBV上升但价格下降，底背离，关注反转"
        else:
            signal, desc = -1, "OBV下降且价格下降，弱势"
        return FactorResult(
            name="OBV", category="technical",
            value=round(slope, 2), signal=signal,
            weight=self._get_weight("OBV"),
            description=desc,
        )

    def cci(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period:
            return None
        cci_val = ti_cci(self.highs, self.lows, self.closes, period=period)[-1]
        if cci_val > 100:
            signal, desc = -1, f"CCI={cci_val:.1f}，超买区域，回调风险"
        elif cci_val < -100:
            signal, desc = 1, f"CCI={cci_val:.1f}，超卖区域，反弹机会"
        else:
            signal, desc = 0, f"CCI={cci_val:.1f}，常态区域"
        return FactorResult(
            name="CCI", category="technical",
            value=round(cci_val, 2), signal=signal,
            weight=self._get_weight("CCI"),
            description=desc,
        )

    def volume_price_trend(self) -> Optional[FactorResult]:
        if self.n < 6:
            return None
        seq = ti_vpt(self.closes, self.volumes)
        slope = (seq[-1] - seq[-5]) / 5
        price_up = self.closes[-1] > self.closes[-6]
        if slope > 0 and price_up:
            signal, desc = 1, "VPT上升且价格上升，量价配合"
        elif slope < 0 and price_up:
            signal, desc = -1, "VPT下降但价格上升，顶背离"
        elif slope > 0 and not price_up:
            signal, desc = 1, "VPT上升但价格下降，底背离"
        else:
            signal, desc = -1, "VPT下降且价格下降，弱势"
        return FactorResult(
            name="VPT", category="technical",
            value=round(slope, 2), signal=signal,
            weight=self._get_weight("VPT"),
            description=desc,
        )

    def accumulation_distribution(self) -> Optional[FactorResult]:
        if self.n < 6:
            return None
        seq = ti_adl(self.highs, self.lows, self.closes, self.volumes)
        slope = (seq[-1] - seq[-5]) / 5
        price_up = self.closes[-1] > self.closes[-6]
        if slope > 0 and price_up:
            signal, desc = 1, "ADL上升且价格上升，量价配合"
        elif slope < 0 and price_up:
            signal, desc = -1, "ADL下降但价格上升，顶背离"
        elif slope > 0 and not price_up:
            signal, desc = 1, "ADL上升但价格下降，底背离"
        else:
            signal, desc = -1, "ADL下降且价格下降，弱势"
        return FactorResult(
            name="ADL", category="technical",
            value=round(slope, 2), signal=signal,
            weight=self._get_weight("ADL"),
            description=desc,
        )

    def chaikin_oscillator(self) -> Optional[FactorResult]:
        if self.n < 11:
            return None
        seq = ti_chaikin(self.highs, self.lows, self.closes, self.volumes)
        chaikin = seq[-1]
        signal = 1 if chaikin > 0 else -1
        desc = f"Chaikin={chaikin:.0f}，动量{'转正' if chaikin > 0 else '转负'}"
        return FactorResult(
            name="Chaikin Osc", category="technical",
            value=round(chaikin, 2), signal=signal,
            weight=self._get_weight("Chaikin Osc"),
            description=desc,
        )

    def atr(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        res = ti_atr(self.highs, self.lows, self.closes, period=period)
        atr_pct = res.atr_pct[-1]
        if atr_pct > 5:
            signal, desc = -1, f"ATR={atr_pct:.2f}%，波动剧烈，风险大"
        elif atr_pct < 1.5:
            signal, desc = 0, f"ATR={atr_pct:.2f}%，波动平缓"
        else:
            signal, desc = 0, f"ATR={atr_pct:.2f}%，正常波动"
        return FactorResult(
            name="ATR", category="volatility",
            value=round(atr_pct, 2), signal=signal,
            weight=self._get_weight("ATR"),
            description=desc,
        )

    # =====================================================================
    # 趋势类
    # =====================================================================
    def ma_alignment(self) -> Optional[FactorResult]:
        if self.n < 60:
            return None
        ma5 = sum(self.closes[-5:]) / 5
        ma10 = sum(self.closes[-10:]) / 10
        ma20 = sum(self.closes[-20:]) / 20
        ma60 = sum(self.closes[-60:]) / 60
        if ma5 > ma10 > ma20 > ma60:
            signal, score, desc = 1, 1.0, "完全多头排列（MA5>MA10>MA20>MA60）"
        elif ma5 < ma10 < ma20 < ma60:
            signal, score, desc = -1, -1.0, "完全空头排列（MA5<MA10<MA20<MA60）"
        elif ma5 > ma10 > ma20:
            signal, score, desc = 1, 0.6, "短期多头排列（MA5>MA10>MA20）"
        elif ma5 < ma10 < ma20:
            signal, score, desc = -1, -0.6, "短期空头排列（MA5<MA10<MA20）"
        else:
            signal, score, desc = 0, 0.0, "均线缠绕，方向不明"
        return FactorResult(
            name="均线排列", category="trend",
            value=round(score, 2), signal=signal,
            weight=self._get_weight("均线排列"),
            description=desc,
        )

    def trend_strength(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        ups, downs = 0, 0
        for i in range(self.n - period, self.n):
            if self.closes[i] > self.closes[i - 1]:
                ups += 1
            else:
                downs += 1
        consistency = abs(ups - downs) / period * 100
        direction = 1 if ups > downs else -1
        if consistency > 50:
            signal = direction
            desc = f"趋势强度={consistency:.0f}%，{'上升' if direction > 0 else '下降'}趋势明确"
        else:
            signal = 0
            desc = f"趋势强度={consistency:.0f}%，无明确方向"
        return FactorResult(
            name="趋势强度", category="trend",
            value=round(consistency * direction, 2), signal=signal,
            weight=self._get_weight("趋势强度"),
            description=desc,
        )

    def adx(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period * 2:
            return None
        res = ti_adx(self.highs, self.lows, self.closes, period=period)
        adx_val = res.adx[-1]
        if adx_val < 20:
            signal, desc = 0, f"ADX={adx_val:.1f}，无明确趋势"
        elif res.plus_di[-1] > res.minus_di[-1]:
            signal, desc = 1, f"ADX={adx_val:.1f}，+DI>-DI，上升趋势强"
        else:
            signal, desc = -1, f"ADX={adx_val:.1f}，-DI>+DI，下降趋势强"
        return FactorResult(
            name="ADX", category="trend",
            value=round(adx_val, 2), signal=signal,
            weight=self._get_weight("ADX"),
            description=desc,
        )

    def dmi(self, period: int = 14) -> Optional[FactorResult]:
        if self.n < period * 2:
            return None
        res = ti_adx(self.highs, self.lows, self.closes, period=period)
        pdi_val, mdi_val = res.plus_di[-1], res.minus_di[-1]
        if pdi_val > mdi_val * 1.2:
            signal, desc = 1, f"+DI={pdi_val:.1f} > -DI={mdi_val:.1f}，多头占优"
        elif mdi_val > pdi_val * 1.2:
            signal, desc = -1, f"-DI={mdi_val:.1f} > +DI={pdi_val:.1f}，空头占优"
        else:
            signal, desc = 0, f"+DI={pdi_val:.1f}，-DI={mdi_val:.1f}，多空均衡"
        return FactorResult(
            name="DMI", category="trend",
            value=round(pdi_val - mdi_val, 2), signal=signal,
            weight=self._get_weight("DMI"),
            description=desc,
        )

    # =====================================================================
    # 波动 / 风险类
    # =====================================================================
    def historical_volatility(self, period: int = 20) -> Optional[FactorResult]:
        vol = R.historical_volatility_point(self.closes, period=period)
        if vol is None:
            return None
        if vol > 40:
            signal, desc = -1, f"年化波动率={vol:.1f}%，高波动，风险大"
        elif vol < 15:
            signal, desc = 0, f"年化波动率={vol:.1f}%，低波动，稳定"
        else:
            signal, desc = 0, f"年化波动率={vol:.1f}%，正常水平"
        return FactorResult(
            name="历史波动率", category="volatility",
            value=round(vol, 2), signal=signal,
            weight=self._get_weight("历史波动率"),
            description=desc,
        )

    def max_drawdown_factor(self) -> Optional[FactorResult]:
        md = R.max_drawdown_point(self.closes)
        if md > 30:
            signal, desc = -1, f"最大回撤={md:.1f}%，深度回撤，风险大"
        elif md < 10:
            signal, desc = 0, f"最大回撤={md:.1f}%，回撤控制良好"
        else:
            signal, desc = 0, f"最大回撤={md:.1f}%，正常水平"
        return FactorResult(
            name="最大回撤", category="volatility",
            value=round(md, 2), signal=signal,
            weight=self._get_weight("最大回撤"),
            description=desc,
        )

    def downside_volatility(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        dv = R.downside_volatility_point(self.closes, period=period)
        if dv > 30:
            signal, desc = -1, f"下行波动率={dv:.1f}%，下行风险大"
        else:
            signal, desc = 0, f"下行波动率={dv:.1f}%，下行风险可控"
        return FactorResult(
            name="下行波动率", category="volatility",
            value=round(dv, 2), signal=signal,
            weight=self._get_weight("下行波动率"),
            description=desc,
        )

    def sharpe_ratio(self, period: int = 252) -> Optional[FactorResult]:
        sharpe = R.sharpe_point(self.closes, period=period)
        if sharpe is None:
            return None
        if sharpe > 1.0:
            signal, desc = 1, f"夏普比率={sharpe:.2f}，风险调整后收益优秀"
        elif sharpe > 0:
            signal, desc = 0, f"夏普比率={sharpe:.2f}，风险调整后收益一般"
        else:
            signal, desc = -1, f"夏普比率={sharpe:.2f}，风险调整后收益差"
        return FactorResult(
            name="夏普比率", category="volatility",
            value=round(sharpe, 2), signal=signal,
            weight=self._get_weight("夏普比率"),
            description=desc,
        )

    def sortino_ratio(self, period: int = 252) -> Optional[FactorResult]:
        sortino = R.sortino_point(self.closes, period=period)
        if sortino is None:
            return None
        if sortino > 1.0:
            signal, desc = 1, f"索提诺比率={sortino:.2f}，下行风险调整后收益优秀"
        elif sortino > 0:
            signal, desc = 0, f"索提诺比率={sortino:.2f}，下行风险调整后一般"
        else:
            signal, desc = -1, f"索提诺比率={sortino:.2f}，下行风险调整后差"
        return FactorResult(
            name="索提诺比率", category="volatility",
            value=round(sortino, 2), signal=signal,
            weight=self._get_weight("索提诺比率"),
            description=desc,
        )

    def garman_klass_volatility(self, period: int = 20) -> Optional[FactorResult]:
        v = R.garman_klass_volatility_point(self.highs, self.lows, self.closes, period=period)
        if v is None:
            return None
        signal, desc = (-1, f"GK波动率={v:.1f}%，高波动") if v > 40 else (0, f"GK波动率={v:.1f}%，正常")
        return FactorResult(
            name="GK波动率", category="volatility",
            value=round(v, 2), signal=signal,
            weight=self._get_weight("GK波动率"),
            description=desc,
        )

    def parkinson_volatility(self, period: int = 20) -> Optional[FactorResult]:
        v = R.parkinson_volatility_point(self.highs, self.lows, period=period)
        if v is None:
            return None
        signal, desc = (-1, f"Parkinson波动率={v:.1f}%，高波动") if v > 40 else (0, f"Parkinson波动率={v:.1f}%，正常")
        return FactorResult(
            name="Parkinson波动率", category="volatility",
            value=round(v, 2), signal=signal,
            weight=self._get_weight("Parkinson波动率"),
            description=desc,
        )

    def rogers_satchell_volatility(self, period: int = 20) -> Optional[FactorResult]:
        v = R.rogers_satchell_volatility_point(self.highs, self.lows, self.closes, period=period)
        if v is None:
            return None
        signal, desc = (-1, f"RS波动率={v:.1f}%，高波动") if v > 40 else (0, f"RS波动率={v:.1f}%，正常")
        return FactorResult(
            name="RS波动率", category="volatility",
            value=round(v, 2), signal=signal,
            weight=self._get_weight("RS波动率"),
            description=desc,
        )

    def skewness_factor(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        rets = []
        for i in range(self.n - period, self.n):
            prev = self.closes[i - 1]
            if prev <= 0:
                return None
            rets.append((self.closes[i] - prev) / prev)
        skew = R.skewness_point(rets, period)
        if skew < -1:
            signal, desc = -1, f"偏度={skew:.2f}，负偏严重，左尾风险大"
        elif skew > 1:
            signal, desc = 1, f"偏度={skew:.2f}，正偏，上涨潜力大"
        else:
            signal, desc = 0, f"偏度={skew:.2f}，接近对称"
        return FactorResult(
            name="收益率偏度", category="volatility",
            value=round(skew, 2), signal=signal,
            weight=self._get_weight("收益率偏度"),
            description=desc,
        )

    def kurtosis_factor(self, period: int = 20) -> Optional[FactorResult]:
        if self.n < period + 1:
            return None
        rets = []
        for i in range(self.n - period, self.n):
            prev = self.closes[i - 1]
            if prev <= 0:
                return None
            rets.append((self.closes[i] - prev) / prev)
        kurt = R.kurtosis_point(rets, period)
        if kurt > 3:
            signal, desc = -1, f"峰度={kurt:.2f}，高峰度，胖尾风险大"
        elif kurt < -1:
            signal, desc = 1, f"峰度={kurt:.2f}，低峰度，尾部风险小"
        else:
            signal, desc = 0, f"峰度={kurt:.2f}，接近正态分布"
        return FactorResult(
            name="收益率峰度", category="volatility",
            value=round(kurt, 2), signal=signal,
            weight=self._get_weight("收益率峰度"),
            description=desc,
        )

    def amihud_illiquidity(self, period: int = 20) -> Optional[FactorResult]:
        v = R.amihud_illiquidity_point(self.closes, self.volumes, period=period)
        signal = -1 if v > 0.1 else 0
        desc = (f"Amihud={v:.4f}，流动性差，风险大" if v > 0.1
                else f"Amihud={v:.4f}，流动性正常")
        return FactorResult(
            name="Amihud非流动性", category="volatility",
            value=round(v, 4), signal=signal,
            weight=self._get_weight("Amihud非流动性"),
            description=desc,
        )

    # =====================================================================
    # 流动性 / 资金面类（B 类：从 K 线派生）
    # =====================================================================
    #
    # 仅接入 5 个"有方向"的因子（会产生 +1/-1 信号）。另外 6 个纯信息
    # 字段（换手率绝对值/成交额绝对值/Amihud 原值）仍然会写入
    # factor_liquidity 表，但不参与加权评分，避免 signal 恒为 0 稀释
    # 总权重。所有 liquidity 因子 weight 默认 1.0。
    # =====================================================================
    def turnover_rate_zscore_factor(self, period: int = 20) -> Optional[FactorResult]:
        """当日换手率 Z 分（vs 20 日）。

        放量配合方向判信号：放量上涨 = 动能强 (+1)，放量下跌 = 抛压重 (-1)。
        数据源未提供换手率（近期窗口均值 = 0）时返回 None，不占权重。
        """
        if self.n < period + 1:
            return None
        window = self.turnover_rates[-period:]
        if sum(window) <= 0:
            return None  # 数据源不提供换手率
        z = turnover_rate_zscore(self.turnover_rates, period=period)[-1]
        # 价格 5 日方向，避免被单日噪音影响
        lookback = min(5, self.n - 1)
        prev = self.closes[-1 - lookback]
        price_up = prev > 0 and self.closes[-1] > prev
        if z > 2 and price_up:
            signal, desc = 1, f"换手率Z={z:.2f}，放量上涨，动能强"
        elif z > 2 and not price_up:
            signal, desc = -1, f"换手率Z={z:.2f}，放量下跌，抛压重"
        elif abs(z) < 1:
            signal, desc = 0, f"换手率Z={z:.2f}，成交平稳"
        else:
            signal, desc = 0, f"换手率Z={z:.2f}，温和异动"
        return FactorResult(
            name="换手率Z分", category="liquidity",
            value=round(z, 3), signal=signal,
            weight=self._get_weight("换手率Z分"),
            description=desc,
        )

    def amount_ratio_factor(self) -> Optional[FactorResult]:
        """ADTV5 / ADTV20：资金堆积速度。"""
        if self.n < 20:
            return None
        r = amount_ratio(self.turnovers, fast=5, slow=20)[-1]
        lookback = min(5, self.n - 1)
        prev = self.closes[-1 - lookback]
        price_up = prev > 0 and self.closes[-1] > prev
        if r > 1.2 and price_up:
            signal, desc = 1, f"成交额5/20={r:.2f}，近期资金堆积 + 价格上升"
        elif r > 1.2 and not price_up:
            signal, desc = -1, f"成交额5/20={r:.2f}，放量但价格下跌，警惕派发"
        elif r < 0.8:
            signal, desc = 0, f"成交额5/20={r:.2f}，近期缩量"
        else:
            signal, desc = 0, f"成交额5/20={r:.2f}，成交平稳"
        return FactorResult(
            name="成交额比率", category="liquidity",
            value=round(r, 3), signal=signal,
            weight=self._get_weight("成交额比率"),
            description=desc,
        )

    def illiquidity_rank_factor(self, period: int = 20,
                                 lookback: int = 252) -> Optional[FactorResult]:
        """Amihud 在 252 日自身分布中的分位；>0.8 = 当前流动性极差。"""
        if self.n < lookback + period:
            return None
        amihud_seq = amihud_illiquidity_series(self.closes, self.turnovers,
                                                period=period)
        rank = illiquidity_rank_series(amihud_seq, lookback=lookback)[-1]
        if rank > 0.8:
            signal, desc = -1, f"流动性分位={rank:.2f}，当前吃单成本高"
        elif rank < 0.2:
            signal, desc = 0, f"流动性分位={rank:.2f}，流动性充裕"
        else:
            signal, desc = 0, f"流动性分位={rank:.2f}，流动性正常"
        return FactorResult(
            name="流动性分位", category="liquidity",
            value=round(rank, 3), signal=signal,
            weight=self._get_weight("流动性分位"),
            description=desc,
        )

    def vol_price_corr_factor(self, period: int = 20) -> Optional[FactorResult]:
        """20 日 (日收益率, 日成交额) 相关：量价同向 / 背离。"""
        if self.n < period + 1:
            return None
        c = vol_price_corr(self.closes, self.turnovers, period=period)[-1]
        if c > 0.5:
            signal, desc = 1, f"量价相关={c:.2f}，放量涨/缩量跌，趋势健康"
        elif c < -0.5:
            signal, desc = -1, f"量价相关={c:.2f}，量价背离，警惕"
        else:
            signal, desc = 0, f"量价相关={c:.2f}，无明确量价关系"
        return FactorResult(
            name="量价相关20", category="liquidity",
            value=round(c, 3), signal=signal,
            weight=self._get_weight("量价相关20"),
            description=desc,
        )

    def money_flow_strength_factor(self, period: int = 20) -> Optional[FactorResult]:
        """净资金强度 = Σsign(R)·Amount / Σ|Amount|，∈[-1,1]。"""
        if self.n < period + 1:
            return None
        m = money_flow_strength(self.closes, self.turnovers, period=period)[-1]
        if m > 0.3:
            signal, desc = 1, f"资金强度={m:.2f}，20日资金净流入"
        elif m < -0.3:
            signal, desc = -1, f"资金强度={m:.2f}，20日资金净流出"
        else:
            signal, desc = 0, f"资金强度={m:.2f}，资金方向不明"
        return FactorResult(
            name="资金强度", category="liquidity",
            value=round(m, 3), signal=signal,
            weight=self._get_weight("资金强度"),
            description=desc,
        )

    # =====================================================================
    # 短期反转类
    # =====================================================================
    def weekly_reversal(self) -> Optional[FactorResult]:
        if self.n < 6:
            return None
        ret = (self.closes[-1] / self.closes[-6] - 1) * 100
        if ret < -3:
            signal, desc = 1, f"1周收益={ret:.1f}%，超跌反弹机会"
        elif ret > 3:
            signal, desc = -1, f"1周收益={ret:.1f}%，超涨回调风险"
        else:
            signal, desc = 0, f"1周收益={ret:.1f}%，正常"
        return FactorResult(
            name="1周反转", category="reversal",
            value=round(ret, 2), signal=signal,
            weight=self._get_weight("1周反转"),
            description=desc,
        )

    def biweekly_reversal(self) -> Optional[FactorResult]:
        if self.n < 11:
            return None
        ret = (self.closes[-1] / self.closes[-11] - 1) * 100
        if ret < -5:
            signal, desc = 1, f"2周收益={ret:.1f}%，超跌反弹机会"
        elif ret > 5:
            signal, desc = -1, f"2周收益={ret:.1f}%，超涨回调风险"
        else:
            signal, desc = 0, f"2周收益={ret:.1f}%，正常"
        return FactorResult(
            name="2周反转", category="reversal",
            value=round(ret, 2), signal=signal,
            weight=self._get_weight("2周反转"),
            description=desc,
        )

    # =====================================================================
    # 价格形态类
    # =====================================================================
    def gap_factor(self) -> Optional[FactorResult]:
        if self.n < 2:
            return None
        gaps = []
        for i in range(max(1, self.n - 20), self.n):
            prev = self.closes[i - 1]
            if prev:
                gaps.append((self.closes[i] - prev) / prev * 100)
        avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
        if avg_gap > 2:
            signal, desc = -1, f"平均缺口={avg_gap:.1f}%，向上跳空，可能回调"
        elif avg_gap < -2:
            signal, desc = 1, f"平均缺口={avg_gap:.1f}%，向下跳空，可能反弹"
        else:
            signal, desc = 0, f"平均缺口={avg_gap:.1f}%，正常"
        return FactorResult(
            name="跳空缺口", category="pattern",
            value=round(avg_gap, 2), signal=signal,
            weight=self._get_weight("跳空缺口"),
            description=desc,
        )

    # =====================================================================
    # 基本面类
    # =====================================================================
    def pe_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.pe_ttm <= 0:
            return None
        pe = self.fundamentals.pe_ttm
        if pe < 10:
            signal, desc = 1, f"PE={pe:.2f}，低估值，价值低估"
        elif pe > 30:
            signal, desc = -1, f"PE={pe:.2f}，高估值，价值高估"
        else:
            signal, desc = 0, f"PE={pe:.2f}，估值合理"
        return FactorResult(
            name="市盈率PE", category="valuation",
            value=round(pe, 2), signal=signal,
            weight=self._get_weight("市盈率PE"),
            description=desc,
        )

    def pb_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.pb <= 0:
            return None
        pb = self.fundamentals.pb
        if pb < 1.0:
            signal, desc = 1, f"PB={pb:.2f}，低市净率，价值低估"
        elif pb > 3.0:
            signal, desc = -1, f"PB={pb:.2f}，高市净率，价值高估"
        else:
            signal, desc = 0, f"PB={pb:.2f}，市净率合理"
        return FactorResult(
            name="市净率PB", category="valuation",
            value=round(pb, 2), signal=signal,
            weight=self._get_weight("市净率PB"),
            description=desc,
        )

    def ps_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.ps_ttm <= 0:
            return None
        ps = self.fundamentals.ps_ttm
        if ps < 1.0:
            signal, desc = 1, f"PS={ps:.2f}，低市销率，价值低估"
        elif ps > 3.0:
            signal, desc = -1, f"PS={ps:.2f}，高市销率，价值高估"
        else:
            signal, desc = 0, f"PS={ps:.2f}，市销率合理"
        return FactorResult(
            name="市销率PS", category="valuation",
            value=round(ps, 2), signal=signal,
            weight=self._get_weight("市销率PS"),
            description=desc,
        )

    def roe_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.roe_ttm <= 0:
            return None
        roe = self.fundamentals.roe_ttm
        if roe > 15.0:
            signal, desc = 1, f"ROE={roe:.2f}%，盈利能力优秀"
        elif roe < 5.0:
            signal, desc = -1, f"ROE={roe:.2f}%，盈利能力差"
        else:
            signal, desc = 0, f"ROE={roe:.2f}%，盈利能力一般"
        return FactorResult(
            name="净资产收益率ROE", category="quality",
            value=round(roe, 2), signal=signal,
            weight=self._get_weight("净资产收益率ROE"),
            description=desc,
        )

    def roa_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.roa <= 0:
            return None
        roa = self.fundamentals.roa
        if roa > 8.0:
            signal, desc = 1, f"ROA={roa:.2f}%，资产回报率优秀"
        elif roa < 3.0:
            signal, desc = -1, f"ROA={roa:.2f}%，资产回报率低"
        else:
            signal, desc = 0, f"ROA={roa:.2f}%，资产回报率一般"
        return FactorResult(
            name="资产回报率ROA", category="quality",
            value=round(roa, 2), signal=signal,
            weight=self._get_weight("资产回报率ROA"),
            description=desc,
        )

    def eps_growth_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.eps_growth_ttm == 0:
            return None
        g = self.fundamentals.eps_growth_ttm
        if g > 20.0:
            signal, desc = 1, f"EPS增长率={g:.2f}%，成长性强"
        elif g < 0.0:
            signal, desc = -1, f"EPS增长率={g:.2f}%，盈利下滑"
        else:
            signal, desc = 0, f"EPS增长率={g:.2f}%，稳定成长"
        return FactorResult(
            name="EPS增长率", category="growth",
            value=round(g, 2), signal=signal,
            weight=self._get_weight("EPS增长率"),
            description=desc,
        )

    def revenue_growth_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.revenue_growth_ttm == 0:
            return None
        g = self.fundamentals.revenue_growth_ttm
        if g > 15.0:
            signal, desc = 1, f"营收增长率={g:.2f}%，业务快速扩张"
        elif g < 0.0:
            signal, desc = -1, f"营收增长率={g:.2f}%，营收下滑"
        else:
            signal, desc = 0, f"营收增长率={g:.2f}%，稳定增长"
        return FactorResult(
            name="营收增长率", category="growth",
            value=round(g, 2), signal=signal,
            weight=self._get_weight("营收增长率"),
            description=desc,
        )

    def dividend_yield_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.dividend_yield <= 0:
            return None
        y = self.fundamentals.dividend_yield
        if y > 3.0:
            signal, desc = 1, f"股息率={y:.2f}%，高股息，价值股"
        elif y < 1.0:
            signal, desc = -1, f"股息率={y:.2f}%，低股息"
        else:
            signal, desc = 0, f"股息率={y:.2f}%，中等股息"
        return FactorResult(
            name="股息率", category="dividend",
            value=round(y, 2), signal=signal,
            weight=self._get_weight("股息率"),
            description=desc,
        )

    def market_cap_factor(self) -> Optional[FactorResult]:
        if self.fundamentals is None or self.fundamentals.market_cap <= 0:
            return None
        mcap_yi = self.fundamentals.market_cap / 1e8
        if mcap_yi < 100:
            signal, desc = 1, f"市值={mcap_yi:.0f}亿，小盘股，规模溢价"
        elif mcap_yi > 1000:
            signal, desc = -1, f"市值={mcap_yi:.0f}亿，大盘股，规模折价"
        else:
            signal, desc = 0, f"市值={mcap_yi:.0f}亿，中盘股"
        return FactorResult(
            name="市值规模", category="size",
            value=round(mcap_yi, 2), signal=signal,
            weight=self._get_weight("市值规模"),
            description=desc,
        )

    # =====================================================================
    # 全量计算
    # =====================================================================
    def compute_all(self) -> list[FactorResult]:
        results: list[FactorResult] = []
        factor_funcs = [
            # 动量类
            lambda: self.momentum_return(1),
            lambda: self.momentum_return(3),
            lambda: self.momentum_return(6),
            lambda: self.momentum_return(12),
            self.momentum_return_9m,
            self.momentum_return_11m,
            self.ma_ratio_30_75,
            self.ma_ratio_5_30,
            self.price_to_ma200,
            self.reversal_12m_1m,
            # 技术类
            self.rsi, self.macd, self.bollinger_position, self.volume_trend,
            self.kdj, self.williams_r, self.obv, self.cci, self.atr,
            self.volume_price_trend, self.accumulation_distribution,
            self.chaikin_oscillator,
            # 趋势类
            self.ma_alignment, self.trend_strength, self.adx, self.dmi,
            # 波动 / 风险类
            self.historical_volatility, self.max_drawdown_factor,
            self.downside_volatility, self.sharpe_ratio, self.sortino_ratio,
            self.garman_klass_volatility, self.parkinson_volatility,
            self.rogers_satchell_volatility, self.skewness_factor,
            self.kurtosis_factor, self.amihud_illiquidity,
            # 流动性 / 资金面类（weight 默认 1.0）
            self.turnover_rate_zscore_factor, self.amount_ratio_factor,
            self.illiquidity_rank_factor, self.vol_price_corr_factor,
            self.money_flow_strength_factor,
            # 短期反转类
            self.weekly_reversal, self.biweekly_reversal,
            # 价格形态类
            self.gap_factor,
            # 基本面类
            self.pe_factor, self.pb_factor, self.ps_factor,
            self.roe_factor, self.roa_factor,
            self.eps_growth_factor, self.revenue_growth_factor,
            self.dividend_yield_factor, self.market_cap_factor,
        ]
        for fn in factor_funcs:
            try:
                r = fn()
                if r is not None:
                    results.append(r)
            except Exception as e:
                _log.warning("factor %s error: %s", getattr(fn, "__name__", "?"), e)
        return results
