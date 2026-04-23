# -*- coding: utf-8 -*-
"""yfinance QuoteAPI 自测用例

所有数据源的 test_api.py 接口一致：
    - run_self_test(name: str | None = None) -> bool
    - 可直接运行：python quote_api/yfinance/test_api.py
"""

from __future__ import annotations

import os
import sys
from typing import Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from quote_api.yfinance import YFinanceQuoteAPI  # noqa: E402


SOURCE_NAME = "yfinance"
DEFAULT_STOCK = "Tencent"


def run_self_test(name: Optional[str] = None) -> bool:
    name = name or DEFAULT_STOCK
    print("=" * 60)
    print("[%s] self-test for stock=%s" % (SOURCE_NAME, name))
    print("=" * 60)

    api = YFinanceQuoteAPI()

    quote = api.get_daily_quote(name, date=None)
    print("[daily_quote] ->", quote)
    ok_daily = quote is not None and quote.is_valid()

    klines = api.get_klines(name, limit=5)
    print("[klines] count=%d" % len(klines))
    for k in klines:
        print("   ", k)
    ok_kline = len(klines) > 0

    passed = ok_daily and ok_kline
    print("-" * 60)
    print("[%s] result: %s" % (SOURCE_NAME, "PASS" if passed else "FAIL"))
    return passed


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    ok = run_self_test(arg)
    sys.exit(0 if ok else 1)
