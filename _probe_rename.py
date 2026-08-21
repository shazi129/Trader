import sys, os
sys.path.insert(0, os.getcwd())
# 验证新包路径
from quantitative.fields import KlineIndicator
from quantitative.analyzer.factors.manager import FactorManager
from quantitative.analyzer.factors.registry import instantiate_all
print("fields.KlineIndicator:", KlineIndicator)
print("analyzer.factors.FactorManager:", FactorManager)
print("因子数量:", len(instantiate_all()))
