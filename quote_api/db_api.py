# -*- coding: utf-8 -*-
"""纯数据库行情源：仅从本地 SQLite 读取 K 线，绝不访问外部网络。

适用于回测场景——数据库 stock_data.db 中已存有历史 K 线
（kline_daily 表），该源直接返回这些数据，不依赖 futu/tencent/sina
等需要联网或登录的数据源。若数据库中无对应数据，则返回空列表。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from quote_api.quote_base import DailyQuote, QuoteAPI
from quote_api.repository import MarketDataRepository


class DbQuoteAPI(QuoteAPI):
    """从本地数据库读取 K 线的行情源（注册名 ``db``）。"""

    SOURCE = "db"

    def __init__(
        self,
        adjustment="none",
        *,
        repository: MarketDataRepository | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        super().__init__(adjustment=adjustment)
        self._repository = repository
        self._db_path = db_path
        self._owns_repository = repository is None

    # ------------------------------------------------------------------
    def _get_repository(self):
        if self._repository is None:
            self._repository = MarketDataRepository(self._db_path)
            self._owns_repository = True
        return self._repository

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date=None,
        end_date=None,
        limit: Optional[int] = None,
    ) -> List[DailyQuote]:
        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)
        repository = self._get_repository()
        rows = repository.get_range(name, sd, ed)
        # 补全来源标识
        for q in rows:
            q.source = self.SOURCE
        if limit is not None and limit > 0:
            # limit 取最近的 N 条（保持升序）
            rows = rows[-limit:]
        return rows

    # ------------------------------------------------------------------
    def get_daily_quote(self, name: str, date=None) -> Optional[DailyQuote]:
        target = self.normalize_date(date)
        repository = self._get_repository()
        if target is None:
            rows = repository.get_range(name, None, None)
            if not rows:
                return None
            q = rows[-1]
            q.source = self.SOURCE
            return q
        q = repository.get_by_date(name, target)
        if q is not None:
            q.source = self.SOURCE
        return q

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._repository is not None and self._owns_repository:
            try:
                self._repository.close()
            except Exception:
                pass
        self._repository = None
        self._owns_repository = False
