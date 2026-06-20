# 东方财富 API 连不上问题排查与处理

> 日期：2026-06-20
> 影响范围：`quote_api/eastmoney/eastmoney_quote.py`、`utils/logger.py`

## 1. 问题描述

使用东方财富（EastMoney）API 获取实时行情和 K 线数据时，**所有股票**（腾讯、阿里、英伟达、白银等）**全部报错**，错误信息为：

```
RemoteDisconnected('Remote end closed connection without response')
```

`tools/stock_widget/test.py` 中 5 只股票无一成功。

## 2. 排查过程

### 2.1 初步假设（已排除）

| 假设 | 排查方式 | 结论 |
|------|----------|------|
| Cookie 缺失导致反爬 | 先访问 `quote.eastmoney.com` 首页获取 Cookie 再请求 API | ❌ 无效，依旧断连 |
| TLS 指纹检测 | 使用 `curl_cffi` 模拟 Chrome 124/131 TLS 指纹 | ❌ 无效，TCP 握手后直接 RST |
| `ut` 参数过期 | 尝试不同 `ut` 值 | ❌ 无效 |
| Referer 缺失 | 添加 Referer 头 | ❌ 无效 |
| HTTP vs HTTPS | 尝试 HTTP 明文请求 | ❌ 无效 |

### 2.2 路由级诊断

编写诊断脚本对东方财富各子域名逐一测试：

```
quote.eastmoney.com           → ✅ 200 OK
so.eastmoney.com              → ✅ 200 OK
datacenter.eastmoney.com      → ✅ 200 OK
push2.eastmoney.com           → ❌ RemoteDisconnected
push2his.eastmoney.com        → ❌ RemoteDisconnected
```

### 2.3 结论

**`push2.eastmoney.com`（IP: `47.112.165.11`）和 `push2his.eastmoney.com` 在当前网络环境下被服务端直接拒绝 TCP 连接。** 其他东方财富子域名均可正常访问，唯独这两台 API 服务器被封锁。

这不是代码层面的问题（不是 Cookie、TLS 指纹、UA、Referer 等能解决的），而是**网络/IP 级别的服务端阻断**。

## 3. 替代方案验证

| 数据源 | 腾讯(港股) | 阿里(港股) | 英伟达(美股) | 白银(期货) |
|--------|-----------|-----------|-------------|-----------|
| Tencent API | ✅ | — | ❌ | — |
| Sina API | ✅ | ✅ | ✅ | ✅ |

**Sina API 对全部 5 只股票均正常工作**，可作为替换方案。

## 4. 处理措施

### 4.1 短期：切换数据源

在 `tools/stock_widget/config.json` 中将 `"api"` 从 `"eastmoney"` 改为 `"sina"`。

> 注意：eastmoney 代码本身保留不动，待网络环境恢复后可随时切回。

### 4.2 长期：日志基础设施升级

为便于未来快速定位类似问题，升级了项目的日志系统。

**`utils/logger.py`** 改动：

- 新增 **FileHandler**，写入 `logs/trader.log`（DEBUG 级别），带时间戳
- 原有 **StreamHandler** 保持 INFO 级别，控制台输出不受影响
- 日志文件格式：

  ```
  [2026-06-20 11:43:41] [trader.quote_api.eastmoney.eastmoney_quote] DEBUG  [EastMoney] GET https://push2.eastmoney.com/api/qt/stock/get?secid=...
  ```

- `logs/` 目录已加入 `.gitignore`

**`quote_api/eastmoney/eastmoney_quote.py`** 改动：

- 使用项目统一日志工具 `utils.logger.get_logger(__name__)` 替代裸 `logging.getLogger`
- 三处 API 请求前添加 `_logger.debug()` 打印完整请求 URL，便于排查
- 删除 `print()` 调试代码

### 4.3 日志使用方式

```python
# 使用时 DEBUG 级别的 URL 记录会自动写入 logs/trader.log
# 无需额外配置，导入模块即自动初始化

# 如需在控制台也看到 DEBUG 日志：
from utils.logger import configure_root_level
import logging
configure_root_level(logging.DEBUG)
```

## 5. 涉及文件

| 文件 | 改动 |
|------|------|
| `tools/stock_widget/config.json` | `api` 改为 `sina`（可随时改回） |
| `utils/logger.py` | 新增 FileHandler（`logs/trader.log`） |
| `quote_api/eastmoney/eastmoney_quote.py` | 使用项目统一 logger，debug 打印请求 URL |
| `.gitignore` | 新增 `logs/` |
