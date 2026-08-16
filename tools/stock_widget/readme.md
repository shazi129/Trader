# stock_widget — 桌面浮窗实时报价

极简 PySide6 浮窗：无边框、半透明、置顶、可拖动，右键菜单切股票 / 切数据源 /
刷新 / 退出。只显示价格，不显示走势图（这是刻意的：小而不扰）。

## 启动

```cmd
:: 前台（带终端、Ctrl+C 退出）
python tools/stock_widget/stock_widget.py

:: 后台常驻（Windows）
start /b python tools\stock_widget\stock_widget.py
```

从子目录里跑也行（脚本头部做了 `sys.path` 兜底）：

```cmd
cd tools\stock_widget
python stock_widget.py
```

## 配置文件 `config.json`

```json
{
    "stocks": ["Tencent", "Alibaba", "AG"],
    "active": "Alibaba",
    "refresh_interval": 60,
    "opacity": 0.75,
    "font_size": 12,
    "position": "bottom_right"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `api` | string | 可选；省略时使用 `QuoteAPIFactory.current_source()`，有效值由 `available_sources()` 提供 |
| `stocks` | string[] | 候选股票的 `name_key` 列表，对应 `quote_api/stock_meta.py` 中 `STOCK_META` 的键；展示名直接从 `STOCK_META` 读取 |
| `active` | string | 当前显示的 `name_key`，必须出现在 `stocks` 中；右键"切换股票"会写回此字段 |
| `refresh_interval` | int | 刷新秒数 |
| `opacity` | float | 窗口透明度 0.0 – 1.0 |
| `font_size` | int | 字号 |
| `position` | string | `"top_left"` / `"top_right"` / `"bottom_left"` / `"bottom_right"` |

右键菜单里也能临时切"当前显示的股票"和"数据源"，会落盘回 `config.json`。

> 兼容旧格式：旧版 `stocks` 为 `[{"name_key":..., "name":..., "show":...}]` 的写法仍可被读取，
> 启动时会自动归一化为新格式（首个 `show: true` 的项作为 `active`）。

## 数据源支持度

浮窗的数据源菜单直接读取 `QuoteAPIFactory.available_sources()`，默认值读取
`QuoteAPIFactory.current_source()`，不单独维护 provider 名单。只要已注册源实现
`get_daily_quote(name_key)` 即可使用；具体股票映射见对应 provider 的 `config.json`。

## 添加一只要显示的股票

1. 确认 `quote_api/stock_meta.py` 的 `STOCK_META` 里有它；没有就先加（见
   根 [README.md 的"新增一只股票"](../../README.md#新增一只股票)）。
2. 确认选用的 `api` 对应的 `quote_api/<api>/config.json` 里有 `name_key → 代码` 映射。
3. 往本 `config.json` 的 `stocks` 列表里加入该 `name_key`，需要默认显示时同步
   修改 `active`。

## 故障排查

- **浮窗打开后一片空白**：大概率是 `api` 字段配的源不支持你列出的某个
  `name_key`，检查 `quote_api/<api>/config.json` 是否有对应映射。
- **Windows 上字体模糊**：PySide6 对高 DPI 屏的缩放有时偏糊；可以把
  `font_size` 调大一点，或者手动给 `python.exe` 关掉系统 DPI 缩放。
- **右键菜单改了源但没生效**：菜单更新后会立刻写回 `config.json` 并重建
  API；如果某个源本身没装/不可用，看日志有没有报错。
- **想改窗口位置但配置里的四个角不够用**：目前只支持四个角的枚举，要自由
  定位请直接拖动窗口（但不持久化，想持久化请 PR `_save_position`）。
