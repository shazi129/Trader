# -*- coding: utf-8 -*-
"""
算法模块 - 基于行情数据计算各种技术指标和因子

目录结构：
- indicators/    # 技术指标计算 (MA, MACD, KDJ, RSI, BOLL等)
- factors/        # 量化因子计算 (动量、趋势、波动率等)
- utils/          # 计算工具函数
"""

from .indicators import *
from .factors import *

__version__ = "1.0.0"
