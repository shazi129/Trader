#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量计算并保存因子到数据库

为指定股票计算所有因子，并保存到对应的数据库表：
- {name}_Trend: 趋势类因子
- {name}_Momentum: 动量类因子
- {name}_Volume: 成交量类因子
- {name}_Risk: 风险指标
- {name}_MA_Ratio: 均线比率
"""

from __future__ import annotations

import sys
import math
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from stock_info import KlineData, KlineIndicator
from database.stock_db_utils import StockDB
from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI
from quote_api.quote_base import DailyQuote


# ===========================================================================
# 因子序列计算引擎
# ===========================================================================

class FactorSeriesEngine:
    """计算所有时间点的因子序列，输出 KlineIndicator 列表"""

    def __init__(self, quotes: list[DailyQuote]):
        self.quotes = quotes
        self.n = len(quotes)
        self.closes = [q.close for q in quotes]
        self.highs = [q.high for q in quotes]
        self.lows = [q.low for q in quotes]
        self.volumes = [q.volume for q in quotes]
        self.dates = [q.date for q in quotes]

    def compute_all(self) -> list[KlineIndicator]:
        """计算所有因子，返回 KlineIndicator 列表"""
        indicators = []
        for i in range(self.n):
            ind = KlineIndicator()
            ind.date = self.dates[i]
            indicators.append(ind)

        # 计算各类因子
        self._compute_ma(indicators)
        self._compute_bollinger(indicators)
        self._compute_kdj(indicators)
        self._compute_macd(indicators)
        self._compute_rsi(indicators)
        self._compute_ema_trend(indicators)
        self._compute_atr(indicators)
        self._compute_adx(indicators)
        self._compute_momentum(indicators)
        self._compute_volume_factors(indicators)
        self._compute_risk_factors(indicators)
        self._compute_ma_ratios(indicators)

        return indicators

    # -----------------------------------------------------------------------
    # 均线系统
    # -----------------------------------------------------------------------
    def _compute_ma(self, indicators: list[KlineIndicator]):
        """计算MA5/10/20/30/60/120/250"""
        for i in range(self.n):
            for period in [5, 10, 20, 30, 60, 120, 250]:
                if i >= period - 1:
                    ma_val = sum(self.closes[i - period + 1:i + 1]) / period
                    if period == 5:
                        indicators[i].ma5 = ma_val
                    elif period == 10:
                        indicators[i].ma10 = ma_val
                    elif period == 20:
                        indicators[i].ma20 = ma_val
                    elif period == 30:
                        indicators[i].ma30 = ma_val
                    elif period == 60:
                        indicators[i].ma60 = ma_val
                    elif period == 120:
                        indicators[i].ma120 = ma_val
                    elif period == 250:
                        indicators[i].ma250 = ma_val

    def _compute_ma_ratios(self, indicators: list[KlineIndicator]):
        """计算均线比率"""
        for i in range(self.n):
            if i >= 199:  # 需要200日
                indicators[i].ma200 = sum(self.closes[i - 199:i + 1]) / 200
                indicators[i].ma_ratio_200 = self.closes[i] / indicators[i].ma200 if indicators[i].ma200 != 0 else 0
                indicators[i].ma_ratio_5 = self.closes[i] / indicators[i].ma5 if indicators[i].ma5 != 0 else 0
                indicators[i].ma_ratio_10 = self.closes[i] / indicators[i].ma10 if indicators[i].ma10 != 0 else 0
                indicators[i].ma_ratio_20 = self.closes[i] / indicators[i].ma20 if indicators[i].ma20 != 0 else 0
                indicators[i].ma_ratio_60 = self.closes[i] / indicators[i].ma60 if indicators[i].ma60 != 0 else 0

            # 周线均线（近似）
            if i >= 149:  # 30周 ≈ 150日
                ma30w = sum(self.closes[i - 149:i + 1]) / 150
                indicators[i].ma30w = ma30w
            if i >= 374:  # 75周 ≈ 375日
                ma75w = sum(self.closes[i - 374:i + 1]) / 375
                indicators[i].ma75w = ma75w
                if ma30w != 0:
                    indicators[i].ma_ratio_30w_75w = ma30w / ma75w
                if indicators[i].ma30w != 0:
                    indicators[i].ma_ratio_5w_30w = (sum(self.closes[i - 24:i + 1]) / 25) / indicators[i].ma30w

    # -----------------------------------------------------------------------
    # 布林带
    # -----------------------------------------------------------------------
    def _compute_bollinger(self, indicators: list[KlineIndicator], period: int = 20):
        """计算布林带"""
        for i in range(self.n):
            if i >= period - 1:
                window = self.closes[i - period + 1:i + 1]
                sma = sum(window) / period
                variance = sum((x - sma) ** 2 for x in window) / period
                std = variance ** 0.5
                indicators[i].boll_up = sma + 2 * std
                indicators[i].boll_low = sma - 2 * std

    # -----------------------------------------------------------------------
    # KDJ
    # -----------------------------------------------------------------------
    def _compute_kdj(self, indicators: list[KlineIndicator], period: int = 9):
        """计算KDJ"""
        k_vals = [50.0]
        d_vals = [50.0]
        for i in range(self.n):
            if i < period - 1:
                rsv = 50.0
            else:
                low_n = min(self.lows[i - period + 1:i + 1])
                high_n = max(self.highs[i - period + 1:i + 1])
                if high_n == low_n:
                    rsv = 50.0
                else:
                    rsv = (self.closes[i] - low_n) / (high_n - low_n) * 100
            k = 2.0 / 3 * k_vals[-1] + 1.0 / 3 * rsv
            d = 2.0 / 3 * d_vals[-1] + 1.0 / 3 * k
            k_vals.append(k)
            d_vals.append(d)
            indicators[i].k = k
            indicators[i].d = d
            indicators[i].j = 3 * k - 2 * d

    # -----------------------------------------------------------------------
    # MACD
    # -----------------------------------------------------------------------
    def _compute_macd(self, indicators: list[KlineIndicator]):
        """计算MACD"""
        ema12 = self._ema(self.closes, 12)
        ema26 = self._ema(self.closes, 26)
        dif = [ema12[i] - ema26[i] for i in range(self.n)]
        dea = self._ema(dif, 9)
        for i in range(self.n):
            indicators[i].ema12 = ema12[i]
            indicators[i].ema26 = ema26[i]
            indicators[i].dif = dif[i]
            indicators[i].dea = dea[i]
            indicators[i].macd = dif[i] - dea[i]
            indicators[i].macd_hist = dif[i] - dea[i]

    # -----------------------------------------------------------------------
    # RSI
    # -----------------------------------------------------------------------
    def _compute_rsi(self, indicators: list[KlineIndicator], period: int = 14):
        """计算RSI"""
        gains = [0.0]
        losses = [0.0]
        for i in range(1, self.n):
            diff = self.closes[i] - self.closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        
        avg_gain = self._sma(gains, period)
        avg_loss = self._sma(losses, period)
        
        for i in range(self.n):
            if i >= period:
                if avg_loss[i] == 0:
                    indicators[i].rsi1 = 100.0
                else:
                    rs = avg_gain[i] / avg_loss[i]
                    indicators[i].rsi1 = 100 - (100 / (1 + rs))
                indicators[i].rsi2 = indicators[i].rsi1  # 简化：rsi2=rsi1
                indicators[i].rsi3 = indicators[i].rsi1  # 简化：rsi3=rsi1

    # -----------------------------------------------------------------------
    # EMA趋势因子
    # -----------------------------------------------------------------------
    def _compute_ema_trend(self, indicators: list[KlineIndicator]):
        """计算EMA12/26/50"""
        ema12 = self._ema(self.closes, 12)
        ema26 = self._ema(self.closes, 26)
        ema50 = self._ema(self.closes, 50)
        for i in range(self.n):
            indicators[i].ema12 = ema12[i]
            indicators[i].ema26 = ema26[i]
            indicators[i].ema50 = ema50[i]

    # -----------------------------------------------------------------------
    # ATR & ADX
    # -----------------------------------------------------------------------
    def _compute_atr(self, indicators: list[KlineIndicator], period: int = 14):
        """计算ATR"""
        tr = self._true_range()
        for i in range(self.n):
            indicators[i].tr = tr[i]
        
        # ATR (Wilder's smoothing)
        atr = []
        s = 0.0
        for i in range(self.n):
            if i == 0:
                s = tr[i]
            else:
                s = s - s / period + tr[i]
            atr.append(s)
            indicators[i].atr = s
            indicators[i].atr_pct = s / self.closes[i] * 100 if self.closes[i] != 0 else 0

    def _compute_adx(self, indicators: list[KlineIndicator], period: int = 14):
        """计算ADX"""
        tr = self._true_range()
        pdm = self._plus_dm(period)
        mdm = self._minus_dm(period)
        
        tr14 = self._smooth(tr, period)
        pdm14 = self._smooth(pdm, period)
        mdm14 = self._smooth(mdm, period)
        
        pdi = [pdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]
        mdi = [mdm14[i] / tr14[i] * 100 if tr14[i] != 0 else 0.0 for i in range(self.n)]
        
        dx_list = []
        for i in range(self.n):
            denom = pdi[i] + mdi[i]
            dx = 100 * abs(pdi[i] - mdi[i]) / denom if denom != 0 else 0.0
            dx_list.append(dx)
        
        adx_vals = self._smooth(dx_list, period)
        
        for i in range(self.n):
            indicators[i].plus_di = pdi[i]
            indicators[i].minus_di = mdi[i]
            indicators[i].adx = adx_vals[i]

    # -----------------------------------------------------------------------
    # 动量因子
    # -----------------------------------------------------------------------
    def _compute_momentum(self, indicators: list[KlineIndicator]):
        """计算动量因子"""
        for i in range(self.n):
            # MOM (N日价格变化百分比)
            for period, attr in [(5, 'mom1w'), (10, 'mom2w'), (21, 'mom1m'), 
                                  (63, 'mom3m'), (126, 'mom6m'), (189, 'mom9m'), (252, 'mom12m')]:
                if i >= period:
                    ret = (self.closes[i] / self.closes[i - period] - 1) * 100
                    setattr(indicators[i], attr, ret)
            
            # ROC (Rate of Change)
            for period, attr in [(5, 'roc1w'), (10, 'roc2w'), (21, 'roc1m'),
                                  (63, 'roc3m'), (126, 'roc6m'), (189, 'roc9m'), (252, 'roc12m')]:
                if i >= period:
                    ret = (self.closes[i] / self.closes[i - period] - 1) * 100
                    setattr(indicators[i], attr, ret)
        
        # CCI
        self._compute_cci(indicators)
        # Williams %R
        self._compute_williams_r(indicators)

    def _compute_cci(self, indicators: list[KlineIndicator], period: int = 20):
        """计算CCI"""
        for i in range(self.n):
            if i >= period - 1:
                window = [(self.highs[j] + self.lows[j] + self.closes[j]) / 3 
                         for j in range(i - period + 1, i + 1)]
                ma_tp = sum(window) / period
                md = sum(abs(x - ma_tp) for x in window) / period
                tp = (self.highs[i] + self.lows[i] + self.closes[i]) / 3
                indicators[i].cci = (tp - ma_tp) / (0.015 * md) if md != 0 else 0

    def _compute_williams_r(self, indicators: list[KlineIndicator], period: int = 14):
        """计算Williams %R"""
        for i in range(self.n):
            start = max(0, i - period + 1)
            high_n = max(self.highs[start:i + 1])
            low_n = min(self.lows[start:i + 1])
            if high_n == low_n:
                indicators[i].williams_r = -50.0
            else:
                indicators[i].williams_r = (high_n - self.closes[i]) / (high_n - low_n) * -100

    # -----------------------------------------------------------------------
    # 成交量因子
    # -----------------------------------------------------------------------
    def _compute_volume_factors(self, indicators: list[KlineIndicator]):
        """计算成交量因子"""
        # OBV
        obv = [0.0]
        for i in range(1, self.n):
            if self.closes[i] > self.closes[i - 1]:
                obv.append(obv[-1] + self.volumes[i])
            elif self.closes[i] < self.closes[i - 1]:
                obv.append(obv[-1] - self.volumes[i])
            else:
                obv.append(obv[-1])
        for i in range(self.n):
            indicators[i].obv = obv[i]
        
        # VPT
        vpt = [0.0]
        for i in range(1, self.n):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1] if self.closes[i - 1] != 0 else 0
            vpt.append(vpt[-1] + self.volumes[i] * ret)
        for i in range(self.n):
            indicators[i].vpt = vpt[i]
        
        # ADL
        adl = [0.0]
        for i in range(1, self.n):
            if self.highs[i] == self.lows[i]:
                clv = 0.0
            else:
                clv = ((self.closes[i] - self.lows[i]) - (self.highs[i] - self.closes[i])) / (self.highs[i] - self.lows[i]) * self.volumes[i]
            adl.append(adl[-1] + clv)
        for i in range(self.n):
            indicators[i].adl = adl[i]
        
        # MFI (Money Flow Index)
        self._compute_mfi(indicators)
        
        # Force Index
        for i in range(self.n):
            if i >= 1:
                indicators[i].force_index1 = self.closes[i] - self.closes[i - 1]
            if i >= 13:
                indicators[i].force_index13 = sum(self.closes[j] - self.closes[j - 1] for j in range(i - 12, i + 1))
            if i >= 21:
                indicators[i].force_index21 = sum(self.closes[j] - self.closes[j - 1] for j in range(i - 20, i + 1))

    def _compute_mfi(self, indicators: list[KlineIndicator], period: int = 14):
        """计算MFI"""
        for i in range(self.n):
            if i >= period - 1:
                positive_flow = 0.0
                negative_flow = 0.0
                for j in range(i - period + 1, i + 1):
                    tp = (self.highs[j] + self.lows[j] + self.closes[j]) / 3
                    prev_tp = (self.highs[j - 1] + self.lows[j - 1] + self.closes[j - 1]) / 3 if j > 0 else tp
                    if tp > prev_tp:
                        positive_flow += tp * self.volumes[j]
                    else:
                        negative_flow += tp * self.volumes[j]
                if negative_flow == 0:
                    indicators[i].mfi = 100.0
                else:
                    mr = positive_flow / negative_flow
                    indicators[i].mfi = 100 - (100 / (1 + mr))

    # -----------------------------------------------------------------------
    # 风险因子
    # -----------------------------------------------------------------------
    def _compute_risk_factors(self, indicators: list[KlineIndicator]):
        """计算风险因子"""
        # HV20, HV60
        for i in range(self.n):
            if i >= 19:
                returns = [math.log(self.closes[j] / self.closes[j - 1]) for j in range(i - 18, i + 1)]
                std = (sum(r ** 2 for r in returns) / 19) ** 0.5
                indicators[i].hv20 = std * (252 ** 0.5) * 100
            if i >= 59:
                returns = [math.log(self.closes[j] / self.closes[j - 1]) for j in range(i - 58, i + 1)]
                std = (sum(r ** 2 for r in returns) / 59) ** 0.5
                indicators[i].hv60 = std * (252 ** 0.5) * 100
        
        # Max Drawdown
        for i in range(self.n):
            peak = max(self.closes[:i + 1])
            dd = (peak - self.closes[i]) / peak * 100
            indicators[i].max_drawdown = dd
        
        # Sharpe, Sortino, Calmar
        for i in range(self.n):
            if i >= 251:  # 需要252个交易日
                returns = [(self.closes[j] / self.closes[j - 1] - 1) for j in range(i - 251, i + 1) if j > 0]
                mean_r = sum(returns) / len(returns)
                std_r = (sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5
                indicators[i].sharpe = (mean_r / std_r) * (252 ** 0.5) if std_r != 0 else 0
                
                # Sortino
                downsides = [r ** 2 for r in returns if r < 0]
                dd = (sum(downsides) / len(returns)) ** 0.5
                indicators[i].sortino = (mean_r / dd) * (252 ** 0.5) if dd != 0 else 0
                
                # Calmar
                max_dd = indicators[i].max_drawdown
                annual_return = (self.closes[i] / self.closes[i - 252] - 1) * 100 if i >= 252 else 0
                indicators[i].calmar = annual_return / max_dd if max_dd != 0 else 0
        
        # Skewness, Kurtosis
        for i in range(self.n):
            if i >= 251:
                returns = [(self.closes[j] / self.closes[j - 1] - 1) for j in range(i - 251, i + 1) if j > 0]
                mean_r = sum(returns) / len(returns)
                std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
                if std_r != 0:
                    skewness = sum((r - mean_r) ** 3 for r in returns) / len(returns) / (std_r ** 3)
                    kurtosis = sum((r - mean_r) ** 4 for r in returns) / len(returns) / (std_r ** 4) - 3
                    indicators[i].skewness = skewness
                    indicators[i].kurtosis = kurtosis

    # -----------------------------------------------------------------------
    # 工具函数
    # -----------------------------------------------------------------------
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

    def _sma(self, data: list[float], period: int) -> list[float]:
        """简单移动平均"""
        result = []
        for i in range(len(data)):
            if i < period:
                result.append(0.0)
            else:
                result.append(sum(data[i - period + 1:i + 1]) / period)
        return result

    def _true_range(self) -> list[float]:
        """真实波幅"""
        tr = []
        for i in range(self.n):
            c_prev = self.closes[i - 1] if i > 0 else self.closes[i]
            tr_val = max(self.highs[i], c_prev) - min(self.lows[i], c_prev)
            tr.append(tr_val)
        return tr

    def _plus_dm(self, period: int = 14) -> list[float]:
        """+DM"""
        pdm = []
        for i in range(self.n):
            if i == 0:
                pdm.append(0.0)
            else:
                up_move = self.highs[i] - self.highs[i - 1]
                down_move = self.lows[i - 1] - self.lows[i]
                pdm.append(max(up_move, 0) if up_move > down_move else 0.0)
        return pdm

    def _minus_dm(self, period: int = 14) -> list[float]:
        """-DM"""
        mdm = []
        for i in range(self.n):
            if i == 0:
                mdm.append(0.0)
            else:
                up_move = self.highs[i] - self.highs[i - 1]
                down_move = self.lows[i - 1] - self.lows[i]
                mdm.append(max(down_move, 0) if down_move > up_move else 0.0)
        return mdm

    def _smooth(self, data: list[float], period: int) -> list[float]:
        """Wilder's smoothing"""
        result = []
        s = 0.0
        for i, v in enumerate(data):
            if i == 0:
                s = v
            else:
                s = s - s / period + v
            result.append(s)
        return result


# ===========================================================================
# 批量处理与保存
# ===========================================================================

def compute_and_save_factors(stock_name: str, api_name: str = "tencent", 
                             db_path: Optional[str] = None, 
                             limit: int = 5000,
                             force_refresh: bool = False) -> bool:
    """
    计算并保存指定股票的所有因子到数据库
    
    :param stock_name: 股票名称 (如 "Tencent")
    :param api_name: API数据源 (如 "tencent")
    :param db_path: 数据库路径 (默认: database/stock_data.db)
    :param limit: 获取K线数据的数量
    :param force_refresh: 是否强制从API刷新数据（忽略缓存）
    :return: 是否成功
    """
    
    print(f"[FactorBatch] 开始处理股票: {stock_name}")
    
    # 1. 获取K线数据
    print(f"[FactorBatch] 正在从 {api_name} 获取K线数据...")
    raw_api = QuoteAPIFactory.create(api_name)
    
    if force_refresh:
        # 强制从API获取，不使用缓存
        print(f"[FactorBatch] 强制刷新模式：直接从API获取")
        quotes = raw_api.get_klines(stock_name, limit=limit)
    else:
        # 使用缓存
        cached_api = CachedQuoteAPI(raw_api)
        quotes = cached_api.get_klines(stock_name, limit=limit)
    if not quotes:
        print(f"[FactorBatch] 无法获取 {stock_name} 的K线数据")
        return False
    
    print(f"[FactorBatch] 获取到 {len(quotes)} 条K线数据")
    
    # 1.5 保存原始K线数据到数据库
    print(f"[FactorBatch] 正在保存原始K线数据到数据库...")
    from stock_info import KlineData
    db_temp = StockDB(db_path)
    db_temp.create_all_tables(stock_name)
    saved_count = 0
    for quote in quotes:
        kline = KlineData()
        kline.date = quote.date
        kline.open = quote.open
        kline.close = quote.close
        kline.high = quote.high
        kline.low = quote.low
        kline.volume = quote.volume
        kline.turnover = getattr(quote, 'turnover', 0.0)
        kline.turnover_rate = 0.0
        kline.pe = 0.0
        try:
            db_temp.write_kline_data(stock_name, kline)
            saved_count += 1
        except Exception as e:
            pass  # 跳过已存在的数据
    db_temp.close()
    print(f"[FactorBatch] 保存原始K线数据: {saved_count} 条")
    
    # 2. 计算所有因子
    print(f"[FactorBatch] 正在计算所有因子...")
    engine = FactorSeriesEngine(quotes)
    indicators = engine.compute_all()
    print(f"[FactorBatch] 因子计算完成")
    
    # 3. 连接到数据库
    db = StockDB(db_path)
    db.create_all_tables(stock_name)
    
    # 4. 保存因子到数据库
    print(f"[FactorBatch] 正在保存因子到数据库...")
    
    # 保存趋势因子
    count_trend = 0
    for ind in indicators:
        if ind.date:
            db.write_trend_data(stock_name, ind)
            count_trend += 1
    print(f"[FactorBatch] 保存趋势因子: {count_trend} 条")
    
    # 保存动量因子
    count_momentum = 0
    for ind in indicators:
        if ind.date:
            db.write_momentum_data(stock_name, ind)
            count_momentum += 1
    print(f"[FactorBatch] 保存动量因子: {count_momentum} 条")
    
    # 保存成交量因子
    count_volume = 0
    for ind in indicators:
        if ind.date:
            db.write_volume_data(stock_name, ind)
            count_volume += 1
    print(f"[FactorBatch] 保存成交量因子: {count_volume} 条")
    
    # 保存风险因子
    count_risk = 0
    for ind in indicators:
        if ind.date:
            db.write_risk_data(stock_name, ind)
            count_risk += 1
    print(f"[FactorBatch] 保存风险因子: {count_risk} 条")
    
    # 保存均线比率
    count_ma = 0
    for ind in indicators:
        if ind.date:
            db.write_ma_ratio_data(stock_name, ind)
            count_ma += 1
    print(f"[FactorBatch] 保存均线比率: {count_ma} 条")
    
    # 5. 关闭数据库
    db.close()
    
    print(f"[FactorBatch] [OK] 完成! 股票 {stock_name} 的所有因子已保存到数据库")
    return True


def batch_process_all_stocks(api_name: str = "tencent", db_path: Optional[str] = None):
    """
    批量处理所有股票
    
    :param api_name: API数据源
    :param db_path: 数据库路径
    """
    import config
    
    print(f"[FactorBatch] 开始批量处理所有股票...")
    
    for name_key, stock_info in config.global_stock_list.items():
        print(f"\n{'='*70}")
        print(f"处理: {stock_info.name} ({name_key})")
        print(f"{'='*70}")
        
        success = compute_and_save_factors(name_key, api_name, db_path)
        if success:
            print(f"[OK] {name_key} 处理成功")
        else:
            print(f"[ERROR] {name_key} 处理失败")
    
    print(f"\n[FactorBatch] 批量处理完成!")


# ===========================================================================
# 命令行入口
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="批量计算并保存因子到数据库")
    parser.add_argument("--stock", help="指定股票名称 (如 Tencent)，不指定则处理所有股票")
    parser.add_argument("--api", default="tencent", help="API数据源 (default: tencent)")
    parser.add_argument("--limit", type=int, default=5000, help="K线数据数量 (default: 5000)")
    parser.add_argument("--db", help="数据库路径 (默认: database/stock_data.db)")
    parser.add_argument("--force-refresh", action="store_true", help="强制从API刷新数据（忽略缓存）")
    args = parser.parse_args()
    
    if args.stock:
        # 处理单个股票
        success = compute_and_save_factors(args.stock, args.api, args.db, args.limit, args.force_refresh)
        sys.exit(0 if success else 1)
    else:
        # 处理所有股票
        batch_process_all_stocks(args.api, args.db)


if __name__ == "__main__":
    main()
