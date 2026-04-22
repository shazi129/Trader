"""
Windows 11 浮空股票报价小控件 (PySide6)
- 极简到极致：仅显示价格
- 半透明、无边框、置顶、可拖动
- 右键菜单退出/刷新/打开配置
- 使用腾讯财经接口，国内直连无需翻墙
"""

import sys
import json
import re
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

@dataclass
class StockConfig:
    """单只股票的配置"""
    stock_code: str     # 腾讯接口代码: hk00700, sh600519, sz000001, usAAPL
    name: str           # 自定义显示名
    show: bool          # 是否在 widget 上显示

def load_config() -> dict:
    default = {
        "stocks": [
            {"stock_code": "hk00700", "name": "腾讯", "show": True},
        ],
        "refresh_interval": 5,
        "opacity": 0.75,
        "font_size": 12,
        "position": "bottom_right",
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                # 兼容旧配置：单个 stock_code 转为 stocks 数组
                if "stock_code" in cfg and "stocks" not in cfg:
                    code = cfg.pop("stock_code")
                    cfg["stocks"] = [{"stock_code": code, "name": code, "show": True}]
                default.update(cfg)
        except Exception:
            pass
    # 将 stocks 字典列表转为 StockConfig 对象列表
    default["stocks"] = [
        StockConfig(**s) if not isinstance(s, StockConfig) else s
        for s in default["stocks"]
    ]
    return default

def get_active_stock(config: dict) -> StockConfig | None:
    """获取当前 show=True 的股票配置，返回第一个匹配的"""
    for s in config["stocks"]:
        if s.show:
            return s
    return None

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class StockQuote:
    """腾讯财经接口返回的行情快照"""
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
# 数据获取线程（腾讯财经接口）
# ---------------------------------------------------------------------------

_TENCENT_URL = "https://qt.gtimg.cn/q="

class FetchThread(QThread):
    result_ready = Signal(object)  # StockQuote | None

    def __init__(self, stock_code: str, parent=None):
        super().__init__(parent)
        self.stock_code = stock_code

    def run(self):
        """
        腾讯财经行情接口:
          URL: https://qt.gtimg.cn/q=<stock_code>
          stock_code 格式: hk00700(港股), sh600519(沪股), sz000001(深股), usAAPL(美股)

          返回格式为 v_<code>="字段1~字段2~...~字段N";
          实际字段顺序(~分隔, 从0开始):
            0=未知, 1=名称, 2=代码, 3=最新价, 4=涨跌额, 5=涨跌幅(%),
            6=最高, 7=最低, ...
          所有市场使用相同的字段顺序，需要根据最新价和涨跌额计算昨收价
        """
        quote = None
        try:
            url = f"{_TENCENT_URL}{self.stock_code}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com",
            })
            resp = urllib.request.urlopen(req, timeout=8)
            raw = resp.read().decode("gbk")

            # 解析响应: v_hk00700="xxx~xxx~...";
            match = re.search(r'"([^"]+)"', raw)
            if not match:
                self.result_ready.emit(None)
                return

            fields = match.group(1).split("~")
            if len(fields) < 10:
                self.result_ready.emit(None)
                return

            market = self.stock_code[:2].lower()
            quote = self._parse_by_market(market, fields)

        except Exception as e:
            print(f"[FetchThread] error: {e}")
            quote = None
        self.result_ready.emit(quote)

    def _parse_by_market(self, market: str, fields: list) -> StockQuote | None:
        """
        根据市场类型解析字段。腾讯接口所有市场的字段布局实际一致:
          3=最新价, 4=昨收, 5=今开, 6=成交量, ...
          31=涨跌额, 32=涨跌幅(%), 33=最高, 34=最低
        """
        try:
            currency_map = {"hk": "HKD", "us": "USD"}
            currency = currency_map.get(market, "CNY")

            price = float(fields[3]) if len(fields) > 3 else 0.0
            prev_close = float(fields[4]) if len(fields) > 4 else 0.0

            return StockQuote(
                name=fields[1] if len(fields) > 1 else "",
                code=fields[2] if len(fields) > 2 else "",
                price=price,
                prev_close=prev_close,
                change=float(fields[31]) if len(fields) > 31 else 0.0,
                change_pct=float(fields[32]) if len(fields) > 32 else 0.0,
                high=float(fields[33]) if len(fields) > 33 else 0.0,
                low=float(fields[34]) if len(fields) > 34 else 0.0,
                currency=currency,
            )
        except (ValueError, IndexError) as e:
            print(f"[FetchThread] parse error ({market}): {e}")
            return None

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

        active = get_active_stock(self.config)
        if active is None:
            self.label.setText("--")
            return

        self._fetching = True

        # 清理上一轮残留线程
        self._cleanup_thread()

        self._thread = FetchThread(active.stock_code, parent=None)
        self._thread.result_ready.connect(self._on_data, Qt.QueuedConnection)
        self._thread.finished.connect(self._on_thread_finished, Qt.QueuedConnection)
        self._thread.start()

    def _on_data(self, quote):
        """收到 StockQuote 或 None，展示格式: 507.0|+3.5 或 507.0|-2.0"""
        if quote is not None and isinstance(quote, StockQuote):
            if quote.change > 0:
                change_str = f"+{quote.change}"
            elif quote.change < 0:
                change_str = f"{quote.change}"
            else:
                change_str = "0"
            self.label.setText(f"{quote.price}|{change_str}")
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
            QMenu::item:checked { color: #4fc3f7; }
        """)

        # 股票切换子菜单
        stock_menu = menu.addMenu("切换股票")
        for stock in self.config["stocks"]:
            action = QAction(f"{'✔ ' if stock.show else '   '}{stock.name} ({stock.stock_code})", self)
            action.triggered.connect(lambda checked, s=stock: self._switch_stock(s))
            stock_menu.addAction(action)

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

    def _switch_stock(self, target: StockConfig):
        """切换显示的股票：将目标设为 show=True，其余设为 False，并立即刷新"""
        for s in self.config["stocks"]:
            s.show = (s is target)
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
