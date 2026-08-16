"""
测试脚本：读取 config.json，拉取一次报价并打印结果。
"""

import sys
import json
from pathlib import Path

# 让子目录能 import 项目根包
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from quote_api import QuoteAPIFactory
from quote_api.quote_base import DailyQuote


CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """加载配置（精简版）"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_quote(api_name: str, name_key: str) -> DailyQuote | str | None:
    """使用指定数据源拉取单只股票的最新报价。返回 DailyQuote / "UNSUPPORTED" / None."""
    try:
        api = QuoteAPIFactory.create(api_name)
    except Exception as e:
        print(f"  [ERROR] 创建 API '{api_name}' 失败: {e}")
        return None

    if not api.is_supported(name_key):
        print(f"  [INFO] API '{api_name}' 不支持 '{name_key}'")
        return "UNSUPPORTED"

    # 取最新快照
    try:
        quote = api.get_daily_quote(name_key, date=None)
    except Exception as e:
        print(f"  [ERROR] get_daily_quote 失败: {e}")
        return None

    if quote is None:
        return None

    # 补齐昨收与涨跌
    pre_close = quote.pre_close if quote.pre_close > 0 else 0.0
    if pre_close <= 0:
        try:
            klines = api.get_klines(name_key, limit=2)
        except Exception:
            klines = []
        if len(klines) >= 2:
            pre_close = klines[-2].close
        elif klines:
            pre_close = klines[-1].close
    if pre_close <= 0:
        pre_close = quote.close

    quote.pre_close = pre_close
    quote.change = round(quote.close - pre_close, 4)
    quote.change_pct = round((quote.change / pre_close * 100) if pre_close > 0 else 0.0, 2)

    # 填充展示名
    try:
        from quote_api.stock_meta import get_meta
        info = get_meta(name_key)
        if info:
            quote.name = info.name
    except Exception:
        pass

    return quote


def format_quote(quote: DailyQuote) -> str:
    """格式化输出报价信息"""
    arrow = "↑" if quote.change > 0 else ("↓" if quote.change < 0 else "→")
    currency = quote.currency or "-"
    return (
        f"  {quote.name} ({quote.code}) | 日期: {quote.date} | 币种: {currency}\n"
        f"  收盘: {quote.close:.4f}  |  涨跌: {quote.change:+.4f}  "
        f"({quote.change_pct:+.2f}%) {arrow}\n"
        f"  开盘: {quote.open:.4f}  |  最高: {quote.high:.4f}  "
        f"|  最低: {quote.low:.4f}\n"
        f"  昨收: {quote.pre_close:.4f}  |  成交量: {quote.volume:,.0f}  "
        f"|  成交额: {quote.turnover:,.2f}\n"
        f"  数据源: {quote.source}"
    )


def main():
    config = load_config()
    api_name = config.get("api", QuoteAPIFactory.current_source())
    stocks = config.get("stocks", [])
    active = config.get("active", "")

    print("=" * 60)
    print(f"  数据源: {api_name}")
    print(f"  可用数据源: {QuoteAPIFactory.available_sources()}")
    print(f"  股票列表: {stocks}")
    print(f"  当前选中: {active}")
    print("=" * 60)

    for name_key in stocks:
        print(f"\n>>> [{name_key}]")
        quote = fetch_quote(api_name, name_key)

        if quote is None:
            print("  [WARN] 获取报价失败")
        elif quote == "UNSUPPORTED":
            print("  [SKIP] 当前数据源不支持此股票")
        else:
            print(format_quote(quote))

    print("\n" + "=" * 60)
    print("  拉取完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
