"""
Windows 11 浮空股票报价小控件 (PySide6)
- 极简到极致：仅显示价格
- 半透明、无边框、置顶、可拖动
- 右键菜单退出/刷新/打开配置
- 使用东方财富推送接口，国内直连无需翻墙
"""

import sys
import json
import urllib.request
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPoint
from PySide6.QtGui import QFont, QAction, QCursor

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config() -> dict:
    default = {
        "secid": "116.00700",       # 东方财富 secid: 116.港股, 1.沪股, 0.深股, 105.美股
        "refresh_interval": 5,
        "opacity": 0.75,
        "font_size": 12,
        "position": "bottom_right",
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                default.update(json.load(f))
        except Exception:
            pass
    return default

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class StockQuote:
    """东方财富接口返回的行情快照"""
    name: str           # 中文名
    code: str           # 证券代码
    price: float        # 最新价
    prev_close: float   # 昨收
    change: float       # 涨跌额
    change_pct: float   # 涨跌幅 (%)
    high: float         # 最高
    low: float          # 最低
    currency: str       # 币种

# ---------------------------------------------------------------------------
# 数据获取线程（东方财富推送接口）
# ---------------------------------------------------------------------------

_EASTMONEY_URL = "https://push2.eastmoney.com/api/qt/stock/get"
_EASTMONEY_FIELDS = "f57,f58,f59,f43,f44,f45,f46,f60,f169,f170,f172"

class FetchThread(QThread):
    result_ready = Signal(object)  # StockQuote | None

    def __init__(self, secid: str, parent=None):
        super().__init__(parent)
        self.secid = secid

    def run(self):
        """
        东方财富推送接口:
          secid 格式: 116.00700 (港股), 1.600519 (沪股), 0.000001 (深股), 105.AAPL (美股)
          关键字段:
            f57=代码, f58=名称, f59=小数位数(价格scale=10^f59)
            f43=最新价, f44=最高, f45=最低, f46=今开, f60=昨收
            f169=涨跌额, f170=涨跌幅(×100), f172=币种
        """
        quote = None
        try:
            url = (
                f"{_EASTMONEY_URL}?"
                f"ut=6d2ffaa6a585d612eda28417681d58fb"
                f"&fields={_EASTMONEY_FIELDS}"
                f"&secid={self.secid}"
                f"&invt=2"
            )
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com",
            })
            resp = urllib.request.urlopen(req, timeout=8)
            raw = resp.read().decode("utf-8")
            data = json.loads(raw).get("data")
            if not data:
                self.result_ready.emit(None)
                return

            # f59 = 小数位数, scale = 10^f59
            f59 = data.get("f59", 2)
            scale = 10 ** f59 if isinstance(f59, int) else 100

            def _s(key: str) -> float:
                """按 scale 缩放价格字段"""
                v = data.get(key, 0)
                return round(v / scale, f59) if isinstance(v, (int, float)) else 0.0

            quote = StockQuote(
                name=str(data.get("f58", "")),
                code=str(data.get("f57", "")),
                price=_s("f43"),
                prev_close=_s("f60"),
                change=_s("f169"),
                change_pct=round(data.get("f170", 0) / 100, 2) if isinstance(data.get("f170"), (int, float)) else 0.0,
                high=_s("f44"),
                low=_s("f45"),
                currency=str(data.get("f172", "")),
            )
        except Exception as e:
            print(f"[FetchThread] error: {e}")
            quote = None
        self.result_ready.emit(quote)

# ---------------------------------------------------------------------------
# 主控件
# ---------------------------------------------------------------------------

class StockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._drag_pos = QPoint()
        self._fetching = False
        self._thread: FetchThread | None = None

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
        self._fetching = True

        # 清理上一轮残留线程
        self._cleanup_thread()

        self._thread = FetchThread(self.config["secid"], parent=None)
        self._thread.result_ready.connect(self._on_data, Qt.QueuedConnection)
        self._thread.finished.connect(self._on_thread_finished, Qt.QueuedConnection)
        self._thread.start()

    def _on_data(self, quote):
        """收到 StockQuote 或 None"""
        if quote is not None and isinstance(quote, StockQuote):
            self.label.setText(f"{quote.price}")
        else:
            self.label.setText("--")
        # 自适应大小
        self.adjustSize()

    def _on_thread_finished(self):
        """线程执行结束的兜底回调，无论成功失败都恢复 _fetching 标记。"""
        self._fetching = False

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
        """)

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

# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = StockWidget()
    widget.show()
    sys.exit(app.exec())
