from enum import Enum
import datetime

#市场类型枚举
class StockMarket(Enum):
    NONE        = 0
    SH          = 1     #上证
    SZ          = 2     #深证
    HK          = 3     #港证
    COMEX       = 4     #纽约商品交易所
    NASDAQ      = 5     #纳斯达克
    NYSE        = 6     #纽约证券交易所
    US          = 7     #美股通用

#股票信息抽象
class StockInfo:
    def __init__(self, name: str, code:str, market: StockMarket, listing_date:str, is_derivative:bool=False) -> None:
        self.name:str = name #股票名称
        self.code:str = code #股票代码
        self.market: StockMarket = market #所属市场
        self.listing_date:str = listing_date #上市日期
        self.is_derivative = is_derivative #是否是衍生品

    def get_list_date(self)->datetime.datetime:
        return datetime.datetime.strptime(self.listing_date, "%Y-%m-%d")

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
        return 8

    def parse(self, v: tuple)->bool:
        if len(v) != 8 or not isinstance(v, tuple):
            print("KlineData parse error, invalid v:%s" % str(v))
            return False
        self.date = str(v[0])
        self.open = float(v[1])
        self.close = float(v[2])
        self.high = float(v[3])
        self.low = float(v[4])
        self.volume = float(v[5])
        self.turnover = float(v[6])
        self.turnover_rate = float(v[7])
        return True

    def __str__(self) -> str:
        return "date:%s, open:%f, close:%f, high:%f, low:%f, volume:%f, turnover:%f, turnover_rate:%f" % (
            self.date, self.open, self.close, self.high, self.low, self.volume, self.turnover, self.turnover_rate
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

        # ========================================
        # 新增：趋势类因子
        # ========================================
        # EMA
        self.ema12:float = 0
        self.ema26:float = 0
        self.ema50:float = 0

        # MACD柱状图
        self.macd_hist:float = 0

        # ADX
        self.adx:float = 0
        self.plus_di:float = 0
        self.minus_di:float = 0

        # ATR
        self.tr:float = 0
        self.atr:float = 0
        self.atr_pct:float = 0

        # ========================================
        # 新增：动量类因子
        # ========================================
        # 多周期动量
        self.mom1w:float = 0
        self.mom2w:float = 0
        self.mom1m:float = 0
        self.mom3m:float = 0
        self.mom6m:float = 0
        self.mom9m:float = 0
        self.mom12m:float = 0

        # 变动率
        self.roc1w:float = 0
        self.roc2w:float = 0
        self.roc1m:float = 0
        self.roc3m:float = 0
        self.roc6m:float = 0
        self.roc9m:float = 0
        self.roc12m:float = 0

        # CCI & Williams %R
        self.cci:float = 0
        self.williams_r:float = 0

        # ========================================
        # 新增：成交量类因子
        # ========================================
        self.obv:float = 0
        self.vpt:float = 0
        self.adl:float = 0
        self.mfi:float = 0
        self.force_index1:float = 0
        self.force_index13:float = 0
        self.force_index21:float = 0

        # ========================================
        # 新增：波动率类因子
        # ========================================
        self.hv20:float = 0
        self.hv60:float = 0
        self.max_drawdown:float = 0
        self.volatility:float = 0

        # ========================================
        # 新增：均线比率因子
        # ========================================
        self.ma_ratio_5:float = 0
        self.ma_ratio_10:float = 0
        self.ma_ratio_20:float = 0
        self.ma_ratio_60:float = 0
        self.ma_ratio_200:float = 0
        self.ma200:float = 0

        # ========================================
        # 新增：风险调整收益类因子
        # ========================================
        self.sharpe: float = 0
        self.sortino: float = 0
        self.calmar: float = 0
        self.skewness: float = 0
        self.kurtosis: float = 0

        # ========================================
        # 新增：周线因子
        # ========================================
        self.ma30w:float = 0
        self.ma75w:float = 0
        self.ma_ratio_30w_75w:float = 0
        self.ma_ratio_5w_30w:float = 0

    def __str__(self) -> str:
        return "date:%s, ma5:%f, ma10:%f, ma20:%f, ma30:%f, ma60:%f, ma120:%f, ma250:%f, boll_up:%f, boll_low:%f, \
k:%f, d:%f, j:%f, dif:%f, dea:%f, macd:%f, rsi1:%f, rsi2:%f, rsi3:%f, adosc:%f, \
ema12:%f, ema26:%f, ema50:%f, macd_hist:%f, adx:%f, plus_di:%f, minus_di:%f, \
tr:%f, atr:%f, atr_pct:%f, \
mom1w:%f, mom2w:%f, mom1m:%f, mom3m:%f, mom6m:%f, mom9m:%f, mom12m:%f, \
roc1w:%f, roc2w:%f, roc1m:%f, roc3m:%f, roc6m:%f, roc9m:%f, roc12m:%f, \
cci:%f, williams_r:%f, \
obv:%f, vpt:%f, adl:%f, mfi:%f, force_index1:%f, force_index13:%f, force_index21:%f, \
hv20:%f, hv60:%f, max_drawdown:%f, volatility:%f, \
ma_ratio_5:%f, ma_ratio_10:%f, ma_ratio_20:%f, ma_ratio_60:%f, ma_ratio_200:%f, ma200:%f, \
ma30w:%f, ma75w:%f, ma_ratio_30w_75w:%f, ma_ratio_5w_30w:%f" % (
            self.date, self.ma5, self.ma10, self.ma20, self.ma30, self.ma60, self.ma120, self.ma250,
            self.boll_up, self.boll_low, self.k, self.d, self.j, self.dif, self.dea, self.macd,
            self.rsi1, self.rsi2, self.rsi3, self.adosc,
            self.ema12, self.ema26, self.ema50, self.macd_hist, self.adx, self.plus_di, self.minus_di,
            self.tr, self.atr, self.atr_pct,
            self.mom1w, self.mom2w, self.mom1m, self.mom3m, self.mom6m, self.mom9m, self.mom12m,
            self.roc1w, self.roc2w, self.roc1m, self.roc3m, self.roc6m, self.roc9m, self.roc12m,
            self.cci, self.williams_r,
            self.obv, self.vpt, self.adl, self.mfi, self.force_index1, self.force_index13, self.force_index21,
            self.hv20, self.hv60, self.max_drawdown, self.volatility,
            self.ma_ratio_5, self.ma_ratio_10, self.ma_ratio_20, self.ma_ratio_60, self.ma_ratio_200, self.ma200,
            self.ma30w, self.ma75w, self.ma_ratio_30w_75w, self.ma_ratio_5w_30w)
    

class DataValue:
    def __init__(self, date:str, value:float) -> None:
        self.date = date
        self.value = value

    def __str__(self) -> str:
        return "date:%s, value:%f" % (self.date, self.value)