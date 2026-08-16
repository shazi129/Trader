# -*- coding: utf-8 -*-
#!/usr/bin/env python

# 股票元信息已下沉到 quote_api 包内统一管理；
# 这里通过 re-export 保留 `config.global_stock_list` 旧接口，
# 业务层无需修改。新增/调整股票请编辑 quote_api/stock_meta.py。
from quote_api.stock_meta import STOCK_META as global_stock_list  # noqa: F401

# 默认行情数据源；可用值由 QuoteAPIFactory.available_sources() 提供。
QUOTE_SOURCE: str = "futu"
