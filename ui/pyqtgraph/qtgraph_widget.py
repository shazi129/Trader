import time
import numpy as np
import pyqtgraph as pg
import trader_utils

class QTGraphWidget(pg.PlotWidget):
    # 定义尽量包含parent， 这样可以方便父子关系的联通
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test1()

    def test2(self):
        # 界面的背景设置
        self.setBackground('w')
        self.axisItems['left'].setPen('b')

        # 将绘图项与PlotWidget的主要坐标结合， 并设置坐标轴标签
        self.plotItem.getAxis('left').setLabel("日期", color='blue')
        self.plotItem.getAxis('bottom').setLabel("数值", color='blue')

        datas = trader_utils.get_ratio_data("Tencent", "Tencent_27124")
        x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        values = [item * item for item in x]
        self.cuv = pg.PlotCurveItem(pen=pg.mkPen(color='blue', width=4))
        self.cuv.setData(x, values)

        # 将曲线添加到上面定义的绘图项self.p
        self.plotItem.addItem(self.cuv)


    def test1(self):
        self.axisItems = {'bottom': pg.DateAxisItem()}
        self.showGrid(x=True, y=True)

        # Plot sin(1/x^2) with timestamps in the last 100 years
        now = time.time()
        x = np.linspace(2*np.pi, 1000*2*np.pi, 8301)
        self.plot(now-(2*np.pi/x)**2*100*np.pi*1e7, np.sin(x), symbol='o')