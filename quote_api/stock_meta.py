# -*- coding: utf-8 -*-
"""股票元信息中心（quote_api 内部唯一数据源）

设计要点：
1. 元信息（中文名 / 默认 code / 所属市场 / 上市日期）属于"数据源无关"的概念，
   放在 quote_api 包内统一管理，避免业务层（config）反向给数据层喂数据。
2. 业务层 `config.py` 通过 re-export 的方式继续暴露 `global_stock_list`，
   旧代码 `config.global_stock_list[...]` 完全保持兼容。
3. **代码采用"默认 + override"双层结构**：
   - `StockInfo.code` 是该股票的**默认 code**（多数数据源直接用它，前缀如
     ``hk`` / ``116.`` / ``rt_`` 等由各 API 自行按市场拼）。
   - 各 `quote_api/<source>/config.json` 仅做差异化覆盖：
     * **缺 key**            → 该源支持，使用默认 code。
     * **`"key": ""`**       → 该源**不支持**这只股票（白名单显式排除）。
     * **`"key": "abc"`**    → 该源支持，用 ``"abc"`` 覆盖默认 code。
4. `StockMarket` 枚举与 `StockInfo` 元信息载体类也定义在此（原先散落在顶层
   stock_info.py，已合并进来），确保整个 quote_api 域的类型自洽。

新增/调整股票时：
- 默认情况：在这里改 STOCK_META 即可，3 家数据源自动支持。
- 某源不支持：在该源的 config.json 加 ``"name_key": ""``。
- 某源代码不同：在该源的 config.json 加 ``"name_key": "<该源专用 code>"``。
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# 市场类型枚举
# ---------------------------------------------------------------------------
class StockMarket(Enum):
    NONE        = 0
    SH          = 1     # 上证
    SZ          = 2     # 深证
    HK          = 3     # 港证
    COMEX       = 4     # 纽约商品交易所
    NASDAQ      = 5     # 纳斯达克
    NYSE        = 6     # 纽约证券交易所
    US          = 7     # 美股通用


# ---------------------------------------------------------------------------
# 股票元信息载体
# ---------------------------------------------------------------------------
class StockInfo:
    """股票元信息抽象（与数据源无关的纯静态描述）

    `code` 为该股票的**默认 code**（不带任何源的协议前缀）。各数据源若代码
    不同或不支持该股票，可通过自己的 ``config.json`` 进行 override / 排除。
    """

    def __init__(
        self,
        name: str,
        code: str,
        market: StockMarket,
        listing_date: str,
        is_derivative: bool = False,
    ) -> None:
        self.name: str = name                  # 股票名称（中文/通用名，仅用于展示）
        self.code: str = code                  # 默认 stock_code（交易所原始代码，不含前缀）
        self.market: StockMarket = market      # 所属市场
        self.listing_date: str = listing_date  # 上市日期 YYYY-MM-DD
        self.is_derivative: bool = is_derivative  # 是否衍生品

    def get_list_date(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.listing_date, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# 全量元信息表：name_key -> StockInfo
# 注意：name_key 是项目内的唯一逻辑标识；StockInfo.code 是默认 code，
#       各数据源可通过自己的 config.json 做 override 或排除。
# ---------------------------------------------------------------------------
STOCK_META: dict[str, StockInfo] = {
    "Tencent":       StockInfo('腾讯',       '00700',  StockMarket.HK,     "2004-06-16"),
    "Tencent_Put":   StockInfo('腾讯-沽',    '14136',  StockMarket.HK,     "2025-02-25"),
    "Alibaba":       StockInfo('阿里-港',    '09988',  StockMarket.HK,     "2019-11-26"),
    "NVIDIA":        StockInfo('英伟达',     'NVDA',   StockMarket.NASDAQ, "1999-01-22"),
    "COMEX_AG":      StockInfo('Comex白银',  'SI00Y',  StockMarket.COMEX,  "2011-07-22"),
}


def get_meta(name_key: str) -> Optional[StockInfo]:
    """根据 name_key 返回 StockInfo；不存在返回 None。"""
    return STOCK_META.get(name_key)


def all_keys() -> list[str]:
    """返回所有已知的 name_key。"""
    return list(STOCK_META.keys())


def register(name_key: str, info: StockInfo) -> None:
    """运行期注册新股票（外部扩展用，不影响 config.json 文件）。"""
    STOCK_META[name_key] = info


def has(name_key: str) -> bool:
    return name_key in STOCK_META
