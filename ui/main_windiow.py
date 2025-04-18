from PySide6.QtWidgets import QMainWindow, QVBoxLayout
import numpy as np
import config
from ui.designer.gen.main_window_generated import Ui_MainWindow
from ui.matplot.matplot_widget import MatplotlibWidget
from ui.pyqtgraph.qtgraph_widget import QTGraphWidget
from ui.ratio_display_widget import RatioDisplayWidget
from ui.update_widget import UpdateModuleWidget
from ui.pyqtgraph.qtgraph_widget import QTGraphWidget
from utils.event_system import EventSystem;

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mainWindow = Ui_MainWindow()
        self.mainWindow.setupUi(self)

        self.cur_module_index = 0
        self.mainWindow.moduleList.itemClicked.connect(self.on_list_item_clicked)

        self.module_widgets = []

        self.mainWindow.moduleList.addItem("更新")
        self.update_wiget = UpdateModuleWidget()
        self.module_widgets.append(self.update_wiget)
        self.mainWindow.ModuleArea.addChildWidget(self.update_wiget)
        self.update_wiget.setVisible(True)

        self.mainWindow.moduleList.addItem("比值展示")
        self.ratio_display_widget = RatioDisplayWidget()
        self.module_widgets.append(self.ratio_display_widget)
        self.mainWindow.ModuleArea.addChildWidget(self.ratio_display_widget)
        self.ratio_display_widget.setVisible(False)

        self.plot_widget = QTGraphWidget()
        self.plot_widget.setObjectName(u"QTGraphWidget")
        self.plot_widget.setContentsMargins(0, 0, 0, 0)
        self.mainWindow.GraphArea.addWidget(self.plot_widget)

        EventSystem.get_instance().register_listner(config.EventID.SHOW_DATA, self.on_show_data)

    def on_list_item_clicked(self, item):
        index = self.mainWindow.moduleList.row(item)
        print(f"index: {index}, {item}")
        for i, widget in enumerate(self.module_widgets):
            if i == index:
                widget.setVisible(True)
            else:
                widget.setVisible(False)

    def on_show_data(self, data):
        if (data is None):
            return
        
        print(f"show data: {data}")
        self.plot_widget.clear()
        #elf.plot_widget.plot(data)