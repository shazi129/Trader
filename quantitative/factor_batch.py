#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量计算并保存因子到数据库。

`FactorSeriesEngine` 把整段 K 线序列一次性算完所有因子，输出
`KlineIndicator` 列表；底层算法全部委托给 `quantitative.indicators.*`，
不再重复实现 EMA/SMA/TR/+DM/-DM/Wilder smoothing 等基础原语。
"""

from __future__ import annotations

import argparse
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional

# 项目根目录（保留以兼容 `python factor_batch.py` 直接调用；
# 推荐用 `python -m quantitative.factor_batch`）
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from quantitative.factor_data import KlineIndicator
from quantitative.indicators.trend import macd as ti_macd, atr as ti_atr, adx as ti_adx, bollinger as ti_boll
from quantitative.indicators.momentum import (
    rsi as ti_rsi,
    kdj as ti_kdj,
    momentum_pct,
    cci as ti_cci,
    williams_r as ti_williams_r,
)
from quantitative.indicators.volume import (
    obv as ti_obv,
    vpt as ti_vpt,
    adl as ti_adl,
    mfi as ti_mfi,
    force_index as ti_force_index,
)
from quantitative.indicators.risk import (
    historical_volatility_series,
    max_drawdown_series,
    rolling_sharpe_sortino_calmar,
    rolling_skew_kurt,
)
from quantitative.indicators.liquidity import (
    turnover_rate_ma,
    turnover_rate_zscore,
    amount_ma,
    amount_ratio,
    amihud_illiquidity_series,
    illiquidity_rank_series,
    vol_price_corr,
    money_flow_strength,
)
from database.stock_db_utils import StockDB
from quote_api import QuoteAPIFactory
from quote_api.quote_base import DailyQuote
from utils.logger import get_logger

_log = get_logger(__name__)


# ===========================================================================
# 因子序列计算引擎
# ===========================================================================

class FactorSeriesEngine:
    """计算所有时间点的因子序列，输出 KlineIndicator 列表。

    实现策略：
    - 所有底层算法通过 `quantitative.indicators` 包共享，避免与
      `quant_analyzer` 中的 QuantFactorEngine 重复实现。
    - 各 `_compute_*` 方法只负责把"序列结果"回填到对应的
      KlineIndicator 字段上。
    """

    def __init__(self, quotes: list[DailyQuote]):
        self.quotes = quotes
        self.n = len(quotes)
        self.closes = [q.close for q in quotes]
        self.highs = [q.high for q in quotes]
        self.lows = [q.low for q in quotes]
        self.volumes = [q.volume for q in quotes]
        self.turnovers = [q.turnover for q in quotes]
        self.turnover_rates = [getattr(q, "turnover_rate", 0.0) for q in quotes]
        self.dates = [q.date for q in quotes]

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def compute_all(self) -> list[KlineIndicator]:
        indicators = [KlineIndicator() for _ in range(self.n)]
        for i in range(self.n):
            indicators[i].date = self.dates[i]

        self._compute_ma(indicators)
        self._compute_bollinger(indicators)
        self._compute_kdj(indicators)
        self._compute_macd(indicators)
        self._compute_rsi(indicators)
        self._compute_ema_trend(indicators)
        self._compute_atr_adx(indicators)
        self._compute_momentum(indicators)
        self._compute_volume_factors(indicators)
        self._compute_risk_factors(indicators)
        self._compute_ma_ratios(indicators)
        self._compute_liquidity_factors(indicators)
        return indicators

    # ------------------------------------------------------------------
    # 均线
    # ------------------------------------------------------------------
    _MA_PERIODS = (
        (5, "ma5"), (10, "ma10"), (20, "ma20"),
        (30, "ma30"), (60, "ma60"), (120, "ma120"), (250, "ma250"),
    )

    def _compute_ma(self, indicators: list[KlineIndicator]):
        # 用增量和实现 O(n) MA，避免每根 bar 重新求和（原版本是 O(n*period)）
        for period, attr in self._MA_PERIODS:
            if self.n < period:
                continue
            window_sum = sum(self.closes[:period])
            setattr(indicators[period - 1], attr, window_sum / period)
            for i in range(period, self.n):
                window_sum += self.closes[i] - self.closes[i - period]
                setattr(indicators[i], attr, window_sum / period)

    def _compute_ma_ratios(self, indicators: list[KlineIndicator]):
        # MA200 / 200日比 / 5/10/20/60 与收盘比
        if self.n >= 200:
            window_sum = sum(self.closes[:200])
            indicators[199].ma200 = window_sum / 200
            for i in range(200, self.n):
                window_sum += self.closes[i] - self.closes[i - 200]
                indicators[i].ma200 = window_sum / 200
        for i in range(self.n):
            ind = indicators[i]
            if ind.ma200:
                ind.ma_ratio_200 = self.closes[i] / ind.ma200
            if ind.ma5:
                ind.ma_ratio_5 = self.closes[i] / ind.ma5
            if ind.ma10:
                ind.ma_ratio_10 = self.closes[i] / ind.ma10
            if ind.ma20:
                ind.ma_ratio_20 = self.closes[i] / ind.ma20
            if ind.ma60:
                ind.ma_ratio_60 = self.closes[i] / ind.ma60

        # 周线均线（近似：30 周 ≈ 150 日，75 周 ≈ 375 日，5 周 ≈ 25 日）
        if self.n >= 150:
            for i in range(149, self.n):
                indicators[i].ma30w = sum(self.closes[i - 149:i + 1]) / 150
        if self.n >= 375:
            for i in range(374, self.n):
                indicators[i].ma75w = sum(self.closes[i - 374:i + 1]) / 375
                if indicators[i].ma75w:
                    indicators[i].ma_ratio_30w_75w = indicators[i].ma30w / indicators[i].ma75w
        if self.n >= 150:  # 5W/30W 至少需要 30 周
            for i in range(149, self.n):
                if indicators[i].ma30w and self.n - 1 - i >= 0 and i >= 24:
                    ma5w = sum(self.closes[i - 24:i + 1]) / 25
                    indicators[i].ma_ratio_5w_30w = ma5w / indicators[i].ma30w

    # ------------------------------------------------------------------
    # 布林带 / KDJ / MACD / RSI / EMA / ATR / ADX
    # ------------------------------------------------------------------
    def _compute_bollinger(self, indicators: list[KlineIndicator], period: int = 20):
        boll = ti_boll(self.closes, period=period, k=2.0)
        for i in range(self.n):
            up, lo = boll.upper[i], boll.lower[i]
            if up == up:  # not nan
                indicators[i].boll_up = up
                indicators[i].boll_low = lo

    def _compute_kdj(self, indicators: list[KlineIndicator], period: int = 9):
        res = ti_kdj(self.highs, self.lows, self.closes, period=period)
        for i in range(self.n):
            indicators[i].k = res.k[i]
            indicators[i].d = res.d[i]
            indicators[i].j = res.j[i]

    def _compute_macd(self, indicators: list[KlineIndicator]):
        res = ti_macd(self.closes, fast=12, slow=26, signal=9)
        for i in range(self.n):
            indicators[i].ema12 = res.ema_fast[i]
            indicators[i].ema26 = res.ema_slow[i]
            indicators[i].dif = res.dif[i]
            indicators[i].dea = res.dea[i]
            indicators[i].macd = res.hist[i]
            indicators[i].macd_hist = res.hist[i]

    def _compute_rsi(self, indicators: list[KlineIndicator], period: int = 14):
        # 使用 simple 模式与历史入库数据保持一致（旧实现是窗口内简单平均）。
        # QuantFactorEngine 的单点 RSI 走标准 Wilder（默认值）以做信号判断，
        # 二者分工明确：批量入库 = 长期可比；单点信号 = 教科书定义。
        rsi_seq = ti_rsi(self.closes, period=period, mode="simple")
        for i in range(self.n):
            v = rsi_seq[i]
            if v != v:  # nan -> 留默认 0
                continue
            indicators[i].rsi1 = v
            indicators[i].rsi2 = v
            indicators[i].rsi3 = v

    def _compute_ema_trend(self, indicators: list[KlineIndicator]):
        # MACD 已写入 ema12/ema26；这里补 ema50
        from quantitative.indicators.primitives import ema as ti_ema
        ema50 = ti_ema(self.closes, 50)
        for i in range(self.n):
            indicators[i].ema50 = ema50[i]

    def _compute_atr_adx(self, indicators: list[KlineIndicator], period: int = 14):
        atr_res = ti_atr(self.highs, self.lows, self.closes, period=period)
        adx_res = ti_adx(self.highs, self.lows, self.closes, period=period)
        for i in range(self.n):
            indicators[i].tr = atr_res.tr[i]
            indicators[i].atr = atr_res.atr[i]
            indicators[i].atr_pct = atr_res.atr_pct[i]
            indicators[i].plus_di = adx_res.plus_di[i]
            indicators[i].minus_di = adx_res.minus_di[i]
            indicators[i].adx = adx_res.adx[i]

    # ------------------------------------------------------------------
    # 动量 / 量价 / 风险
    # ------------------------------------------------------------------
    _MOM_PERIODS = (
        (5, "mom1w", "roc1w"),
        (10, "mom2w", "roc2w"),
        (21, "mom1m", "roc1m"),
        (63, "mom3m", "roc3m"),
        (126, "mom6m", "roc6m"),
        (189, "mom9m", "roc9m"),
        (252, "mom12m", "roc12m"),
    )

    def _compute_momentum(self, indicators: list[KlineIndicator]):
        for period, mom_attr, roc_attr in self._MOM_PERIODS:
            seq = momentum_pct(self.closes, period)
            for i in range(self.n):
                if i >= period:
                    setattr(indicators[i], mom_attr, seq[i])
                    setattr(indicators[i], roc_attr, seq[i])

        cci_seq = ti_cci(self.highs, self.lows, self.closes, period=20)
        wr_seq = ti_williams_r(self.highs, self.lows, self.closes, period=14)
        for i in range(self.n):
            indicators[i].cci = cci_seq[i]
            indicators[i].williams_r = wr_seq[i]

    def _compute_volume_factors(self, indicators: list[KlineIndicator]):
        obv_seq = ti_obv(self.closes, self.volumes)
        vpt_seq = ti_vpt(self.closes, self.volumes)
        adl_seq = ti_adl(self.highs, self.lows, self.closes, self.volumes)
        mfi_seq = ti_mfi(self.highs, self.lows, self.closes, self.volumes, period=14)
        f1 = ti_force_index(self.closes, self.volumes, period=1)
        f13 = ti_force_index(self.closes, self.volumes, period=13)
        f21 = ti_force_index(self.closes, self.volumes, period=21)
        for i in range(self.n):
            indicators[i].obv = obv_seq[i]
            indicators[i].vpt = vpt_seq[i]
            indicators[i].adl = adl_seq[i]
            indicators[i].mfi = mfi_seq[i]
            indicators[i].force_index1 = f1[i]
            indicators[i].force_index13 = f13[i]
            indicators[i].force_index21 = f21[i]

    def _compute_risk_factors(self, indicators: list[KlineIndicator]):
        hv20 = historical_volatility_series(self.closes, period=20)
        hv60 = historical_volatility_series(self.closes, period=60)
        md = max_drawdown_series(self.closes)
        sharpe, sortino, calmar = rolling_sharpe_sortino_calmar(
            self.closes, md, period=252
        )
        skew, kurt = rolling_skew_kurt(self.closes, period=252)
        for i in range(self.n):
            indicators[i].hv20 = hv20[i]
            indicators[i].hv60 = hv60[i]
            indicators[i].max_drawdown = md[i]
            indicators[i].sharpe = sharpe[i]
            indicators[i].sortino = sortino[i]
            indicators[i].calmar = calmar[i]
            indicators[i].skewness = skew[i]
            indicators[i].kurtosis = kurt[i]

    # ------------------------------------------------------------------
    # 流动性 / 资金面（B 类：从 K 线派生）
    # ------------------------------------------------------------------
    def _compute_liquidity_factors(self, indicators: list[KlineIndicator]):
        tr_ma5 = turnover_rate_ma(self.turnover_rates, 5)
        tr_ma20 = turnover_rate_ma(self.turnover_rates, 20)
        tr_z20 = turnover_rate_zscore(self.turnover_rates, period=20)
        amt_ma5 = amount_ma(self.turnovers, 5)
        amt_ma20 = amount_ma(self.turnovers, 20)
        amt_ratio = amount_ratio(self.turnovers, fast=5, slow=20)
        amihud_seq = amihud_illiquidity_series(self.closes, self.turnovers,
                                               period=20)
        illiq_rank = illiquidity_rank_series(amihud_seq, lookback=252)
        vp_corr = vol_price_corr(self.closes, self.turnovers, period=20)
        mfs = money_flow_strength(self.closes, self.turnovers, period=20)
        for i in range(self.n):
            ind = indicators[i]
            ind.turnover_rate = self.turnover_rates[i]
            ind.turnover_rate_ma5 = tr_ma5[i]
            ind.turnover_rate_ma20 = tr_ma20[i]
            ind.turnover_rate_z20 = tr_z20[i]
            ind.amount_ma5 = amt_ma5[i]
            ind.amount_ma20 = amt_ma20[i]
            ind.amount_ratio_5_20 = amt_ratio[i]
            ind.amihud = amihud_seq[i]
            ind.illiquidity_rank = illiq_rank[i]
            ind.vol_price_corr_20 = vp_corr[i]
            ind.money_flow_strength = mfs[i]


# ===========================================================================
# 批量处理与保存
# ===========================================================================

#: 因子计算所需的最少 K 线条数（用于 sanity check）。
#: 取值依据：最长窗口 ma75w = 375 根 + 252 日风险滚动 + EMA/HV 预热缓冲 ≈ 600。
#: 不再用作"拉取条数限制"——拉取范围由 cached_api 内部按 [meta.listing_date, today]
#: 区间补齐策略决定。
MIN_BARS_FOR_FACTORS = 600


def compute_and_save_factors(stock_name: str, api_name: str = "tencent",
                             db_path: Optional[str] = None,
                             limit: Optional[int] = None,
                             force_refresh: bool = False) -> bool:
    """计算并保存指定股票的所有因子到数据库。

    :param limit: 可选的"只用最近 N 条 K 线参与计算"上限。``None`` 表示用 DB 中
        ``[meta.listing_date, today]`` 的全部数据。**不影响上游拉取范围**——
        拉取永远按区间补齐策略，由 ``CachedQuoteAPI`` 决定是否分批请求上游。
    """

    _log.info("开始处理股票: %s", stock_name)

    # 1. 获取K线数据（Factory 内部已做单例缓存，重复调用不会创建新实例）
    _log.info("正在从 %s 获取K线数据...", api_name)
    if force_refresh:
        # 强制刷新模式：跳过 DB 缓存，直接走上游全区间拉取（不再用 limit）
        _log.info("强制刷新模式：直接从API获取（按区间）")
        raw_api = QuoteAPIFactory.create(api_name)
        # 让上游按其默认起点拉（区间内），再由本地切片
        quotes = raw_api.get_klines(stock_name)
    else:
        cached_api = QuoteAPIFactory.create_with_cache(api_name)
        # 不传 limit/start_date：CachedQuoteAPI 会按 meta.listing_date ~ today
        # 区间补齐缺失数据，并在内部分批向上游请求。
        quotes = cached_api.get_klines(stock_name)
    if not quotes:
        _log.warning("无法获取 %s 的K线数据", stock_name)
        return False

    # 调用方传 limit 时仅做尾部截断（用于"只算最近 N 条"的场景）
    if limit and limit > 0 and len(quotes) > limit:
        quotes = quotes[-limit:]

    if len(quotes) < MIN_BARS_FOR_FACTORS:
        _log.warning("获取到 %d 条K线，少于因子最长窗口 %d 条，部分因子可能为空",
                     len(quotes), MIN_BARS_FOR_FACTORS)
    else:
        _log.info("获取到 %d 条K线数据", len(quotes))

    # 2. 因子计算 + 入库（同一个 DB 连接里完成所有写入）
    _log.info("正在计算所有因子...")
    engine = FactorSeriesEngine(quotes)
    indicators = engine.compute_all()
    _log.info("因子计算完成")

    valid_inds = [ind for ind in indicators if ind.date]
    with closing(StockDB(db_path)) as db:
        try:
            db.write_kline_data_many(stock_name, quotes)
            _log.info("保存原始K线数据: %d 条", len(quotes))
        except Exception as e:
            _log.error("保存原始K线数据失败: %s", e)

        _log.info("正在批量保存 7 张因子表...")
        db.write_all_indicators_many(stock_name, valid_inds)
        _log.info("批量保存完成: %d 条 × 7 张因子表", len(valid_inds))

    _log.info("[OK] 完成! 股票 %s 的所有因子已保存到数据库", stock_name)
    return True


def batch_process_all_stocks(api_name: str = "tencent",
                             db_path: Optional[str] = None):
    """批量处理 config.global_stock_list 中所有股票。"""
    import config

    _log.info("开始批量处理所有股票...")
    try:
        for name_key, stock_info in config.global_stock_list.items():
            _log.info("=" * 70)
            _log.info("处理: %s (%s)", stock_info.name, name_key)
            _log.info("=" * 70)
            success = compute_and_save_factors(name_key, api_name, db_path)
            _log.info("[%s] %s 处理%s",
                      "OK" if success else "ERROR",
                      name_key,
                      "成功" if success else "失败")
        _log.info("批量处理完成!")
    finally:
        # 释放 Factory 中缓存的 CachedQuoteAPI（关闭 DB 连接）
        QuoteAPIFactory.clear_cache()


# ===========================================================================
# 命令行入口
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="批量计算并保存因子到数据库")
    parser.add_argument("--stock", help="指定股票名称 (如 Tencent)，不指定则处理所有")
    parser.add_argument("--api", default="tencent", help="API数据源 (default: tencent)")
    parser.add_argument("--limit", type=int, default=None,
                        help="可选：只用最近 N 条 K 线参与计算（默认用全部）")
    parser.add_argument("--db", help="数据库路径 (默认: database/stock_data.db)")
    parser.add_argument("--force-refresh", action="store_true",
                        help="强制从API刷新数据（忽略缓存）")
    args = parser.parse_args()

    if args.stock:
        ok = compute_and_save_factors(args.stock, args.api, args.db,
                                      args.limit, args.force_refresh)
        QuoteAPIFactory.clear_cache()
        sys.exit(0 if ok else 1)
    else:
        batch_process_all_stocks(args.api, args.db)


if __name__ == "__main__":
    main()
