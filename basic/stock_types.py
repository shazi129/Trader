from enum import Enum
import datetime

#市场类型枚举
class StockMarket(Enum):
    NONE        = 0
    SH          = 1     #上证
    SZ          = 2     #深证
    HK          = 3     #港证
    COMEX       = 4     #纽约商品交易所

#股票信息抽象
class StockInfo:
    def __init__(self, code:str, market: StockMarket, listing_date:str, is_derivative:bool=False) -> None:
        self.code:str = code #股票代码
        self.market: StockMarket = market #所属市场
        self.listing_date:str = listing_date #上市日期
        self.is_derivative = is_derivative #是否是衍生品

    def get_list_date(self)->datetime.datetime:
        return datetime.datetime.strptime(self.listing_date, "%Y-%m-%d")

#当前用到的股票信息配置
StockList: dict[str, StockInfo] = {
    "Tencent": StockInfo('00700',  StockMarket.HK, "2004-06-16"),
    "Tencent_14136": StockInfo('14136',  StockMarket.HK, "2025-02-25", True),
    "Tencent_14210": StockInfo('14210',  StockMarket.HK, "2025-02-26", True),
    "Tencent_27124": StockInfo('27124',  StockMarket.HK, "2024-09-03", True),

    "Alibaba": StockInfo('09988', StockMarket.HK, "2019-11-26"),
    "COMEX_AG": StockInfo('SI00Y', StockMarket.COMEX, "2011-07-22"),
}

#K线信息
class KlineData:
    def __init__(self):
        self.date:str = ""         #日期, 格式: 2025-02-04
        self.open:float = 0      #开盘价
        self.close:float = 0       #收盘价
        self.high:float = 0         #最高价
        self.low:float = 0          #最低价
        self.volume:float = 0       #成交量
        self.turnover:float = 0     #成交额
        self.turnover_rate:float = 0    #换手率
        self.pe:float = 0 #市盈率

    def FIELD_NUM():
        return 9
    
    def parse(self, v: tuple)->bool:
        if len(v) != 9 or not isinstance(v, tuple):
            print("KlineData parse error, invalud v:%s" % str(v))
            return False
        self.date = str(v[0])
        self.open = float(v[1])
        self.close = float(v[2])
        self.high = float(v[3])
        self.low = float(v[4])
        self.volume = float(v[5])
        self.turnover = float(v[6])
        self.turnover_rate = float(v[7])
        self.pe = float(v[8])
        return True

    def __str__(self) -> str:
        return "date:%s, open:%f, close:%f, high:%f, low:%f, volume:%f, turnover:%f, turnover_rate:%f, pe:%f" % (
            self.date, self.open, self.close, self.high, self.low, self.volume, self.turnover, self.turnover_rate, self.pe
        )
    
#k线参数信息
class KlineIndicator:
    def __init__(self) -> None:
        self.date:str = ""         #日期, 格式: 2025-02-04

        #均线
        self.ma5:float =     0
        self.ma10:float =     0
        self.ma20:float =     0
        self.ma30:float =     0
        self.ma60:float =     0
        self.ma120:float =     0
        self.ma250:float =     0

        #布林带, 中线是20均线
        self.boll_up:float = 0
        self.boll_low:float = 0

        #KDJ
        self.k = 0
        self.d = 0
        self.j = 0

        #MACD
        self.dif = 0
        self.dea = 0
        self.macd = 0

        #RSI
        self.rsi1 = 0
        self.rsi2 = 0
        self.rsi3 = 0

        #ADOSC
        self.adosc = 0

    def __str__(self) -> str:
        return "date:%s, ma5:%f, ma10:%f, ma20:%f, ma30:%f, ma60:%f, ma120:%f, ma250:%f, boll_up:%f, boll_low:%f, \
k:%f, d:%f, j:%f, dif:%f, dea:%f, macd:%f, rsi1:%f, rsi2:%f, rsi3:%f, adosc:%f" % (
            self.date, self.ma5, self.ma10, self.ma20, self.ma30, self.ma60, self.ma120, self.ma250,
            self.boll_up, self.boll_low, self.k, self.d, self.j, self.dif, self.dea, self.macd,
            self.rsi1, self.rsi2, self.rsi3, self.adosc)