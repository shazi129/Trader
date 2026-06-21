# 东方财富 API 连不上问题排查与处理

> 日期：2026-06-20（持续更新）
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
| Cookie 缺失导致反爬 | 先访问 `quote.eastmoney.com` 首页获取 Cookie 再请求 API | ❌ 无效 |
| `ut` 参数过期 | 尝试不同 `ut` 值 | ❌ 无效 |
| Referer 缺失 | 添加 Referer 头 | ❌ 无效 |

### 2.2 域名级诊断

```
quote.eastmoney.com           → ✅ 200 OK
so.eastmoney.com              → ✅ 200 OK
datacenter.eastmoney.com      → ✅ 200 OK
push2.eastmoney.com           → ❌ RemoteDisconnected
push2his.eastmoney.com        → ❌ RemoteDisconnected
```

只有 API 专用域名 (`push2` / `push2his`) 被阻断，普通页面域名正常。

### 2.3 关键转折：浏览器能通

用户反馈：**同一 URL 在浏览器中直接输入就可以正常返回数据**，但代码里不行。这推翻了「IP 封锁」的假设——如果是 IP 封锁，浏览器也应该不通。

### 2.4 HTTP 协议版本排查

| 客户端 | HTTP 版本 | 结果 |
|--------|----------|------|
| Python `requests` | HTTP/1.1 | ❌ RemoteDisconnected |
| Python `httpx` | HTTP/1.1 | ❌ RemoteDisconnected |
| Python `httpx` | HTTP/2 | ❌ RemoteDisconnected |
| 系统 `curl.exe` | HTTP/1.1 | ❌ 失败 |
| 系统 `curl.exe` | HTTP/2 | ❌ 失败 |

### 2.5 TLS 指纹绕过尝试

| 方式 | 结果 |
|------|------|
| `curl_cffi` 模拟 Chrome 124 指纹 | ❌ 失败 |
| `curl_cffi` 模拟 Chrome 131 指纹 | ❌ 失败 |

### 2.6 代理排查

发现 Windows 系统代理已开启（`127.0.0.1:10808`，SOCKS5），但通过该代理请求同样失败。

| 代理方式 | 结果 |
|----------|------|
| 直连（不走代理） | ❌ RemoteDisconnected |
| HTTP 代理 `127.0.0.1:10808` | ❌ ProxyError |
| SOCKS5 代理 `127.0.0.1:10808` | ❌ RemoteDisconnected |

代理端口本身可达，但代理转发出去的请求仍然被 `push2.eastmoney.com` 服务端拒绝。

### 2.7 VPN 验证（关键转折）

用户将 VPN 切换到**东京节点**后，Python 代码即可正常访问 `push2.eastmoney.com`。

当前直连出口 IP：`120.229.21.145`（中国移动，国内 IP）

| 来源 IP | 客户端类型 | 结果 |
|---------|-----------|------|
| 国内 IP (120.229.x.x) | 真实浏览器 (Chrome) | ✅ 通过 |
| 国内 IP (120.229.x.x) | Python requests / httpx / curl | ❌ RST |
| 国内 IP (120.229.x.x) | curl_cffi 模拟 Chrome | ❌ RST |
| 东京 VPN IP | Python / curl / 任何客户端 | ✅ 通过 |

**当时的结论**：东方财富按 IP 地区分级反爬——国内严格 JA4 指纹检测，海外放行。

### 2.8 情况升级：海外 IP 也被封锁

时间推移后，**同一东京 VPN 节点也不再可用**。

当前出口 IP：`43.167.196.125`（海外）

| 端点 | 国内 IP (之前) | 海外 IP (之前) | **海外 IP (现在)** |
|------|:---:|:---:|:---:|
| push2.eastmoney.com | RST | ✅ 200 | **502 Bad Gateway** |
| push2his.eastmoney.com | RST | RST | RST |
| quote.eastmoney.com | ✅ | ✅ | ✅ |
| so.eastmoney.com | ✅ | ✅ | ✅ |

变化要点：
- **push2**：TLS 握手成功（说明指纹检测可能通过或降低），但 HTTP 层返回 `502 Bad Gateway`（nginx/1.26.2）。可能是新部署的 WAF 层面拦截，也可能是后端真实故障。
- **push2his**：仍然在 TLS 层 RST 断连，海外 IP 也不例外。
- **其他域名**（quote / so / datacenter）一切正常。

### 2.9 修正结论：JA4 之外的路径级拦截

回退到**国内直连**后，在浏览器中做了更精细的诊断：

| 端点 | 结果 |
|------|:---:|
| `push2.eastmoney.com` 根路径 | ✅ |
| `/api/qt/stock/get` (实时行情) | ❌ **网络完全断开** |
| `/api/qt/stock/trends2/get` (分时) | ✅ **JSONP 成功** |
| `/api/qt/stock/kline/get` (K线) | ❌ RST |

关键发现：

- `push2` 域名本身可访问（TCP/TLS 握手成功）
- 同一域名下，**路径不同结果完全不同**：`get` 被断连，`trends2` 正常工作
- 这推翻了单纯的「JA4 TLS 指纹反爬」结论——服务器在 **HTTP 路由层**针对特定 API 路径做了区分拦截

### 2.10 最终结论：多层组合反爬

东方财富的反爬是**多层级组合**：

| 层 | 机制 | 影响 |
|----|------|------|
| TLS 指纹 | 非浏览器 TLS 栈 → RST | Python/curl 全挂 |
| 路径过滤 | `/api/qt/stock/get` 被单独拦截 | 浏览器也访问不了 |
| 海外 IP | 之前放行，后升级 | VPN 也失效 |

**但也发现了突破口**：`trends2` 端点（分时数据）不受路径拦截，且确认支持 JSONP 回调。

## 3. 替代方案验证

| 数据源 | 腾讯(港股) | 阿里(港股) | 英伟达(美股) | 白银(期货) |
|--------|-----------|-----------|-------------|-----------|
| Tencent API | ✅ | — | ❌ | — |
| Sina API | ✅ | ✅ | ✅ | ✅ |

**Sina API 对全部 5 只股票均正常工作**，可作为替换方案。

## 4. 处理措施

### 4.1 当前方案：Sina API + 浏览器 Widget（已实施）

- **Python 端**：`config.json` 中 `api` 保持 `"sina"`，稳定可靠。
- **浏览器端**：`stock_widget.html` 使用 `trends2` 端点 + JSONP，**绕过所有反爬层**（浏览器原生 TLS + 非拦截路径）。

### 4.2 浏览器 Widget 原理

```
浏览器打开 stock_widget.html
  → <script> 标签注入 JSONP 请求
  → 浏览器原生 Chrome TLS 栈（JA4 天然通过）
  → /api/qt/stock/trends2/get 端点（不被路径拦截）
  → 分时数据解析 → 实时价格/涨跌幅/最高最低
```

> 其他模拟方案（curl_cffi / CycleTLS / tls_client）均不可靠。

### 4.3 日志基础设施升级

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

### 4.4 日志使用方式

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
