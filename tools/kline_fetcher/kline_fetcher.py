# -*- coding: utf-8 -*-
"""定时增量拉取日 K 线工具。

行为概述
--------
1. 自动从 ``STOCK_META`` 获取全部股票列表，按 ``config.json`` 的 ``exclude``
   字段排除不需要的股票；
2. 对每只股票：
   - 从数据库 ``kline_daily`` 表查 ``get_latest_date(name_key)``：
     * 若已有记录 → 从 **最新日期 + 1 天** 开始拉（增量补齐）；
     * 若无记录 → 从 ``StockInfo.listing_date`` 起拉；
   - 按个股 ``StockInfo.market`` 判定今日是否已收盘（A 股 15:00 / 港股 16:00 /
     美股美东 16:00）。**今天未收盘则 end_date 回退到最近工作日**，避免把盘中
     不完整的"伪日 K"写进数据库；
   - 调用 ``CachedQuoteAPI.get_klines(name, start_date, end_date)`` 抓数据：
     缓存层会自动按 ~600 交易日窗口分批向上游请求，并在内部 UPSERT 入库，
     fetcher 不需要自己控制 limit 或处理写库；
   - **写库成功后**自动物化 ``quant_feature_daily``，
     保证特征快照与 ``kline_daily`` 的最新日期一致；特征计算
     失败不影响 K 线拉取结果。
3. 单只股票失败不影响其它股票，整体输出统计。

两种运行模式
------------
- **单次**：``python tools/kline_fetcher/kline_fetcher.py run``
- **守护**：``python tools/kline_fetcher/kline_fetcher.py daemon``
  每天到 ``schedule_time`` 自动跑一次，无需 cron / 任务计划程序。

单股票操作
----------
- **补全历史**：``python tools/kline_fetcher/kline_fetcher.py fill Tencent``
  从 listing_date 拉到今天。
- **最近 N 天**：``python tools/kline_fetcher/kline_fetcher.py recent Tencent -n 60``
  强制拉取最近 N 天数据（默认 30）。
- **删除 K 线**：``python tools/kline_fetcher/kline_fetcher.py delete Tencent``
  删除该股票在 kline_daily 表中的全部记录。

设计取舍
--------
- 不依赖 ``schedule`` / ``APScheduler`` 等三方包：用最朴素的"算下一次时间 → sleep
  → 跑"循环，零依赖、Windows/Linux 都能跑。
- 行情存储走 ``MarketDataRepository``，特征存储归量化域所有。
- 股票列表不再手动维护，直接读取 ``STOCK_META`` 全量，新增股票只需在
  ``quote_api/stock_meta.py`` 加一行。
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---- 让脚本既能 ``python tools/kline_fetcher/kline_fetcher.py`` 直跑，
# ----        也能 ``python -m tools.kline_fetcher.kline_fetcher`` 运行
_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from quote_api.repository import MarketDataRepository  # noqa: E402
from quantitative.features import FeatureRepository, materialize_symbol  # noqa: E402
from quote_api import QuoteAPIFactory  # noqa: E402
from quote_api.stock_meta import StockMarket, all_keys, get_meta  # noqa: E402
from utils.logger import get_logger  # noqa: E402

try:
    # Python 3.9+ 标准库；Windows 上若缺 tzdata 包会抛 ZoneInfoNotFoundError，
    # 后面会做兜底（按本机时间近似处理）
    from zoneinfo import ZoneInfo  # noqa: E402
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

_log = get_logger(__name__)

DEFAULT_CONFIG_PATH = _THIS_DIR / "config.json"


# ---------------------------------------------------------------------------
# 配置载入
# ---------------------------------------------------------------------------
@dataclass
class FetcherConfig:
    api_name: str
    schedule_time: str                # "HH:MM"
    exclude: list[str]                # 排除的 name_key（不拉取）


def load_config(path: Path) -> FetcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    exclude = raw.get("exclude") or []
    if not isinstance(exclude, list):
        exclude = []

    configured_api = str(raw.get("api") or "").lower()
    available_apis = QuoteAPIFactory.available_sources()
    api_name = (
        configured_api
        if configured_api in available_apis
        else QuoteAPIFactory.current_source()
    )

    return FetcherConfig(
        api_name=api_name,
        schedule_time=str(raw.get("schedule_time", "17:30")),
        exclude=[str(k) for k in exclude],
    )


# ---------------------------------------------------------------------------
# 拉取逻辑
# ---------------------------------------------------------------------------
def _next_day(date_str: str) -> str:
    """'YYYY-MM-DD' → 下一天 'YYYY-MM-DD'。"""
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return (d + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


# ---- 各市场收盘判断 -------------------------------------------------------
# 返回 True 表示"今天这只股票已经收盘，今天的日 K 已经定型，可以拉"。
# 周六/周日一律视为未开盘 → False。
def _now_in_tz(tz_name: str) -> Optional[datetime.datetime]:
    """获取指定时区当前时间；ZoneInfo 不可用则返回 None。"""
    if ZoneInfo is None:
        return None
    try:
        return datetime.datetime.now(ZoneInfo(tz_name))
    except Exception:
        return None


def _is_closed_cn(now_local: datetime.datetime) -> bool:
    """A 股：周一到周五 15:00 后收盘。"""
    if now_local.weekday() >= 5:  # 周六/日
        return False
    return now_local.hour >= 15


def _is_closed_hk(now_local: datetime.datetime) -> bool:
    """港股：周一到周五 16:00 后收盘（与 A 股同一时区）。"""
    if now_local.weekday() >= 5:
        return False
    return now_local.hour >= 16


def _is_closed_us(now_local: datetime.datetime) -> bool:
    """美股：周一到周五美东 16:00 后收盘（zoneinfo 自动处理夏/冬令时）。"""
    now_et = _now_in_tz("America/New_York")
    if now_et is None:
        # 兜底：本机若是北京时间，美东 16:00 ≈ 北京次日 04:00（夏令）/ 05:00（冬令）。
        # 为安全起见，这种情况下永远视为"今日未收盘"，让 end_date 退回昨天。
        return False
    if now_et.weekday() >= 5:
        return False
    return now_et.hour >= 16


def _is_today_closed(market: StockMarket) -> bool:
    """判断指定市场今天是否已收盘。"""
    now_local = datetime.datetime.now()
    if market in (StockMarket.SH, StockMarket.SZ):
        return _is_closed_cn(now_local)
    if market == StockMarket.HK:
        return _is_closed_hk(now_local)
    if market in (StockMarket.NASDAQ, StockMarket.NYSE, StockMarket.US, StockMarket.FUTURES):
        return _is_closed_us(now_local)
    # 未知市场 → 保守按"未收盘"，end_date 回退到昨天
    return False


def _last_weekday(date: datetime.date) -> datetime.date:
    """从 date 起向前找最近的工作日（含 date 本身）。"""
    while date.weekday() >= 5:
        date -= datetime.timedelta(days=1)
    return date


def _resolve_end_date(name_key: str, today: datetime.date) -> str:
    """根据个股市场，决定可安全入库的最晚日期（end_date）。

    - 今天已收盘 → today
    - 今天未收盘 → 昨天；若昨天是周末则继续往前到最近工作日
    - 元信息缺失 → 保守按"未收盘"处理
    """
    meta = get_meta(name_key)
    market = meta.market if meta else StockMarket.NONE

    if _is_today_closed(market):
        return today.strftime("%Y-%m-%d")

    # 今天不能拉，回退到昨天最近工作日
    end = _last_weekday(today - datetime.timedelta(days=1))
    return end.strftime("%Y-%m-%d")


def _resolve_start_date(repository: MarketDataRepository,
                        name_key: str) -> Optional[str]:
    """决定起始拉取日期。

    优先级：DB 最新日期 +1 > StockInfo.listing_date。
    全部为空时返回 None，让上游 / 缓存层按其默认起点处理。
    """
    latest = repository.latest_date(name_key)
    if latest:
        return _next_day(latest)

    meta = get_meta(name_key)
    if meta and meta.listing_date:
        return meta.listing_date

    return None


def fetch_one(api, repository: MarketDataRepository, name_key: str, cfg: FetcherConfig,
              today: datetime.date) -> tuple[bool, int, str]:
    """拉取并入库单只股票。

    :return: (是否成功, 新增条数, 起始日期)
    """
    start = _resolve_start_date(repository, name_key)
    end = _resolve_end_date(name_key, today)

    if start and start > end:
        _log.info("[%s] 已是最新或当日未收盘（start=%s, end=%s），跳过",
                  name_key, start, end)
        return True, 0, start

    try:
        # 走 cached_api：内部按区间补齐 + 自动分批拉上游，
        # 调用方不需要再关心"limit / 单次最大窗口"。
        quotes = api.get_klines(name_key, start_date=start, end_date=end)
    except Exception as e:
        _log.error("[%s] 拉取失败: %s", name_key, e)
        return False, 0, start or ""

    if not quotes:
        _log.info("[%s] 区间 %s ~ %s 无新数据",
                  name_key, start or "<listing>", end)
        return True, 0, start or ""

    # cached_api 已在内部完成入库；这里只统计区间内的总条数（含已存量）。
    # 真正的"新增条数"由 cached_api 的日志输出，本函数无需再写一遍 DB。
    _log.info("[%s] 当前区间共 %d 条 (%s ~ %s)",
              name_key, len(quotes), quotes[0].date, quotes[-1].date)

    # K 线已写入行情仓储 → 同步物化特征，保证两个领域视图的最新日期一致。
    # 失败不影响本次 K 线拉取；stock_advisor 下次分析时还会兜底物化。
    try:
        feature_count = materialize_symbol(name_key, source="db")
        if feature_count:
            _log.info("[%s] 特征快照已同步（%d条）", name_key, feature_count)
        else:
            _log.warning("[%s] 特征计算返回空结果，跳过", name_key)
    except Exception as e:
        _log.error("[%s] 特征物化异常（不影响 K 线入库结果）: %s",
                   name_key, e)

    return True, len(quotes), start or ""


def run_once(config_path: Path = DEFAULT_CONFIG_PATH) -> int:
    """跑一次拉取流程，返回退出码（0 全成功，1 有失败）。"""
    cfg = load_config(config_path)
    today = datetime.date.today()

    # 直接从 STOCK_META 获取全量股票，按 exclude 过滤
    exclude_set = set(cfg.exclude)
    names = [k for k in all_keys() if k not in exclude_set]
    if not names:
        _log.warning("没有可拉取的股票（STOCK_META 为空或全部被排除），结束")
        return 0

    _log.info("=" * 60)
    _log.info("开始拉取 K 线: api=%s, adjustment=%s, today=%s, 共 %d 只",
              cfg.api_name, QuoteAPIFactory.current_adjustment().value,
              today.strftime("%Y-%m-%d"), len(names))
    _log.info("=" * 60)

    # 统一走 cached_api：内部按区间补齐 + 自动分批拉上游 + 自动写库。
    # 这样 fetcher 自己不再关心"limit / 单批最大窗口 / 写库"等细节。
    api = QuoteAPIFactory.create_with_cache(cfg.api_name)

    ok_cnt = 0
    fail_cnt = 0
    total_rows = 0

    with closing(MarketDataRepository()) as db:
        for name_key in names:
            ok, rows, _ = fetch_one(api, db, name_key, cfg, today)
            if ok:
                ok_cnt += 1
                total_rows += rows
            else:
                fail_cnt += 1

    _log.info("=" * 60)
    _log.info("完成: 成功 %d, 失败 %d, 累计写入 %d 条",
              ok_cnt, fail_cnt, total_rows)
    _log.info("=" * 60)

    return 0 if fail_cnt == 0 else 1


# ---------------------------------------------------------------------------
# 守护进程模式
# ---------------------------------------------------------------------------
def _next_run_at(now: datetime.datetime, schedule_time: str) -> datetime.datetime:
    """根据 'HH:MM' 算下一次触发时间（今天该点已过则取明天）。"""
    hh, mm = schedule_time.split(":")
    target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target


def run_daemon(config_path: Path = DEFAULT_CONFIG_PATH,
               run_on_start: bool = False) -> int:
    """守护模式：每天定时执行一次拉取。"""
    cfg = load_config(config_path)
    _log.info("守护模式启动，每日 %s 执行（按本机时区）", cfg.schedule_time)

    if run_on_start:
        _log.info("--run-on-start：先跑一次再进入定时循环")
        try:
            run_once(config_path)
        except Exception as e:
            _log.error("启动首跑异常: %s", e)

    while True:
        # 每轮重新读 cfg，方便用户改 schedule_time 后下一轮就生效
        try:
            cfg = load_config(config_path)
        except Exception as e:
            _log.error("配置载入失败，沿用上次配置: %s", e)

        now = datetime.datetime.now()
        next_at = _next_run_at(now, cfg.schedule_time)
        wait_sec = (next_at - now).total_seconds()
        _log.info("下次执行: %s（约 %.1f 小时后）",
                  next_at.strftime("%Y-%m-%d %H:%M"), wait_sec / 3600.0)

        # 分段 sleep，避免长时间 sleep 期间 Ctrl+C 没反应
        try:
            while wait_sec > 0:
                step = min(wait_sec, 60.0)
                time.sleep(step)
                wait_sec -= step
        except KeyboardInterrupt:
            _log.info("收到中断，退出守护模式")
            return 0

        try:
            run_once(config_path)
        except Exception as e:
            _log.error("本轮拉取异常: %s", e)


# ---------------------------------------------------------------------------
# 单股票操作模式
# ---------------------------------------------------------------------------
def run_fill(symbol: str, config_path: Path = DEFAULT_CONFIG_PATH) -> int:
    """补全某只股票的全部历史 K 线（从 listing_date 拉到今天）。"""
    cfg = load_config(config_path)
    today = datetime.date.today()

    _log.info("=" * 60)
    _log.info("补全 [%s] 全部历史 K 线: api=%s", symbol, cfg.api_name)
    _log.info("=" * 60)

    api = QuoteAPIFactory.create_with_cache(cfg.api_name)
    with closing(MarketDataRepository()) as db:
        ok, rows, start = fetch_one(api, db, symbol, cfg, today)
        if not ok:
            _log.error("[%s] 补全失败", symbol)
            return 1
        _log.info("[%s] 补全完成，起始日期 %s，共 %d 条", symbol, start, rows)
    return 0


def run_recent(symbol: str, days: int, config_path: Path = DEFAULT_CONFIG_PATH) -> int:
    """拉某只股票最近 N 天的 K 线（强制从 N 天前开始拉）。"""
    cfg = load_config(config_path)
    today = datetime.date.today()

    _log.info("=" * 60)
    _log.info("拉取 [%s] 最近 %d 天 K 线: api=%s", symbol, days, cfg.api_name)
    _log.info("=" * 60)

    api = QuoteAPIFactory.create_with_cache(cfg.api_name)
    with closing(MarketDataRepository()) as db:
        # 最近 N 天：end_date 按正常收盘逻辑，start_date 从 end 往前推 days 天
        end = _resolve_end_date(symbol, today)
        start_d = datetime.datetime.strptime(end, "%Y-%m-%d").date()
        start_d -= datetime.timedelta(days=days)
        start = start_d.strftime("%Y-%m-%d")

        try:
            quotes = api.get_klines(symbol, start_date=start, end_date=end)
        except Exception as e:
            _log.error("[%s] 拉取失败: %s", symbol, e)
            return 1

        if not quotes:
            _log.info("[%s] 区间 %s ~ %s 无数据", symbol, start, end)
            return 0

        _log.info("[%s] 拉取完成: %d 条 (%s ~ %s)",
                  symbol, len(quotes), quotes[0].date, quotes[-1].date)

        # 同步物化量化特征
        try:
            feature_count = materialize_symbol(symbol, source="db")
            _log.info("[%s] 特征快照已同步（%d条）", symbol, feature_count)
        except Exception as e:
            _log.warning("[%s] 特征物化异常: %s", symbol, e)
    return 0


def run_delete(symbol: str, config_path: Path = DEFAULT_CONFIG_PATH) -> int:
    """删除某只股票的所有 K 线。"""
    _log.info("=" * 60)
    _log.info("删除 [%s] 的全部 K 线", symbol)
    _log.info("=" * 60)

    with closing(MarketDataRepository()) as repository:
        deleted = repository.delete_symbol(symbol)
    with closing(FeatureRepository()) as feature_repository:
        feature_repository.delete_symbol(symbol)
        if deleted == 0:
            _log.info("[%s] 没有 K 线记录，无需删除", symbol)
        else:
            _log.info("[%s] 已删除 %d 条 K 线记录", symbol, deleted)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="定时增量拉取日 K 线入库")
    sub = parser.add_subparsers(dest="mode", help="运行模式")

    # ---- run -----------------------------------------------------------
    p_run = sub.add_parser("run", help="拉取所有股票增量 K 线")
    p_run.add_argument("--config", default=str(DEFAULT_CONFIG_PATH),
                       help="配置文件路径")

    # ---- daemon --------------------------------------------------------
    p_daemon = sub.add_parser("daemon", help="每日定时执行")
    p_daemon.add_argument("--config", default=str(DEFAULT_CONFIG_PATH),
                          help="配置文件路径")
    p_daemon.add_argument("--run-on-start", action="store_true",
                          help="启动时先跑一次")

    # ---- fill ----------------------------------------------------------
    p_fill = sub.add_parser("fill", help="补全某只股票全部历史 K 线")
    p_fill.add_argument("symbol", help="name_key，如 Tencent")
    p_fill.add_argument("--config", default=str(DEFAULT_CONFIG_PATH),
                        help="配置文件路径")

    # ---- recent --------------------------------------------------------
    p_recent = sub.add_parser("recent", help="拉某只股票最近 N 天 K 线")
    p_recent.add_argument("symbol", help="name_key，如 Tencent")
    p_recent.add_argument("-n", "--days", type=int, default=30,
                          help="拉取最近多少天（默认 30）")
    p_recent.add_argument("--config", default=str(DEFAULT_CONFIG_PATH),
                          help="配置文件路径")

    # ---- delete --------------------------------------------------------
    p_delete = sub.add_parser("delete", help="删除某只股票的所有 K 线")
    p_delete.add_argument("symbol", help="name_key，如 Tencent")
    p_delete.add_argument("--config", default=str(DEFAULT_CONFIG_PATH),
                          help="配置文件路径")

    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        return 0

    config_path = Path(args.config)
    if not config_path.exists():
        _log.error("配置文件不存在: %s", config_path)
        return 2

    try:
        if args.mode == "run":
            return run_once(config_path)
        elif args.mode == "daemon":
            return run_daemon(config_path, run_on_start=args.run_on_start)
        elif args.mode == "fill":
            return run_fill(args.symbol, config_path)
        elif args.mode == "recent":
            return run_recent(args.symbol, args.days, config_path)
        elif args.mode == "delete":
            return run_delete(args.symbol, config_path)
        else:
            return 1
    finally:
        # 释放 Factory 缓存的实例（含 Futu 的 OpenQuoteContext 网络连接、
        # 以及 CachedQuoteAPI 的 DB 连接），否则 futu 的后台线程会让进程
        # 在任务结束后仍然不退出。
        QuoteAPIFactory.clear_cache()


if __name__ == "__main__":
    sys.exit(main())
