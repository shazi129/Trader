
from PySide6.QtWidgets import QWidget
from UI.Designer.Ui_UpdateModule import Ui_UpdateModule

class UpdateModuleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.updateModule = Ui_UpdateModule()
        self.updateModule.setupUi(self)
        self.updateModule.pushButton.clicked.connect(self.on_update_all_clicked)
        self.updateModule.pushButton_2.clicked.connect(self.on_update_clicked)

    def on_update_all_clicked(self):
        print("update all clicked")

    def on_update_clicked(self):
        print("update clicked")