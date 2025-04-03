from __future__ import annotations

import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class MatplotlibWidget(QWidget):
    def __init__(self):
        super().__init__()
        plt.rcParams['font.size'] = 8  # 字体大小
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题

        # 创建 Matplotlib 图形
        self.figure, self.ax = plt.subplots()
        # FigureCanvas 是 Matplotlib 的一个类
        # 专门用于将 Matplotlib 图形嵌入到 Qt 应用程序中
        # 具体来说，FigureCanvasQTAgg 是一个后端类
        # 它实现了 FigureCanvas，并提供了与 Qt 的集成
        self.canvas = FigureCanvas(self.figure)

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def show(self, name: str, points: List[Tuple[float, float]]):
        # 清空之前的图形
        self.ax.clear()

        # 生成 X 值
        x = [i[0] for i in points]
        # 计算 Y 值
        y = [i[1] for i in points]

        # 绘制曲线
        self.ax.plot(x, y, label = name, color = 'red', linewidth = 3)
        self.ax.set_title(name)
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.grid()
        self.ax.legend()

        # 刷新画布
        self.canvas.draw()