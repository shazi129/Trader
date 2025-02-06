import trader_utils
from api import api_base
from datetime import datetime

def test_kline_api():
    print("\n".join([str(item) for item in trader_utils.get_day_klines(
        "Tencent",
        datetime.strptime("2025-01-24","%Y-%m-%d"),
        datetime.strptime("2025-02-05","%Y-%m-%d"))]))

def test_update_db():
    trader_utils.update_stock_db("Tencent")

if __name__ == "__main__":
    #test_kline_api()
    test_update_db()
    
    #update_stock_db(StockCode.TX)
    #stock_db = stock_db_utils.StockDB()
    #print (stock_db.get_lastest_date(StockCode.AG))
    #print(get_date_span("1990-01-01", 100))
    #print((datetime.strptime("2025-02-04", "%Y-%m-%d") < datetime.strptime("2025-02-05", "%Y-%m-%d")))