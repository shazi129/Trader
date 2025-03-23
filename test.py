import TraderUtils
import talib
import numpy
from datetime import datetime


def test_kline_api():
    print("\n".join([str(item) for item in TraderUtils.get_day_klines(
        "Tencent",
        datetime.strptime("2025-01-24","%Y-%m-%d"),
        datetime.strptime("2025-02-05","%Y-%m-%d"))]))

def test_update_stock_klines():
    TraderUtils.update_stock_klines("Tencent")


def test_talib():
    price = numpy.array([387.4,383.4, 381.2, 390.6, 395.6, 401.2, 404.2, 420.8, 417.8, 420.4])
    print(talib.SMA(price, 5))
    print(talib.MACD(price))
    print(talib.get_functions())
    print(talib.get_function_groups())


if __name__ == "__main__":
    #test_kline_api()
    #test_update_stock_klines()
    #test_talib()
    #items = ['2025-02-07', 420.4, 428.2, 432.4, 417.8, 34567530.0, 14741790976.0, 0.38, 0]
    #print(",".join([f'\'{item}\'' if isinstance(item, str) else str(item) for item in items]))
    #trader_utils.update_all_klines()
    TraderUtils.update_stocket("Tencent_14136")
    TraderUtils.update_stocket("Tencent_14210")
    TraderUtils.update_stocket("Tencent_27124")
    #trader_utils.update_socket_indicator("Tencent")