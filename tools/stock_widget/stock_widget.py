"""
Windows 11 浮空股票报价小控件 (PySide6)
- 极简到极致：仅显示价格
- 半透明、无边框、置顶、可拖动
- 右键菜单退出/刷新/打开配置/切换股票/切换数据源
- 支持多种行情数据源（腾讯财经 / 东方财富 / AkShare / yfinance / 雪球）
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass
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
SUPPORTED_APIS = ("tencent", "eastmoney", "akshare", "yfinance", "xueqiu", "sina")
DEFAULT_API = "tencent"


@dataclass
class StockConfig:
    """单只股票的配置"""
    stock_code: str          # 腾讯接口代码: hk00700, sh600519, sz000001, usAAPL
    name: str                # 自定义显示名
    show: bool               # 是否在 widget 上显示
    name_key: str = ""       # 对应 config.global_stock_list 的键（供非腾讯源使用）


def load_config() -> dict:
    default = {
        "api": DEFAULT_API,
        "stocks": [
            {"stock_code": "hk00700", "name": "腾讯", "show": True, "name_key": "Tencent"},
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

    # 归一化 api 字段
    api = str(default.get("api", DEFAULT_API)).lower()
    if api not in SUPPORTED_APIS:
        api = DEFAULT_API
    default["api"] = api

    # 将 stocks 字典列表转为 StockConfig 对象列表
    normalized: list[StockConfig] = []
    for s in default["stocks"]:
        if isinstance(s, StockConfig):
            normalized.append(s)
            continue
        normalized.append(StockConfig(
            stock_code=s.get("stock_code", ""),
            name=s.get("name", ""),
            show=bool(s.get("show", False)),
            name_key=s.get("name_key", ""),
        ))
    default["stocks"] = normalized
    return default


def save_config(config: dict) -> None:
    """把当前 config 写回 config.json（仅保留可持久化字段）"""
    try:
        data = {
            "api": config.get("api", DEFAULT_API),
            "stocks": [
                {
                    "stock_code": s.stock_code,
                    "name": s.name,
                    "show": s.show,
                    "name_key": s.name_key,
                }
                for s in config["stocks"]
            ],
            "refresh_interval": config.get("refresh_interval", 5),
            "opacity": config.get("opacity", 0.75),
            "font_size": config.get("font_size", 12),
            "position": config.get("position", "bottom_right"),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[save_config] error: {e}")


def get_active_stock(config: dict) -> Optional[StockConfig]:
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
    """统一行情快照"""
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
# 数据获取线程
# ---------------------------------------------------------------------------


class FetchThread(QThread):
    """
    完全通过 quote_api.QuoteAPIFactory 统一取数，不对任何数据源做特殊分支。
    - 优先调 get_daily_quote(name_key, date=None)，各源可走各自最实时的通道
      （如 tencent 会走 qt.gtimg.cn 实时接口；其它源取最近一根日K）。
    - 若拿不到 pre_close，则再取最近两根日K，用上一根 close 作为昨收计算涨跌。
    """
    result_ready = Signal(object)  # StockQuote | None

    def __init__(self, api: str, stock: StockConfig, parent=None):
        super().__init__(parent)
        self.api = api
        self.stock = stock

    # ------------------------------------------------------------------
    def run(self):
        quote: Optional[StockQuote] = None
        try:
            quote = self._fetch_via_quote_api(self.api, self.stock)
        except Exception as e:
            print(f"[FetchThread] error ({self.api}): {e}")
            quote = None
        self.result_ready.emit(quote)

    # ------------------------------------------------------------------
    def _fetch_via_quote_api(self, api: str, stock: StockConfig) -> Optional[StockQuote]:
        if not stock.name_key:
            print(f"[FetchThread] stock '{stock.name}' missing 'name_key', cannot query api={api}")
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

        # 1) 取当前最新一条
        try:
            last = impl.get_daily_quote(stock.name_key, date=None)
        except Exception as e:
            print(f"[FetchThread] get_daily_quote error ({api}): {e}")
            return None
        if last is None:
            return None

        # 2) 如果没有昨收，再拉最近两根日K补齐
        prev_close = last.pre_close if last.pre_close > 0 else 0.0
        if prev_close <= 0:
            try:
                klines = impl.get_klines(stock.name_key, limit=2)
            except Exception as e:
                print(f"[FetchThread] get_klines fallback error ({api}): {e}")
                klines = []
            if len(klines) >= 2:
                prev_close = klines[-2].close
            elif klines:
                prev_close = klines[-1].close
        if prev_close <= 0:
            prev_close = last.close  # 彻底无法确定时退化为 0 涨跌

        change = last.close - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0

        # 币种按市场前缀推测（stock_code 保留前缀用于展示/币种推断）
        market_prefix = stock.stock_code[:2].lower()
        currency_map = {"hk": "HKD", "us": "USD"}
        currency = currency_map.get(market_prefix, "CNY")

        return StockQuote(
            name=stock.name,
            code=last.code or stock.stock_code,
            price=last.close,
            prev_close=prev_close,
            change=round(change, 4),
            change_pct=round(change_pct, 2),
            high=last.high,
            low=last.low,
            currency=currency,
        )

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

        active = get_active_stock(self.config)
        if active is None:
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
        """收到 StockQuote 或 None，展示格式: 507.00|+3.50 或 507.00|-2.00"""
        if quote is not None and isinstance(quote, StockQuote):
            price_str = f"{quote.price:.2f}"
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
        for stock in self.config["stocks"]:
            action = QAction(
                f"{'✔ ' if stock.show else '   '}{stock.name} ({stock.stock_code})",
                self,
            )
            action.triggered.connect(lambda checked=False, s=stock: self._switch_stock(s))
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

    def _switch_stock(self, target: StockConfig):
        """切换显示的股票：将目标设为 show=True，其余设为 False，并立即刷新"""
        for s in self.config["stocks"]:
            s.show = (s is target)
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
