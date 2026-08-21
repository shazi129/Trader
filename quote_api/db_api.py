# -*- coding: utf-8 -*-
"""纯数据库行情源：仅从本地 SQLite 读取 K 线，绝不访问外部网络。

适用于回测场景——数据库 stock_data.db 中已存有历史 K 线
（kline_daily 表），该源直接返回这些数据，不依赖 futu/tencent/sina
等需要联网或登录的数据源。若数据库中无对应数据，则返回空列表。
"""

from __future__ import annotations

from typing import List, Optional

from quote_api.quote_base import DailyQuote, QuoteAPI


class DbQuoteAPI(QuoteAPI):
    """从本地数据库读取 K 线的行情源（注册名 ``db``）。"""

    SOURCE = "db"

    def __init__(self, adjustment="none") -> None:
        super().__init__(adjustment=adjustment)
        self._db = None

    # ------------------------------------------------------------------
    def _get_db(self):
        if self._db is None:
            from database.stock_db_utils import StockDB
            self._db = StockDB()
        return self._db

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
        db = self._get_db()
        rows = db.get_klines_in_range(name, sd, ed)
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
        db = self._get_db()
        if target is None:
            rows = db.get_klines_in_range(name, None, None)
            if not rows:
                return None
            q = rows[-1]
            q.source = self.SOURCE
            return q
        q = db.get_daily_quote_by_date(name, target)
        if q is not None:
            q.source = self.SOURCE
        return q

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None
