"""
Windows 11 浮空股票报价小控件 (PySide6)
- 极简到极致：仅显示价格
- 半透明、无边框、置顶、可拖动
- 右键菜单退出/刷新/打开配置/切换股票/切换数据源
- 支持多种行情数据源（腾讯财经 / 东方财富 / 新浪财经）
"""

import sys
import json
from pathlib import Path
from typing import Optional

# 让 `tools/stock_widget/` 子目录直接运行时也能 import 项目根包
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPoint
from PySide6.QtGui import QFont, QAction, QCursor

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.json"

# 支持的数据源。顺序决定菜单中的排列顺序。
# 注意：sina 仅稳定支持 A 股（实时+K 线）；港股只有实时快照、没有历史 K 线。
SUPPORTED_APIS = ("tencent", "eastmoney", "sina")
DEFAULT_API = "tencent"


def _resolve_display_name(name_key: str) -> str:
    """从 stock_meta 获取展示名；查不到则回退到 name_key 本身。"""
    try:
        from quote_api.stock_meta import get_meta
        info = get_meta(name_key)
        if info is not None:
            return info.name
    except Exception:
        pass
    return name_key


def load_config() -> dict:
    default = {
        "api": DEFAULT_API,
        "stocks": ["Tencent"],
        "active": "Tencent",
        "refresh_interval": 5,
        "opacity": 0.75,
        "font_size": 12,
        "position": "bottom_right",
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default.update(cfg)
        except Exception:
            pass

    # 归一化 api 字段
    api = str(default.get("api", DEFAULT_API)).lower()
    if api not in SUPPORTED_APIS:
        api = DEFAULT_API
    default["api"] = api

    # 归一化 stocks：兼容旧的 [{"name_key":..., "show":...}] 格式
    raw_stocks = default.get("stocks") or []
    stocks: list[str] = []
    legacy_active: Optional[str] = None
    for s in raw_stocks:
        if isinstance(s, str):
            if s:
                stocks.append(s)
        elif isinstance(s, dict):
            key = s.get("name_key", "")
            if not key:
                continue
            stocks.append(key)
            if s.get("show"):
                legacy_active = key
    if not stocks:
        stocks = ["Tencent"]
    default["stocks"] = stocks

    # 归一化 active：必须是 stocks 中的一个
    active = default.get("active") or legacy_active or stocks[0]
    if active not in stocks:
        active = stocks[0]
    default["active"] = active

    return default


def save_config(config: dict) -> None:
    """把当前 config 写回 config.json（仅保留可持久化字段）"""
    try:
        data = {
            "api": config.get("api", DEFAULT_API),
            "stocks": list(config.get("stocks", [])),
            "active": config.get("active", ""),
            "refresh_interval": config.get("refresh_interval", 5),
            "opacity": config.get("opacity", 0.75),
            "font_size": config.get("font_size", 12),
            "position": config.get("position", "bottom_right"),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[save_config] error: {e}")

# ---------------------------------------------------------------------------
# 数据获取线程
# ---------------------------------------------------------------------------


class FetchThread(QThread):
    """
    完全通过 quote_api.QuoteAPIFactory 统一取数，不对任何数据源做特殊分支。
    - 优先调 get_daily_quote(name_key, date=None)，各源可走各自最实时的通道
      （如 tencent 会走 qt.gtimg.cn 实时接口；其它源取最近一根日K）。
    - 若拿不到 pre_close，则再取最近两根日K，用上一根 close 作为昨收计算涨跌。
    """
    result_ready = Signal(object)  # DailyQuote | str("UNSUPPORTED") | None

    def __init__(self, api: str, name_key: str, parent=None):
        super().__init__(parent)
        self.api = api
        self.name_key = name_key

    # ------------------------------------------------------------------
    def run(self):
        quote = None
        try:
            quote = self._fetch_via_quote_api(self.api, self.name_key)
        except Exception as e:
            print(f"[FetchThread] error ({self.api}): {e}")
            quote = None
        self.result_ready.emit(quote)

    # ------------------------------------------------------------------
    def _fetch_via_quote_api(self, api: str, name_key: str):
        if not name_key:
            print(f"[FetchThread] missing name_key, cannot query api={api}")
            return None

        try:
            from quote_api import QuoteAPIFactory
        except Exception as e:
            print(f"[FetchThread] import quote_api failed: {e}")
            return None

        try:
            impl = QuoteAPIFactory.create(api)
        except Exception as e:
            print(f"[FetchThread] create api '{api}' failed: {e}")
            return None

        # 检查当前 API 是否支持该 name_key
        if not impl.is_supported(name_key):
            print(f"[FetchThread] api '{api}' does not support '{name_key}'")
            return "UNSUPPORTED"

        # 1) 取当前最新一条
        try:
            last = impl.get_daily_quote(name_key, date=None)
        except Exception as e:
            print(f"[FetchThread] get_daily_quote error ({api}): {e}")
            return None
        if last is None:
            return None

        # 2) 如果没有昨收，再拉最近两根日K补齐
        prev_close = last.pre_close if last.pre_close > 0 else 0.0
        if prev_close <= 0:
            try:
                klines = impl.get_klines(name_key, limit=2)
            except Exception as e:
                print(f"[FetchThread] get_klines fallback error ({api}): {e}")
                klines = []
            if len(klines) >= 2:
                prev_close = klines[-2].close
            elif klines:
                prev_close = klines[-1].close
        if prev_close <= 0:
            prev_close = last.close  # 彻底无法确定时退化为 0 涨跌

        # 3) 填充派生字段
        last.pre_close = prev_close
        last.change = round(last.close - prev_close, 4)
        last.change_pct = round((last.change / prev_close * 100) if prev_close > 0 else 0.0, 2)
        last.name = _resolve_display_name(name_key)

        # 币种按 stock_meta 中的 market 推断
        try:
            from quote_api.stock_meta import get_meta
            from quote_api import StockMarket
            info = get_meta(name_key)
            if info is not None:
                _market_currency = {
                    StockMarket.HK: "HKD",
                    StockMarket.COMEX: "USD",
                }
                last.currency = _market_currency.get(info.market, "CNY")
        except Exception:
            pass

        return last

# ---------------------------------------------------------------------------
# 主控件
# ---------------------------------------------------------------------------

class StockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._drag_pos = QPoint()
        self._fetching = False
        self._thread: Optional[FetchThread] = None

        # ---- 窗口属性 ----
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # 不在任务栏显示
        )
        self.setWindowOpacity(self.config["opacity"])

        # ---- 布局 ----
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 主行：仅显示价格
        self.label = QLabel("--")
        self.label.setFont(QFont("Segoe UI", self.config["font_size"]))
        self.label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.label)

        self._apply_style()
        self.adjustSize()

        # ---- 定位 ----
        self._position_window()

        # ---- 定时刷新 ----
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fetch)
        self.timer.start(self.config["refresh_interval"] * 1000)
        self._fetch()  # 立即拉一次

    def _apply_style(self, color: str = "#cccccc"):
        """设置控件样式，颜色随涨跌变化"""
        self.setStyleSheet("background: transparent;")
        self.label.setStyleSheet(
            f"QLabel {{ color: {color}; background: #1e1e1e; "
            f"padding: 4px 10px; border-radius: 6px; }}"
        )

    # ---- 窗口初始定位 ----
    def _position_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 20
        w, h = self.width(), self.height()
        pos_map = {
            "bottom_right": (screen.right() - w - margin, screen.bottom() - h - margin),
            "bottom_left":  (screen.left() + margin, screen.bottom() - h - margin),
            "top_right":    (screen.right() - w - margin, screen.top() + margin),
            "top_left":     (screen.left() + margin, screen.top() + margin),
        }
        x, y = pos_map.get(self.config.get("position"), pos_map["bottom_right"])
        # 确保不超出屏幕
        x = max(screen.left(), min(x, screen.right() - w))
        y = max(screen.top(), min(y, screen.bottom() - h))
        self.move(x, y)

    # ---- 清理旧线程 ----
    def _cleanup_thread(self):
        if self._thread is not None:
            try:
                self._thread.result_ready.disconnect(self._on_data)
            except (RuntimeError, TypeError):
                pass
            try:
                self._thread.finished.disconnect(self._on_thread_finished)
            except (RuntimeError, TypeError):
                pass
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(2000)
            self._thread.deleteLater()
            self._thread = None

    # ---- 数据获取 ----
    def _fetch(self):
        if self._fetching:
            return

        active = self.config.get("active") or ""
        if not active:
            self.label.setText("--")
            return

        self._fetching = True

        # 清理上一轮残留线程
        self._cleanup_thread()

        self._thread = FetchThread(self.config["api"], active, parent=None)
        self._thread.result_ready.connect(self._on_data, Qt.QueuedConnection)
        self._thread.finished.connect(self._on_thread_finished, Qt.QueuedConnection)
        self._thread.start()

    def _on_data(self, quote):
        """收到 DailyQuote / "UNSUPPORTED" / None，展示对应内容"""
        from quote_api.quote_base import DailyQuote
        if quote == "UNSUPPORTED":
            self.label.setText("不支持")
            self._apply_style("#888888")
        elif quote is not None and isinstance(quote, DailyQuote):
            price_str = f"{quote.close:.2f}"
            if quote.change > 0:
                change_str = f"+{quote.change:.2f}"
            elif quote.change < 0:
                change_str = f"{quote.change:.2f}"
            else:
                change_str = "0.00"
            self.label.setText(f"{price_str}|{change_str}")
        else:
            self.label.setText("--")
        # 自适应大小
        self.adjustSize()

    def _on_thread_finished(self):
        """线程执行结束的兜底回调，无论成功失败都恢复 _fetching 标记。"""
        self._fetching = False

    # ---- 关闭事件：正确回收线程，避免 QThread 警告 ----
    def closeEvent(self, event):
        try:
            self.timer.stop()
        except Exception:
            pass
        self._cleanup_thread()
        super().closeEvent(event)

    # ---- 拖动 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    # ---- 右键菜单 ----
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #2a2a2a; color: #ccc; border: 1px solid #444; }
            QMenu::item:selected { background: #3a3a3a; }
            QMenu::item:checked { color: #4fc3f7; }
        """)

        # 股票切换子菜单
        stock_menu = menu.addMenu("切换股票")
        active_key = self.config.get("active", "")
        for name_key in self.config["stocks"]:
            mark = "✔ " if name_key == active_key else "   "
            action = QAction(
                f"{mark}{_resolve_display_name(name_key)} ({name_key})",
                self,
            )
            action.triggered.connect(lambda checked=False, k=name_key: self._switch_stock(k))
            stock_menu.addAction(action)

        # 数据源切换子菜单
        api_menu = menu.addMenu("数据源")
        current_api = self.config.get("api", DEFAULT_API)
        for api_name in SUPPORTED_APIS:
            mark = "✔ " if api_name == current_api else "   "
            action = QAction(f"{mark}{api_name}", self)
            action.triggered.connect(lambda checked=False, a=api_name: self._switch_api(a))
            api_menu.addAction(action)

        menu.addSeparator()

        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self._fetch)
        menu.addAction(refresh_action)

        config_action = QAction("打开配置", self)
        config_action.triggered.connect(lambda: __import__("os").startfile(str(CONFIG_PATH)))
        menu.addAction(config_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        menu.exec(QCursor.pos())

    def _switch_stock(self, name_key: str):
        """切换显示的股票：将 active 设为目标 name_key，并立即刷新"""
        if name_key not in self.config["stocks"]:
            return
        if name_key == self.config.get("active"):
            return
        self.config["active"] = name_key
        save_config(self.config)
        self.label.setText("--")
        self._fetch()

    def _switch_api(self, api: str):
        """切换数据源：更新 config，写回磁盘，立即刷新"""
        if api not in SUPPORTED_APIS or api == self.config.get("api"):
            return
        self.config["api"] = api
        save_config(self.config)
        self.label.setText("--")
        self._fetch()

# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = StockWidget()
    widget.show()
    sys.exit(app.exec())
