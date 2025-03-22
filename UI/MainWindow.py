from PySide6.QtWidgets import QMainWindow
from UI.UpdateModuleWidget import UpdateModuleWidget
from UI.Designer.Ui_MainWindow import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mainWindow = Ui_MainWindow()
        self.mainWindow.setupUi(self)

        self.mainWindow.moduleList.addItem("常规")
        self.mainWindow.moduleList.addItem("高级")
        self.mainWindow.moduleList.addItem("关于")
        self.mainWindow.moduleList.itemClicked.connect(self.on_list_item_clicked)

        self.updateModuleWidget = UpdateModuleWidget()
        self.mainWindow.moduleArea.addChildWidget(self.updateModuleWidget)


    def on_list_item_clicked(self, item):
        index = self.mainWindow.moduleList.row(item)
        print(f"index: {index}")