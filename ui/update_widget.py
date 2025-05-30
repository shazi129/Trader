
import config
import trader_utils
from PySide6.QtWidgets import QWidget

from ui.designer.gen.update_widget_generated import Ui_UpdateModule

class UpdateModuleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.updateModule = Ui_UpdateModule()
        self.updateModule.setupUi(self)
        self.updateModule.pushButton.clicked.connect(self.on_update_all_clicked)
        self.updateModule.pushButton_2.clicked.connect(self.on_update_clicked)

        #初始化下拉框
        self.updateSockIndex = 0
        self.stock_keys = [key for key in config.global_stock_list]
        self.updateModule.comboBox.addItems([config.global_stock_list[key].name for key in self.stock_keys])
        self.updateModule.comboBox.currentIndexChanged.connect(self.on_combobox_index_changed)

    def on_combobox_index_changed(self, index):
        print(f"update stock: {self.stock_keys[index]}")
        self.updateSockIndex = index
        

    def on_update_all_clicked(self):
        print("update all clicked")
        trader_utils.update_all_stocks()

    def on_update_clicked(self):
        print("update clicked, {self.stockKeyList[self.updateSockIndex]}")
        trader_utils.update_stocket(self.stock_keys[self.updateSockIndex])
