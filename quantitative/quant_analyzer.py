# -*- coding: utf-8 -*-
"""
量化因子分析工具

基于 Quantitative Primer 中的量化因子框架，对指定股票进行多因子分析，
输出后续涨跌概率和趋势判断。

可用因子（共 40 个，全部基于 K 线/成交量数据）：

【动量类 10个】
- 1M/3M/6M/12M/9M/11M 价格动量
- 30W/75W 均线比、5W/30W 均线比
- 价格/200日均线
- 12M+1M 反转因子

【技术类 11个】
- RSI(14)、MACD、KDJ、Williams %R
- 布林带%B、OBV 能量潮、CCI 商品通道
- ATR 平均真实波幅、量比（成交量趋势）
- VPT（成交量价格趋势）、ADL（积累/分配线）、Chaikin 震荡

【趋势类 4个】
- 均线排列（5/10/20/60）
- 趋势强度、ADX 平均趋向指数、DMI 方向运动指标

【波动/风险类 9个】
- 历史波动率（年化）、最大回撤、下行波动率
- ATR 波动率、夏普比率、索提诺比率
- GK波动率、Parkinson波动率、RS波动率
- 收益率偏度、收益率峰度、Amihud非流动性

【短期反转类 2个】
- 1周反转、2周反转

【价格形态类 1个】
- 跳空缺口因子

使用方法：
    python -m quantitative.quant_analyzer Tencent
    python -m quantitative.quant_analyzer SSE_Index --api tencent --days 500
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import config
from quote_api import QuoteAPIFactory
from quote_api.quote_base import DailyQuote, StockFundamental


# ===========================================================================
# 因子结果数据结构
# ===========================================================================

@dataclass
class FactorResult:
    """单个因子的计算结果"""
    name: str              # 因子名称
    category: str          # 类别：momentum / technical / trend / volatility
    value: float           # 因子值
    signal: int            # 信号：+1=看涨, 0=中性, -1=看跌
    weight: float = 1.0    # 权重
    description: str = ""  # 描述


@dataclass
class AnalysisReport:
    """综合分析报告"""
    stock_name: str
    stock_code: str
    data_source: str
    data_days: int
    latest_price: float
    factors: list[FactorResult] = field(default_factory=list)
    bullish_score: float = 0.0   # 看涨综合得分 (0~100)
    bearish_score: float = 0.0   # 看跌综合得分 (0~100)
    trend: str = ""              # "上涨趋势" / "下跌趋势" / "震荡"
    probability_up: float = 0.0  # 上涨概率 (0~1)
    probability_down: float = 0.0  # 下跌概率 (0~1)
    summary: str = ""


# ===========================================================================
# 因子计算引擎
# ===========================================================================

class QuantFactorEngine:
    """量化因子计算引擎"""

    def __init__(self, quotes: list[DailyQuote], fundamentals: Optional[StockFundamental] = None):
        """
        :param quotes: 日K线列表，按日期升序排列
        :param fundamentals: 基本面数据（可选）
        """
        self.quotes = quotes
        self.closes = [q.close for q in quotes]
        self.highs = [q.high for q in quotes]
        self.lows = [q.low for q in quotes]
        self.volumes = [q.volume for q in quotes]
        self.n = len(quotes)
        self.fundamentals = fundamentals  # 基本面数据

    # -----------------------------------------------------------------------
    # 工具函数
    # -----------------------------------------------------------------------
    def _sma(self, data: list[float], period: int) -> list[float]:
        """简单移动平均"""
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(float('nan'))
            else:
                result.append(sum(data[i - period + 1:i + 1]) / period)
        return result

    def _ema(self, data: list[float], period: int) -> list[float]:
        """指数移动平均"""
        result = []
        multiplier = 2.0 / (period + 1)
        for i, v in enumerate(data):
            if i == 0:
                result.append(v)
            else:
                result.append(v * multiplier + result[-1] * (1 - multiplier))
        return result

    def _std(self, data: list[float], period: int) -> list[float]:
        """滚动标准差"""
        import math
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(float('nan'))
            else:
                window = data[i - period + 1:i + 1]
                mean = sum(window) / period
                var = sum((x - mean) ** 2 for x in window) / period
                result.append(math.sqrt(var))
        return result

    def _true_range(self) -> list[float]:
        """真实波幅 TR = max(H_t, C_{t-1}) - min(L_t, C_{t-1})"""
        tr = []
        for i in range(self.n):
            c_prev = self.closes[i - 1] if i > 0 else self.closes[i]
            tr_val = max(self.highs[i], c_prev) - min(self.lows[i], c_prev)
            tr.append(tr_val)
        return tr

    def _plus_dm(self, period: int = 14) -> list[float]:
        """+DM 正向动向（raw，未平滑）"""
        pdm = []
        for i in range(self.n):
            if i == 0:
                pdm.append(0.0)
                continue
            up_move = self.highs[i] - self.highs[i - 1]
            down_move = self.lows[i - 1] - self.lows[i]
            pdm.append(max(up_move, 0) if up_move > down_move else 0.0)
        return pdm

    def _minus_dm(self, period: int = 14) -> list[float]:
        """-DM 负向动向（raw，未平滑）"""
        mdm = []
        for i in range(self.n):
            if i == 0:
                mdm.append(0.0)
                continue
            up_move = self.highs[i] - self.highs[i - 1]
            down_move = self.lows[i - 1] - self.lows[i]
            mdm.append(max(down_move, 0) if down_move > up_move else 0.0)
        return mdm

    def _smooth(self, data: list[float], period: int) -> list[float]:
        """平滑处理（Wilder's smoothing）"""
        result = []
        s = 0.0
        for i, v in enumerate(data):
            if i == 0:
                s = v
            else:
                s = s - s / period + v
            result.append(s)
        return result

    def _max_drawdown(self) -> float:
        """计算最大回撤（百分比）"""
        if self.n < 2:
            return 0.0
        peak = self.closes[0]
        max_dd = 0.0
        for c in self.closes:
            if c > peak:
                peak = c
            dd = (peak - c) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd * 100

    def _downside_deviation(self, period: int, mar: float = 0.0) -> float:
        """下行偏差（用于 Sortino 比率）"""
        import math
        if self.n < period + 1:
            return 0.0
        downsides = []
        for i in range(self.n - period, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            if ret < mar:
                downsides.append((ret - mar) ** 2)
        if not downsides:
            return 0.0
        return math.sqrt(sum(downsides) / len(downsides))

    def _log_returns(self, period: int = 1) -> list[float]:
        """计算对数收益率"""
        import math
        returns = []
        for i in range(self.n):
            if i < period:
                returns.append(0.0)
            else:
                returns.append(math.log(self.closes[i] / self.closes[i - period]))
        return returns

    def _skewness(self, data: list[float], period: int) -> float:
        """计算偏度"""
        import math
        if len(data) < period:
            return 0.0
        window = data[-period:]
        n = len(window)
        mean = sum(window) / n
        var = sum((x - mean) ** 2 for x in window) / n
        if var == 0:
            return 0.0
        std = math.sqrt(var)
        skew = sum((x - mean) ** 3 for x in window) / n / (std ** 3)
        return skew

    def _kurtosis(self, data: list[float], period: int) -> float:
        """计算峰度（超额峰度）"""
        import math
        if len(data) < period:
            return 0.0
        window = data[-period:]
        n = len(window)
        mean = sum(window) / n
        var = sum((x - mean) ** 2 for x in window) / n
        if var == 0:
            return 0.0
        std = math.sqrt(var)
        kurt = sum((x - mean) ** 4 for x in window) / n / (std ** 4)
        return kurt - 3  # 超额峰度

    def _amihud_illiquidity(self, period: int = 20) -> float:
        """计算 Amihud 非流动性指标"""
        import math
        if self.n < period + 1:
            return 0.0
        illiq_vals = []
        for i in range(self.n - period, self.n):
            if i == 0 or self.volumes[i] == 0:
                illiq_vals.append(0.0)
                continue
            ret = abs((self.closes[i] - self.closes[i - 1]) / self.closes[i - 1])
            illiq = ret / self.volumes[i] * 1e8  # 缩放因子
            illiq_vals.append(illiq)
        return sum(illiq_vals) / len(illiq_vals)

    # -----------------------------------------------------------------------
    # 动量类因子
    # -----------------------------------------------------------------------
    def momentum_return(self, months: int) -> Optional[FactorResult]:
        """价格动量：过去 N 个月的累计回报率"""
        days = months * 21  # 近似交易日
        if self.n < days + 1:
            return None
        ret = (self.closes[-1] / self.closes[-days] - 1) * 100
        signal = 1 if ret > 5 else (-1 if ret < -5 else 0)
        return FactorResult(
            name=f"{months}M动量",
            category="momentum",
            value=round(ret, 2),
            signal=signal,
            weight=1.0,
            description=f"过去{months}个月涨跌幅: {ret:.2f}%"
        )

    def ma_ratio_30_75(self) -> Optional[FactorResult]:
        """30周/75周均线比（Relative Strength）"""
        if self.n < 75 * 5:
            return None
        ma30w = sum(self.closes[-150:]) / 150  # 30周≈150日
        ma75w = sum(self.closes[-375:]) / 375  # 75周≈375日
        ratio = ma30w / ma75w
        signal = 1 if ratio > 1.02 else (-1 if ratio < 0.98 else 0)
        return FactorResult(
            name="30W/75W均线比",
            category="momentum",
            value=round(ratio, 4),
            signal=signal,
            weight=1.2,
            description=f"30周均线/75周均线 = {ratio:.4f}，{'多头排列' if ratio > 1 else '空头排列'}"
        )

    def price_to_ma200(self) -> Optional[FactorResult]:
        """股价相对200日均线的位置"""
        if self.n < 200:
            return None
        ma200 = sum(self.closes[-200:]) / 200
        ratio = self.closes[-1] / ma200
        pct = (ratio - 1) * 100
        signal = 1 if pct > 3 else (-1 if pct < -3 else 0)
        return FactorResult(
            name="价格/MA200",
            category="momentum",
            value=round(pct, 2),
            signal=signal,
            weight=1.0,
            description=f"当前价较200日均线 {'+' if pct > 0 else ''}{pct:.2f}%"
        )

    def momentum_return_9m(self) -> Optional[FactorResult]:
        """9个月价格动量"""
        return self._momentum_n(9, "9M动量")

    def momentum_return_11m(self) -> Optional[FactorResult]:
        """11个月价格动量"""
        return self._momentum_n(11, "11M动量")

    def _momentum_n(self, months: int, name: str) -> Optional[FactorResult]:
        """通用N月动量计算"""
        days = months * 21
        if self.n < days + 1:
            return None
        ret = (self.closes[-1] / self.closes[-days] - 1) * 100
        signal = 1 if ret > 5 else (-1 if ret < -5 else 0)
        return FactorResult(
            name=name,
            category="momentum",
            value=round(ret, 2),
            signal=signal,
            weight=1.0,
            description=f"过去{months}个月涨跌幅: {ret:.2f}%"
        )

    def ma_ratio_5_30(self) -> Optional[FactorResult]:
        """5周/30周均线比（Quantitative Primer 中的 5-week/30-week）"""
        if self.n < 30 * 5:
            return None
        ma5w = sum(self.closes[-25:]) / 25    # 5周≈25日
        ma30w = sum(self.closes[-150:]) / 150  # 30周≈150日
        ratio = ma5w / ma30w
        signal = 1 if ratio > 1.02 else (-1 if ratio < 0.98 else 0)
        return FactorResult(
            name="5W/30W均线比",
            category="momentum",
            value=round(ratio, 4),
            signal=signal,
            weight=1.0,
            description=f"5周均线/30周均线 = {ratio:.4f}，{'短期强于长期' if ratio > 1 else '短期弱于长期'}"
        )

    def reversal_12m_1m(self) -> Optional[FactorResult]:
        """12个月+1个月反转因子（12M & 1M Reversal）
        Quantitative Primer: 做多12个月跑输但近1个月跑赢的股票
        """
        if self.n < 12 * 21 + 1:
            return None
        ret_12m = (self.closes[-1] / self.closes[-12 * 21] - 1) * 100
        ret_1m = (self.closes[-1] / self.closes[-21] - 1) * 100
        # 12个月跑输 + 近1个月跑赢 = 看涨反转信号
        if ret_12m < -5 and ret_1m > 3:
            signal = 1
            desc = f"12M={ret_12m:.1f}%(弱) + 1M={ret_1m:.1f}%(强)，底部反转信号"
        elif ret_12m > 5 and ret_1m < -3:
            signal = -1
            desc = f"12M={ret_12m:.1f}%(强) + 1M={ret_1m:.1f}%(弱)，顶部反转信号"
        else:
            signal = 0
            desc = f"12M={ret_12m:.1f}%, 1M={ret_1m:.1f}%，无明显反转"
        return FactorResult(
            name="12M+1M反转",
            category="momentum",
            value=round(ret_12m - ret_1m, 2),
            signal=signal,
            weight=1.2,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 技术类因子
    # -----------------------------------------------------------------------
    def rsi(self, period: int = 14) -> Optional[FactorResult]:
        """RSI 相对强弱指标"""
        if self.n < period + 1:
            return None
        gains, losses = [], []
        for i in range(self.n - period, self.n):
            diff = self.closes[i] - self.closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))

        if rsi_val > 70:
            signal = -1  # 超买
            desc = f"RSI={rsi_val:.1f}，超买区域，回调风险"
        elif rsi_val < 30:
            signal = 1   # 超卖
            desc = f"RSI={rsi_val:.1f}，超卖区域，反弹机会"
        else:
            signal = 0
            desc = f"RSI={rsi_val:.1f}，中性区域"

        return FactorResult(
            name=f"RSI({period})",
            category="technical",
            value=round(rsi_val, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def macd(self) -> Optional[FactorResult]:
        """MACD 指标"""
        if self.n < 35:
            return None
        ema12 = self._ema(self.closes, 12)
        ema26 = self._ema(self.closes, 26)
        dif = [ema12[i] - ema26[i] for i in range(self.n)]
        dea = self._ema(dif, 9)
        macd_hist = dif[-1] - dea[-1]
        # 信号判断
        prev_hist = dif[-2] - dea[-2]
        if macd_hist > 0 and prev_hist <= 0:
            signal = 1
            desc = "MACD金叉，看涨信号"
        elif macd_hist < 0 and prev_hist >= 0:
            signal = -1
            desc = "MACD死叉，看跌信号"
        elif macd_hist > 0:
            signal = 1
            desc = f"MACD柱状={macd_hist:.4f}，多头持续"
        else:
            signal = -1
            desc = f"MACD柱状={macd_hist:.4f}，空头持续"

        return FactorResult(
            name="MACD",
            category="technical",
            value=round(macd_hist, 4),
            signal=signal,
            weight=1.2,
            description=desc
        )

    def bollinger_position(self, period: int = 20) -> Optional[FactorResult]:
        """布林带位置（%B）"""
        if self.n < period:
            return None
        sma = sum(self.closes[-period:]) / period
        std_vals = self._std(self.closes, period)
        std = std_vals[-1]
        if std == 0 or std != std:  # nan check
            return None
        upper = sma + 2 * std
        lower = sma - 2 * std
        pct_b = (self.closes[-1] - lower) / (upper - lower)

        if pct_b > 0.8:
            signal = -1
            desc = f"布林%B={pct_b:.2f}，接近上轨，回调压力"
        elif pct_b < 0.2:
            signal = 1
            desc = f"布林%B={pct_b:.2f}，接近下轨，反弹支撑"
        else:
            signal = 0
            desc = f"布林%B={pct_b:.2f}，通道中间"

        return FactorResult(
            name="布林带%B",
            category="technical",
            value=round(pct_b, 4),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def volume_trend(self, period: int = 20) -> Optional[FactorResult]:
        """成交量趋势（量比）"""
        if self.n < period + 5:
            return None
        vol_avg = sum(self.volumes[-period - 5:-5]) / period
        vol_recent = sum(self.volumes[-5:]) / 5
        if vol_avg == 0:
            return None
        ratio = vol_recent / vol_avg

        price_change = self.closes[-1] / self.closes[-6] - 1
        # 放量上涨=看涨，放量下跌=看跌，缩量=中性
        if ratio > 1.5 and price_change > 0:
            signal = 1
            desc = f"量比={ratio:.2f}，放量上涨，动能强"
        elif ratio > 1.5 and price_change < 0:
            signal = -1
            desc = f"量比={ratio:.2f}，放量下跌，抛压重"
        else:
            signal = 0
            desc = f"量比={ratio:.2f}，成交平稳"

        return FactorResult(
            name="量比",
            category="technical",
            value=round(ratio, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def kdj(self, period: int = 9, m_period: int = 3) -> Optional[FactorResult]:
        """KDJ 随机指标（Wilder 标准化算法）"""
        if self.n < period + m_period:
            return None
        k_vals, d_vals = [50.0], [50.0]
        for i in range(self.n):
            # 计算 RSV
            if i < period - 1:
                rsv = 50.0
            else:
                low_n = min(self.lows[i - period + 1:i + 1])
                high_n = max(self.highs[i - period + 1:i + 1])
                if high_n == low_n:
                    rsv = 50.0
                else:
                    rsv = (self.closes[i] - low_n) / (high_n - low_n) * 100
            # K, D
            k = 2.0 / 3 * k_vals[-1] + 1.0 / 3 * rsv
            d = 2.0 / 3 * d_vals[-1] + 1.0 / 3 * k
            k_vals.append(k)
            d_vals.append(d)
        j = 3 * k_vals[-1] - 2 * d_vals[-1]

        # 信号：J < 20 超卖（看涨），J > 80 超买（看跌）
        j_val = j
        if j_val < 20:
            signal = 1
            desc = f"KDJ J值={j_val:.1f}，超卖区域，反弹机会"
        elif j_val > 80:
            signal = -1
            desc = f"KDJ J值={j_val:.1f}，超买区域，回调风险"
        else:
            signal = 0
            desc = f"KDJ J值={j_val:.1f}，中性区域"
        return FactorResult(
            name="KDJ",
            category="technical",
            value=round(j_val, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def williams_r(self, period: int = 14) -> Optional[FactorResult]:
        """威廉指标 Williams %R（所有 bar 均计算，无 nan）"""
        if self.n < period:
            return None
        lows = self.lows
        highs = self.highs
        closes = self.closes
        wr = []
        for i in range(self.n):
            start = max(0, i - period + 1)
            high_n = max(highs[start:i + 1])
            low_n = min(lows[start:i + 1])
            if high_n == low_n:
                wr.append(-50.0)
            else:
                wr.append((high_n - closes[i]) / (high_n - low_n) * -100)
        wr_val = wr[-1]
        if wr_val > -20:
            signal = -1
            desc = f"Williams %R={wr_val:.1f}，超买区域，回调风险"
        elif wr_val < -80:
            signal = 1
            desc = f"Williams %R={wr_val:.1f}，超卖区域，反弹机会"
        else:
            signal = 0
            desc = f"Williams %R={wr_val:.1f}，中性区域"
        return FactorResult(
            name="Williams %R",
            category="technical",
            value=round(wr_val, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def obv(self) -> Optional[FactorResult]:
        """OBV 能量潮（On-Balance Volume）"""
        if self.n < 2:
            return None
        obv_vals = [0.0]
        for i in range(1, self.n):
            if self.closes[i] > self.closes[i - 1]:
                obv_vals.append(obv_vals[-1] + self.volumes[i])
            elif self.closes[i] < self.closes[i - 1]:
                obv_vals.append(obv_vals[-1] - self.volumes[i])
            else:
                obv_vals.append(obv_vals[-1])
        # 用最近 OBV 斜率判断：最近5日 OBV 变化方向
        obv_recent = obv_vals[-5:]
        obv_slope = (obv_recent[-1] - obv_recent[0]) / 5
        price_up = self.closes[-1] > self.closes[-6] if self.n >= 6 else True
        # OBV 上升 + 价格上升 = 强势（看涨）
        # OBV 下降 + 价格上升 = 背离（看跌）
        if obv_slope > 0 and price_up:
            signal = 1
            desc = "OBV上升且价格上升，量价配合"
        elif obv_slope < 0 and price_up:
            signal = -1
            desc = "OBV下降但价格上升，顶背离，警惕"
        elif obv_slope > 0 and not price_up:
            signal = 1
            desc = "OBV上升但价格下降，底背离，关注反转"
        else:
            signal = -1
            desc = "OBV下降且价格下降，弱势"
        return FactorResult(
            name="OBV",
            category="technical",
            value=round(obv_slope, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def cci(self, period: int = 20) -> Optional[FactorResult]:
        """CCI 商品通道指数（Commodity Channel Index）"""
        import math
        if self.n < period:
            return None
        tp = [(self.highs[i] + self.lows[i] + self.closes[i]) / 3 for i in range(self.n)]
        cci_vals = []
        for i in range(self.n):
            if i < period - 1:
                cci_vals.append(float('nan'))
                continue
            window = tp[i - period + 1:i + 1]
            ma_tp = sum(window) / period
            md = sum(abs(x - ma_tp) for x in window) / period
            if md == 0:
                cci_vals.append(0.0)
            else:
                cci_vals.append((tp[i] - ma_tp) / (0.015 * md))
        cci_val = cci_vals[-1]
        if cci_val > 100:
            signal = -1
            desc = f"CCI={cci_val:.1f}，超买区域，回调风险"
        elif cci_val < -100:
            signal = 1
            desc = f"CCI={cci_val:.1f}，超卖区域，反弹机会"
        else:
            signal = 0
            desc = f"CCI={cci_val:.1f}，常态区域"
        return FactorResult(
            name="CCI",
            category="technical",
            value=round(cci_val, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def volume_price_trend(self) -> Optional[FactorResult]:
        """成交量价格趋势（Volume Price Trend, VPT）"""
        if self.n < 2:
            return None
        vpt = [0.0]
        for i in range(1, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            vpt.append(vpt[-1] + self.volumes[i] * ret)
        # 用最近VPT斜率判断
        vpt_recent = vpt[-5:]
        vpt_slope = (vpt_recent[-1] - vpt_recent[0]) / 5
        price_up = self.closes[-1] > self.closes[-6] if self.n >= 6 else True
        if vpt_slope > 0 and price_up:
            signal = 1
            desc = "VPT上升且价格上升，量价配合"
        elif vpt_slope < 0 and price_up:
            signal = -1
            desc = "VPT下降但价格上升，顶背离"
        elif vpt_slope > 0 and not price_up:
            signal = 1
            desc = "VPT上升但价格下降，底背离"
        else:
            signal = -1
            desc = "VPT下降且价格下降，弱势"
        return FactorResult(
            name="VPT",
            category="technical",
            value=round(vpt_slope, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def accumulation_distribution(self) -> Optional[FactorResult]:
        """积累/分配线（Accumulation/Distribution Line, ADL）"""
        if self.n < 2:
            return None
        adl = [0.0]
        for i in range(1, self.n):
            if self.highs[i] == self.lows[i]:
                clv = 0.0
            else:
                clv = ((self.closes[i] - self.lows[i]) - (self.highs[i] - self.closes[i])) / (self.highs[i] - self.lows[i]) * self.volumes[i]
            adl.append(adl[-1] + clv)
        # 用最近ADL斜率判断
        adl_recent = adl[-5:]
        adl_slope = (adl_recent[-1] - adl_recent[0]) / 5
        price_up = self.closes[-1] > self.closes[-6] if self.n >= 6 else True
        if adl_slope > 0 and price_up:
            signal = 1
            desc = "ADL上升且价格上升，量价配合"
        elif adl_slope < 0 and price_up:
            signal = -1
            desc = "ADL下降但价格上升，顶背离"
        elif adl_slope > 0 and not price_up:
            signal = 1
            desc = "ADL上升但价格下降，底背离"
        else:
            signal = -1
            desc = "ADL下降且价格下降，弱势"
        return FactorResult(
            name="ADL",
            category="technical",
            value=round(adl_slope, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def chaikin_oscillator(self, period_fast: int = 3, period_slow: int = 10) -> Optional[FactorResult]:
        """Chaikin 震荡指标"""
        if self.n < period_slow + 1:
            return None
        # 计算ADL
        adl = [0.0]
        for i in range(1, self.n):
            if self.highs[i] == self.lows[i]:
                clv = 0.0
            else:
                clv = ((self.closes[i] - self.lows[i]) - (self.highs[i] - self.closes[i])) / (self.highs[i] - self.lows[i]) * self.volumes[i]
            adl.append(adl[-1] + clv)
        # 计算快速和慢速EMA
        ema_fast = self._ema(adl, period_fast)
        ema_slow = self._ema(adl, period_slow)
        chaikin = ema_fast[-1] - ema_slow[-1]
        # 信号判断
        if chaikin > 0:
            signal = 1
            desc = f"Chaikin={chaikin:.0f}，动量转正"
        else:
            signal = -1
            desc = f"Chaikin={chaikin:.0f}，动量转负"
        return FactorResult(
            name="Chaikin Osc",
            category="technical",
            value=round(chaikin, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def atr(self, period: int = 14) -> Optional[FactorResult]:
        """ATR 平均真实波幅"""
        if self.n < period + 1:
            return None
        tr = self._true_range()
        atr_vals = []
        s = 0.0
        for i in range(self.n):
            if i == 0:
                s = tr[i]
            else:
                s = s - s / period + tr[i]
            atr_vals.append(s)
        atr_val = atr_vals[-1]
        atr_pct = atr_val / self.closes[-1] * 100
        if atr_pct > 5:
            signal = -1
            desc = f"ATR={atr_pct:.2f}%，波动剧烈，风险大"
        elif atr_pct < 1.5:
            signal = 0
            desc = f"ATR={atr_pct:.2f}%，波动平缓"
        else:
            signal = 0
            desc = f"ATR={atr_pct:.2f}%，正常波动"
        return FactorResult(
            name="ATR",
            category="volatility",
            value=round(atr_pct, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 趋势类因子
    # -----------------------------------------------------------------------
    def ma_alignment(self) -> Optional[FactorResult]:
        """均线排列（5/10/20/60日）"""
        if self.n < 60:
            return None
        ma5 = sum(self.closes[-5:]) / 5
        ma10 = sum(self.closes[-10:]) / 10
        ma20 = sum(self.closes[-20:]) / 20
        ma60 = sum(self.closes[-60:]) / 60

        # 多头排列: MA5 > MA10 > MA20 > MA60
        if ma5 > ma10 > ma20 > ma60:
            signal = 1
            score = 1.0
            desc = "完全多头排列（MA5>MA10>MA20>MA60）"
        elif ma5 < ma10 < ma20 < ma60:
            signal = -1
            score = -1.0
            desc = "完全空头排列（MA5<MA10<MA20<MA60）"
        elif ma5 > ma10 > ma20:
            signal = 1
            score = 0.6
            desc = "短期多头排列（MA5>MA10>MA20）"
        elif ma5 < ma10 < ma20:
            signal = -1
            score = -0.6
            desc = "短期空头排列（MA5<MA10<MA20）"
        else:
            signal = 0
            score = 0.0
            desc = "均线缠绕，方向不明"

        return FactorResult(
            name="均线排列",
            category="trend",
            value=round(score, 2),
            signal=signal,
            weight=1.5,
            description=desc
        )

    def trend_strength(self, period: int = 14) -> Optional[FactorResult]:
        """趋势强度（简化 ADX）"""
        if self.n < period + 1:
            return None
        # 简化计算：用价格方向一致性衡量趋势强度
        ups = 0
        downs = 0
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
            name="趋势强度",
            category="trend",
            value=round(consistency * direction, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def adx(self, period: int = 14) -> Optional[FactorResult]:
        """ADX 平均趋向指数（完整 Wilder 算法）"""
        if self.n < period * 2:
            return None
        tr = self._true_range()
        pdm_raw = self._plus_dm(period)
        mdm_raw = self._minus_dm(period)

        # TR14, +DM14, -DM14（Wilder 平滑）
        tr14 = self._smooth(tr, period)
        pdm14 = self._smooth(pdm_raw, period)
        mdm14 = self._smooth(mdm_raw, period)

        # +DI14, -DI14
        pdi = [pdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]
        mdi = [mdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]

        # DX, ADX
        dx_list = []
        for i in range(self.n):
            denom = pdi[i] + mdi[i]
            dx = 100 * abs(pdi[i] - mdi[i]) / denom if denom != 0 else 0.0
            dx_list.append(dx)
        # ADX = DX 的 period 日平滑
        adx_vals = self._smooth(dx_list, period)
        adx_val = adx_vals[-1]

        # 信号：ADX > 25 表示趋势强；pdi > mdi 看涨
        if adx_val < 20:
            signal = 0
            desc = f"ADX={adx_val:.1f}，无明确趋势"
        elif pdi[-1] > mdi[-1]:
            signal = 1
            desc = f"ADX={adx_val:.1f}，+DI>-DI，上升趋势强"
        else:
            signal = -1
            desc = f"ADX={adx_val:.1f}，-DI>+DI，下降趋势强"
        return FactorResult(
            name="ADX",
            category="trend",
            value=round(adx_val, 2),
            signal=signal,
            weight=1.2,
            description=desc
        )

    def dmi(self, period: int = 14) -> Optional[FactorResult]:
        """DMI 方向运动指标（+DI / -DI）"""
        if self.n < period * 2:
            return None
        tr = self._true_range()
        pdm_raw = self._plus_dm(period)
        mdm_raw = self._minus_dm(period)
        tr14 = self._smooth(tr, period)
        pdm14 = self._smooth(pdm_raw, period)
        mdm14 = self._smooth(mdm_raw, period)
        pdi = [pdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]
        mdi = [mdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]
        pdi_val = pdi[-1]
        mdi_val = mdi[-1]
        if pdi_val > mdi_val * 1.2:
            signal = 1
            desc = f"+DI={pdi_val:.1f} > -DI={mdi_val:.1f}，多头占优"
        elif mdi_val > pdi_val * 1.2:
            signal = -1
            desc = f"-DI={mdi_val:.1f} > +DI={pdi_val:.1f}，空头占优"
        else:
            signal = 0
            desc = f"+DI={pdi_val:.1f}，-DI={mdi_val:.1f}，多空均衡"
        return FactorResult(
            name="DMI",
            category="trend",
            value=round(pdi_val - mdi_val, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 波动/风险类因子
    # -----------------------------------------------------------------------
    def historical_volatility(self, period: int = 20) -> Optional[FactorResult]:
        """历史波动率"""
        import math
        if self.n < period + 1:
            return None
        returns = []
        for i in range(self.n - period, self.n):
            r = math.log(self.closes[i] / self.closes[i - 1])
            returns.append(r)
        mean_r = sum(returns) / period
        var = sum((r - mean_r) ** 2 for r in returns) / (period - 1)
        vol = math.sqrt(var) * math.sqrt(252) * 100  # 年化

        if vol > 40:
            signal = -1
            desc = f"年化波动率={vol:.1f}%，高波动，风险大"
        elif vol < 15:
            signal = 0
            desc = f"年化波动率={vol:.1f}%，低波动，稳定"
        else:
            signal = 0
            desc = f"年化波动率={vol:.1f}%，正常水平"

        return FactorResult(
            name="历史波动率",
            category="volatility",
            value=round(vol, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def max_drawdown_factor(self) -> Optional[FactorResult]:
        """最大回撤因子"""
        md = self._max_drawdown()
        if md > 30:
            signal = -1
            desc = f"最大回撤={md:.1f}%，深度回撤，风险大"
        elif md < 10:
            signal = 0
            desc = f"最大回撤={md:.1f}%，回撤控制良好"
        else:
            signal = 0
            desc = f"最大回撤={md:.1f}%，正常水平"
        return FactorResult(
            name="最大回撤",
            category="volatility",
            value=round(md, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def downside_volatility(self, period: int = 20) -> Optional[FactorResult]:
        """下行波动率（Downside Volatility）"""
        import math
        if self.n < period + 1:
            return None
        downsides = []
        for i in range(self.n - period, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            if ret < 0:
                downsides.append(ret ** 2)
        if not downsides:
            dv = 0.0
        else:
            dv = math.sqrt(sum(downsides) / len(downsides)) * math.sqrt(252) * 100
        if dv > 30:
            signal = -1
            desc = f"下行波动率={dv:.1f}%，下行风险大"
        else:
            signal = 0
            desc = f"下行波动率={dv:.1f}%，下行风险可控"
        return FactorResult(
            name="下行波动率",
            category="volatility",
            value=round(dv, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def sharpe_ratio(self, period: int = 252, risk_free: float = 0.0) -> Optional[FactorResult]:
        """夏普比率（需要无风险利率，默认0）"""
        import math
        if self.n < period + 1:
            return None
        returns = []
        for i in range(self.n - period, self.n):
            r = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            returns.append(r)
        mean_r = sum(returns) / period
        var = sum((r - mean_r) ** 2 for r in returns) / (period - 1)
        std = math.sqrt(var)
        if std == 0:
            return None
        sharpe = (mean_r - risk_free / 252) / std * math.sqrt(252)
        if sharpe > 1.0:
            signal = 1
            desc = f"夏普比率={sharpe:.2f}，风险调整后收益优秀"
        elif sharpe > 0:
            signal = 0
            desc = f"夏普比率={sharpe:.2f}，风险调整后收益一般"
        else:
            signal = -1
            desc = f"夏普比率={sharpe:.2f}，风险调整后收益差"
        return FactorResult(
            name="夏普比率",
            category="volatility",
            value=round(sharpe, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def sortino_ratio(self, period: int = 252, risk_free: float = 0.0, mar: float = 0.0) -> Optional[FactorResult]:
        """索提诺比率（Sortino Ratio）"""
        import math
        if self.n < period + 1:
            return None
        returns = []
        for i in range(self.n - period, self.n):
            r = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            returns.append(r)
        mean_r = sum(returns) / period
        dd = self._downside_deviation(period, mar)
        if dd == 0:
            return None
        sortino = (mean_r - risk_free / 252) / dd * math.sqrt(252)
        if sortino > 1.0:
            signal = 1
            desc = f"索提诺比率={sortino:.2f}，下行风险调整后收益优秀"
        elif sortino > 0:
            signal = 0
            desc = f"索提诺比率={sortino:.2f}，下行风险调整后一般"
        else:
            signal = -1
            desc = f"索提诺比率={sortino:.2f}，下行风险调整后差"
        return FactorResult(
            name="索提诺比率",
            category="volatility",
            value=round(sortino, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def garman_klass_volatility(self, period: int = 20) -> Optional[FactorResult]:
        """Garman-Klass 波动率（使用日内高低价）"""
        import math
        if self.n < period:
            return None
        gk_vals = []
        for i in range(self.n - period, self.n):
            if self.closes[i - 1] == 0:
                gk_vals.append(0.0)
                continue
            log_hl = (math.log(self.highs[i] / self.lows[i])) ** 2
            log_co = (math.log(self.closes[i] / self.closes[i - 1])) ** 2
            gk = 0.5 * log_hl - (2 * math.log(2) - 1) * log_co
            gk_vals.append(gk)
        gk_vol = math.sqrt(sum(gk_vals) / period) * math.sqrt(252) * 100
        if gk_vol > 40:
            signal = -1
            desc = f"GK波动率={gk_vol:.1f}%，高波动"
        else:
            signal = 0
            desc = f"GK波动率={gk_vol:.1f}%，正常"
        return FactorResult(
            name="GK波动率",
            category="volatility",
            value=round(gk_vol, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def parkinson_volatility(self, period: int = 20) -> Optional[FactorResult]:
        """Parkinson 波动率（使用日内最高/低价）"""
        import math
        if self.n < period:
            return None
        park_vals = []
        for i in range(self.n - period, self.n):
            if self.lows[i] == 0:
                park_vals.append(0.0)
                continue
            park = (math.log(self.highs[i] / self.lows[i])) ** 2
            park_vals.append(park)
        park_vol = math.sqrt(sum(park_vals) / (4 * math.log(2) * period)) * math.sqrt(252) * 100
        if park_vol > 40:
            signal = -1
            desc = f"Parkinson波动率={park_vol:.1f}%，高波动"
        else:
            signal = 0
            desc = f"Parkinson波动率={park_vol:.1f}%，正常"
        return FactorResult(
            name="Parkinson波动率",
            category="volatility",
            value=round(park_vol, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def rogers_satchell_volatility(self, period: int = 20) -> Optional[FactorResult]:
        """Rogers-Satchell 波动率（考虑价格漂移）"""
        import math
        if self.n < period + 1:
            return None
        rs_vals = []
        for i in range(self.n - period, self.n):
            if self.lows[i] == 0 or self.closes[i - 1] == 0:
                rs_vals.append(0.0)
                continue
            log_hc = math.log(self.highs[i] / self.closes[i - 1])
            log_lo = math.log(self.lows[i] / self.closes[i - 1])
            log_co = math.log(self.closes[i] / self.closes[i - 1])
            rs = log_hc * math.log(self.highs[i] / self.closes[i]) + log_lo * math.log(self.lows[i] / self.closes[i])
            rs_vals.append(rs)
        rs_vol = math.sqrt(sum(rs_vals) / period) * math.sqrt(252) * 100
        if rs_vol > 40:
            signal = -1
            desc = f"RS波动率={rs_vol:.1f}%，高波动"
        else:
            signal = 0
            desc = f"RS波动率={rs_vol:.1f}%，正常"
        return FactorResult(
            name="RS波动率",
            category="volatility",
            value=round(rs_vol, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def skewness_factor(self, period: int = 20) -> Optional[FactorResult]:
        """收益率偏度因子"""
        import math
        if self.n < period + 1:
            return None
        returns = []
        for i in range(self.n - period, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            returns.append(ret)
        skew = self._skewness(returns, period)
        # 负偏度（左尾风险大）= 看跌；正偏度 = 看涨
        if skew < -1:
            signal = -1
            desc = f"偏度={skew:.2f}，负偏严重，左尾风险大"
        elif skew > 1:
            signal = 1
            desc = f"偏度={skew:.2f}，正偏，上涨潜力大"
        else:
            signal = 0
            desc = f"偏度={skew:.2f}，接近对称"
        return FactorResult(
            name="收益率偏度",
            category="volatility",
            value=round(skew, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def kurtosis_factor(self, period: int = 20) -> Optional[FactorResult]:
        """收益率峰度因子（超额峰度）"""
        import math
        if self.n < period + 1:
            return None
        returns = []
        for i in range(self.n - period, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            returns.append(ret)
        kurt = self._kurtosis(returns, period)
        # 高峰度（胖尾风险大）= 看跌；低峰度 = 看涨
        if kurt > 3:
            signal = -1
            desc = f"峰度={kurt:.2f}，高峰度，胖尾风险大"
        elif kurt < -1:
            signal = 1
            desc = f"峰度={kurt:.2f}，低峰度，尾部风险小"
        else:
            signal = 0
            desc = f"峰度={kurt:.2f}，接近正态分布"
        return FactorResult(
            name="收益率峰度",
            category="volatility",
            value=round(kurt, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    def amihud_illiquidity(self, period: int = 20) -> Optional[FactorResult]:
        """Amihud 非流动性指标"""
        if self.n < period + 1:
            return None
        illiq_vals = []
        for i in range(self.n - period, self.n):
            if i == 0 or self.volumes[i] == 0:
                illiq_vals.append(0.0)
                continue
            ret = abs((self.closes[i] - self.closes[i - 1]) / self.closes[i - 1])
            illiq = ret / self.volumes[i] * 1e8  # 缩放因子
            illiq_vals.append(illiq)
        illiq_val = sum(illiq_vals) / len(illiq_vals)
        if illiq_val > 0.1:
            signal = -1
            desc = f"Amihud={illiq_val:.4f}，流动性差，风险大"
        else:
            signal = 0
            desc = f"Amihud={illiq_val:.4f}，流动性正常"
        return FactorResult(
            name="Amihud非流动性",
            category="volatility",
            value=round(illiq_val, 4),
            signal=signal,
            weight=0.5,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 短期反转类因子
    # -----------------------------------------------------------------------
    def weekly_reversal(self) -> Optional[FactorResult]:
        """周度反转因子（1周收益率）"""
        if self.n < 5 + 1:
            return None
        ret_1w = (self.closes[-1] / self.closes[-6] - 1) * 100
        # 短期反转：上周跌多了本周涨，上周涨多了本周跌
        if ret_1w < -3:
            signal = 1
            desc = f"1周收益={ret_1w:.1f}%，超跌反弹机会"
        elif ret_1w > 3:
            signal = -1
            desc = f"1周收益={ret_1w:.1f}%，超涨回调风险"
        else:
            signal = 0
            desc = f"1周收益={ret_1w:.1f}%，正常"
        return FactorResult(
            name="1周反转",
            category="reversal",
            value=round(ret_1w, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def biweekly_reversal(self) -> Optional[FactorResult]:
        """双周反转因子（2周收益率）"""
        if self.n < 10 + 1:
            return None
        ret_2w = (self.closes[-1] / self.closes[-11] - 1) * 100
        if ret_2w < -5:
            signal = 1
            desc = f"2周收益={ret_2w:.1f}%，超跌反弹机会"
        elif ret_2w > 5:
            signal = -1
            desc = f"2周收益={ret_2w:.1f}%，超涨回调风险"
        else:
            signal = 0
            desc = f"2周收益={ret_2w:.1f}%，正常"
        return FactorResult(
            name="2周反转",
            category="reversal",
            value=round(ret_2w, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 价格形态类因子
    # -----------------------------------------------------------------------
    def gap_factor(self) -> Optional[FactorResult]:
        """跳空缺口因子"""
        if self.n < 2:
            return None
        # 计算今日跳空幅度
        gap = (self.closes[0] - self.closes[-1]) / self.closes[-1] * 100  # 简化：用首日与昨收比较
        # 更精确：今日开盘价与昨收比较（但K线数据可能没有开盘价）
        # 这里用收盘价近似
        recent_gaps = []
        for i in range(max(1, self.n - 20), self.n):
            g = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1] * 100
            recent_gaps.append(g)
        avg_gap = sum(recent_gaps) / len(recent_gaps)
        if avg_gap > 2:
            signal = -1
            desc = f"平均缺口={avg_gap:.1f}%，向上跳空，可能回调"
        elif avg_gap < -2:
            signal = 1
            desc = f"平均缺口={avg_gap:.1f}%，向下跳空，可能反弹"
        else:
            signal = 0
            desc = f"平均缺口={avg_gap:.1f}%，正常"
        return FactorResult(
            name="跳空缺口",
            category="pattern",
            value=round(avg_gap, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 基本面因子（需要 StockFundamental 数据）
    # -----------------------------------------------------------------------
    def pe_factor(self) -> Optional[FactorResult]:
        """市盈率因子（P/E Ratio）
        
        低PE = 看涨（价值低估），高PE = 看跌（价值高估）
        但也要考虑成长性（低PE可能意味着问题）
        """
        if self.fundamentals is None or self.fundamentals.pe_ttm <= 0:
            return None
        
        pe = self.fundamentals.pe_ttm
        
        # 简单判断：PE < 15 低估，PE > 30 高估
        # 不同行业合理PE不同，这里用通用标准
        if pe < 10:
            signal = 1
            desc = f"PE={pe:.2f}，低估值，价值低估"
        elif pe > 30:
            signal = -1
            desc = f"PE={pe:.2f}，高估值，价值高估"
        else:
            signal = 0
            desc = f"PE={pe:.2f}，估值合理"
        
        return FactorResult(
            name="市盈率PE",
            category="valuation",
            value=round(pe, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def pb_factor(self) -> Optional[FactorResult]:
        """市净率因子（P/B Ratio）
        
        低PB = 看涨（价值低估），高PB = 看跌（价值高估）
        """
        if self.fundamentals is None or self.fundamentals.pb <= 0:
            return None
        
        pb = self.fundamentals.pb
        
        # 简单判断：PB < 1.5 低估，PB > 3 高估
        if pb < 1.0:
            signal = 1
            desc = f"PB={pb:.2f}，低市净率，价值低估"
        elif pb > 3.0:
            signal = -1
            desc = f"PB={pb:.2f}，高市净率，价值高估"
        else:
            signal = 0
            desc = f"PB={pb:.2f}，市净率合理"
        
        return FactorResult(
            name="市净率PB",
            category="valuation",
            value=round(pb, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def ps_factor(self) -> Optional[FactorResult]:
        """市销率因子（P/S Ratio）
        
        需要营收数据，如果不存在则基于市值/营收估算
        """
        if self.fundamentals is None or self.fundamentals.ps_ttm <= 0:
            # 如果没有PS数据，尝试基于市值和价格变动估算
            if self.fundamentals is None or self.fundamentals.market_cap <= 0:
                return None
            # 无法计算，返回None
            return None
        
        ps = self.fundamentals.ps_ttm
        
        # 简单判断：PS < 1 低估，PS > 3 高估
        if ps < 1.0:
            signal = 1
            desc = f"PS={ps:.2f}，低市销率，价值低估"
        elif ps > 3.0:
            signal = -1
            desc = f"PS={ps:.2f}，高市销率，价值高估"
        else:
            signal = 0
            desc = f"PS={ps:.2f}，市销率合理"
        
        return FactorResult(
            name="市销率PS",
            category="valuation",
            value=round(ps, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def roe_factor(self) -> Optional[FactorResult]:
        """净资产收益率因子（ROE）
        
        高ROE = 看涨（盈利能力强）
        """
        if self.fundamentals is None or self.fundamentals.roe_ttm <= 0:
            return None
        
        roe = self.fundamentals.roe_ttm
        
        # ROE > 15% 优秀，ROE < 5% 差
        if roe > 15.0:
            signal = 1
            desc = f"ROE={roe:.2f}%，盈利能力优秀"
        elif roe < 5.0:
            signal = -1
            desc = f"ROE={roe:.2f}%，盈利能力差"
        else:
            signal = 0
            desc = f"ROE={roe:.2f}%，盈利能力一般"
        
        return FactorResult(
            name="净资产收益率ROE",
            category="quality",
            value=round(roe, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def roa_factor(self) -> Optional[FactorResult]:
        """资产回报率因子（ROA）
        
        高ROA = 看涨（资产利用效率高）
        """
        if self.fundamentals is None or self.fundamentals.roa <= 0:
            return None
        
        roa = self.fundamentals.roa
        
        # ROA > 8% 优秀，ROA < 3% 差
        if roa > 8.0:
            signal = 1
            desc = f"ROA={roa:.2f}%，资产回报率优秀"
        elif roa < 3.0:
            signal = -1
            desc = f"ROA={roa:.2f}%，资产回报率低"
        else:
            signal = 0
            desc = f"ROA={roa:.2f}%，资产回报率一般"
        
        return FactorResult(
            name="资产回报率ROA",
            category="quality",
            value=round(roa, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def eps_growth_factor(self) -> Optional[FactorResult]:
        """EPS增长率因子
        
        高增长率 = 看涨（成长性强）
        """
        if self.fundamentals is None or self.fundamentals.eps_growth_ttm == 0:
            return None
        
        growth = self.fundamentals.eps_growth_ttm
        
        # 增长率 > 20% 优秀，增长率 < 0% 差
        if growth > 20.0:
            signal = 1
            desc = f"EPS增长率={growth:.2f}%，成长性强"
        elif growth < 0.0:
            signal = -1
            desc = f"EPS增长率={growth:.2f}%，盈利下滑"
        else:
            signal = 0
            desc = f"EPS增长率={growth:.2f}%，稳定成长"
        
        return FactorResult(
            name="EPS增长率",
            category="growth",
            value=round(growth, 2),
            signal=signal,
            weight=1.0,
            description=desc
        )

    def revenue_growth_factor(self) -> Optional[FactorResult]:
        """营收增长率因子
        
        高增长率 = 看涨（业务扩张）
        """
        if self.fundamentals is None or self.fundamentals.revenue_growth_ttm == 0:
            return None
        
        growth = self.fundamentals.revenue_growth_ttm
        
        if growth > 15.0:
            signal = 1
            desc = f"营收增长率={growth:.2f}%，业务快速扩张"
        elif growth < 0.0:
            signal = -1
            desc = f"营收增长率={growth:.2f}%，营收下滑"
        else:
            signal = 0
            desc = f"营收增长率={growth:.2f}%，稳定增长"
        
        return FactorResult(
            name="营收增长率",
            category="growth",
            value=round(growth, 2),
            signal=signal,
            weight=0.8,
            description=desc
        )

    def dividend_yield_factor(self) -> Optional[FactorResult]:
        """股息率因子
        
        高股息率 = 看涨（稳定现金流，价值股特征）
        """
        if self.fundamentals is None or self.fundamentals.dividend_yield <= 0:
            return None
        
        yield_val = self.fundamentals.dividend_yield
        
        # 股息率 > 3% 高，股息率 < 1% 低
        if yield_val > 3.0:
            signal = 1
            desc = f"股息率={yield_val:.2f}%，高股息，价值股"
        elif yield_val < 1.0:
            signal = -1
            desc = f"股息率={yield_val:.2f}%，低股息"
        else:
            signal = 0
            desc = f"股息率={yield_val:.2f}%，中等股息"
        
        return FactorResult(
            name="股息率",
            category="dividend",
            value=round(yield_val, 2),
            signal=signal,
            weight=0.6,
            description=desc
        )

    def market_cap_factor(self) -> Optional[FactorResult]:
        """市值规模因子（Size Factor）
        
        小盘股通常有更高的预期收益（规模溢价）
        但也要考虑流动性风险
        """
        if self.fundamentals is None or self.fundamentals.market_cap <= 0:
            return None
        
        # 转换为亿为单位
        mcap_yi = self.fundamentals.market_cap / 1e8
        
        # 小盘：< 100亿，中盘：100-1000亿，大盘：> 1000亿
        if mcap_yi < 100:
            signal = 1
            desc = f"市值={mcap_yi:.0f}亿，小盘股，规模溢价"
        elif mcap_yi > 1000:
            signal = -1
            desc = f"市值={mcap_yi:.0f}亿，大盘股，规模折价"
        else:
            signal = 0
            desc = f"市值={mcap_yi:.0f}亿，中盘股"
        
        return FactorResult(
            name="市值规模",
            category="size",
            value=round(mcap_yi, 2),
            signal=signal,
            weight=0.5,
            description=desc
        )

    # -----------------------------------------------------------------------
    # 运行所有因子
    # -----------------------------------------------------------------------
    def compute_all(self) -> list[FactorResult]:
        """计算所有可用因子"""
        results = []
        factor_funcs = [
            # 动量类
            lambda: self.momentum_return(1),
            lambda: self.momentum_return(3),
            lambda: self.momentum_return(6),
            lambda: self.momentum_return(12),
            lambda: self.momentum_return_9m(),
            lambda: self.momentum_return_11m(),
            self.ma_ratio_30_75,
            lambda: self.ma_ratio_5_30(),
            self.price_to_ma200,
            lambda: self.reversal_12m_1m(),
            # 技术类
            self.rsi,
            self.macd,
            self.bollinger_position,
            self.volume_trend,
            self.kdj,
            self.williams_r,
            self.obv,
            self.cci,
            self.atr,
            lambda: self.volume_price_trend(),
            lambda: self.accumulation_distribution(),
            lambda: self.chaikin_oscillator(),
            # 趋势类
            self.ma_alignment,
            self.trend_strength,
            lambda: self.adx(),
            lambda: self.dmi(),
            # 波动/风险类
            self.historical_volatility,
            self.max_drawdown_factor,
            self.downside_volatility,
            lambda: self.sharpe_ratio(),
            lambda: self.sortino_ratio(),
            lambda: self.garman_klass_volatility(),
            lambda: self.parkinson_volatility(),
            lambda: self.rogers_satchell_volatility(),
            lambda: self.skewness_factor(),
            lambda: self.kurtosis_factor(),
            lambda: self.amihud_illiquidity(),
            # 短期反转类
            lambda: self.weekly_reversal(),
            lambda: self.biweekly_reversal(),
            # 价格形态类
            lambda: self.gap_factor(),
            # 基本面类（需要fundamentals数据）
            self.pe_factor,
            self.pb_factor,
            self.ps_factor,
            self.roe_factor,
            self.roa_factor,
            self.eps_growth_factor,
            self.revenue_growth_factor,
            self.dividend_yield_factor,
            self.market_cap_factor,
        ]
        for fn in factor_funcs:
            try:
                r = fn()
                if r is not None:
                    results.append(r)
            except Exception as e:
                print(f"[QuantFactorEngine] factor error: {e}")
        return results


# ===========================================================================
# 综合评分与概率估算
# ===========================================================================

def compute_probability(factors: list[FactorResult]) -> tuple[float, float, str]:
    """
    基于因子加权信号计算涨跌概率。

    返回: (上涨概率, 下跌概率, 趋势描述)
    """
    if not factors:
        return 0.5, 0.5, "数据不足"

    total_weight = sum(f.weight for f in factors)
    weighted_signal = sum(f.signal * f.weight for f in factors)

    # 将加权信号归一化到 [-1, 1] 区间
    if total_weight > 0:
        normalized = weighted_signal / total_weight
    else:
        normalized = 0.0

    # 映射到概率：normalized ∈ [-1, 1] → prob_up ∈ [0.15, 0.85]
    # 使用 sigmoid 型映射，避免极端概率
    prob_up = 0.5 + normalized * 0.35
    prob_up = max(0.15, min(0.85, prob_up))
    prob_down = 1.0 - prob_up

    # 趋势判断
    if normalized > 0.3:
        trend = "上涨趋势"
    elif normalized < -0.3:
        trend = "下跌趋势"
    else:
        trend = "震荡整理"

    return round(prob_up, 3), round(prob_down, 3), trend


# ===========================================================================
# 分析器主类
# ===========================================================================

class QuantAnalyzer:
    """量化分析器"""

    def __init__(self, api: str = "tencent", use_cache: bool = True):
        """
        初始化分析器
        
        :param api: 数据源名称 (tencent/eastmoney/sina)
        :param use_cache: 是否使用数据库缓存 (default: True)
        """
        self.api = api
        self.use_cache = use_cache
        
        if use_cache:
            # 使用带缓存的API
            raw_api = QuoteAPIFactory.create(api)
            self.impl = CachedQuoteAPI(raw_api)
            print(f"[QuantAnalyzer] 使用带缓存的API: {self.impl.SOURCE}")
        else:
            # 使用原始API
            self.impl = QuoteAPIFactory.create(api)
            print(f"[QuantAnalyzer] 使用原始API: {self.impl.SOURCE}")

    def analyze(self, name_key: str, days: int = 500) -> Optional[AnalysisReport]:
        """
        对指定股票进行量化因子分析。

        :param name_key: config.global_stock_list 中的键
        :param days: 拉取的历史数据天数（越多因子可用性越高）
        :return: AnalysisReport 或 None
        """
        # 检查支持性
        if not self.impl.is_supported(name_key):
            print(f"[QuantAnalyzer] api '{self.api}' does not support '{name_key}'")
            return None

        # 获取 K 线数据
        print(f"[QuantAnalyzer] 正在获取 {name_key} 最近 {days} 天K线数据 (api={self.api})...")
        quotes = self.impl.get_klines(name_key, limit=days)
        if not quotes:
            print(f"[QuantAnalyzer] 无法获取K线数据")
            return None

        print(f"[QuantAnalyzer] 获取到 {len(quotes)} 条数据，"
              f"区间: {quotes[0].date} ~ {quotes[-1].date}")

        # 获取基本面数据（可选）
        fundamentals = None
        try:
            print(f"[QuantAnalyzer] 正在获取 {name_key} 基本面数据...")
            fundamentals = self.impl.get_fundamentals(name_key)
            if fundamentals:
                print(f"[QuantAnalyzer] 获取到基本面数据: PE={fundamentals.pe_ttm:.2f}, PB={fundamentals.pb:.2f}")
            else:
                print(f"[QuantAnalyzer] 无基本面数据，将跳过基本面因子")
        except Exception as e:
            print(f"[QuantAnalyzer] 获取基本面数据失败: {e}")

        # 计算因子
        engine = QuantFactorEngine(quotes, fundamentals)
        factors = engine.compute_all()

        # 综合评分
        prob_up, prob_down, trend = compute_probability(factors)

        # 构建报告
        stock_info = config.global_stock_list.get(name_key)
        report = AnalysisReport(
            stock_name=stock_info.name if stock_info else name_key,
            stock_code=stock_info.code if stock_info else "",
            data_source=self.api,
            data_days=len(quotes),
            latest_price=quotes[-1].close,
            factors=factors,
            bullish_score=round(prob_up * 100, 1),
            bearish_score=round(prob_down * 100, 1),
            trend=trend,
            probability_up=prob_up,
            probability_down=prob_down,
        )

        # 生成总结
        report.summary = self._generate_summary(report)
        return report

    def _generate_summary(self, report: AnalysisReport) -> str:
        """生成可读的分析总结"""
        lines = []
        lines.append(f"[分析] {report.stock_name}({report.stock_code}) 量化分析报告")
        lines.append(f"   数据源: {report.data_source} | 数据量: {report.data_days}天")
        lines.append(f"   最新价: {report.latest_price:.2f}")
        lines.append("")
        lines.append("=== 综合判断 ===")
        lines.append(f"   趋势: {report.trend}")
        lines.append(f"   上涨概率: {report.probability_up * 100:.1f}%")
        lines.append(f"   下跌概率: {report.probability_down * 100:.1f}%")
        lines.append("")
        lines.append(f"=== 因子明细 ({len(report.factors)}个) ===")

        # 按类别分组
        categories = {}
        for f in report.factors:
            categories.setdefault(f.category, []).append(f)

        cat_names = {
            "momentum": "动量类", 
            "technical": "技术类",
            "trend": "趋势类", 
            "volatility": "波动/风险类",
            "reversal": "短期反转类",
            "pattern": "价格形态类",
            "valuation": "估值类",
            "quality": "质量类",
            "growth": "成长类",
            "dividend": "股息类",
            "size": "规模类"
        }
        signal_icons = {1: "[+]", -1: "[-]", 0: "[ ]"}

        for cat, factors in categories.items():
            lines.append(f"\n   [{cat_names.get(cat, cat)}]")
            for f in factors:
                icon = signal_icons.get(f.signal, "[ ]")
                lines.append(f"   {icon} {f.name}: {f.description}")

        lines.append("")
        lines.append("=== 风险提示 ===")
        lines.append("   本分析仅基于技术面量化因子，不构成投资建议。")
        lines.append("   基本面、政策面、资金面等因素未纳入考量。")

        return "\n".join(lines)


# ===========================================================================
# 命令行入口
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="量化因子分析工具")
    parser.add_argument("stock", help="股票 name_key（如 Tencent, SSE_Index）")
    parser.add_argument("--api", default="tencent", help="数据源 (default: tencent)")
    parser.add_argument("--days", type=int, default=500, help="历史数据天数 (default: 500)")
    parser.add_argument("--no-cache", action="store_true", help="不使用数据库缓存 (default: 使用缓存)")
    args = parser.parse_args()

    use_cache = not args.no_cache
    analyzer = QuantAnalyzer(api=args.api, use_cache=use_cache)
    report = analyzer.analyze(args.stock, days=args.days)
    if report:
        print("\n" + report.summary)
    else:
        print("分析失败，请检查参数")
        sys.exit(1)


if __name__ == "__main__":
    main()
