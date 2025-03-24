from PySide6.QtWidgets import QMainWindow
from UI.Designer.Ui_MainWindow import Ui_MainWindow
from UI.RatioDisplayWidget import RatioDisplayWidget
from UI.UpdateModuleWidget import UpdateModuleWidget

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
        self.mainWindow.moduleArea.addChildWidget(self.update_wiget)
        self.update_wiget.setVisible(True)

        self.mainWindow.moduleList.addItem("比值展示")
        self.ratio_display_widget = RatioDisplayWidget()
        self.module_widgets.append(self.ratio_display_widget)
        self.mainWindow.moduleArea.addChildWidget(self.ratio_display_widget)
        self.ratio_display_widget.setVisible(False)

    def on_list_item_clicked(self, item):
        index = self.mainWindow.moduleList.row(item)
        print(f"index: {index}, {item}")
        for i, widget in enumerate(self.module_widgets):
            if i == index:
                widget.setVisible(True)
            else:
                widget.setVisible(False)