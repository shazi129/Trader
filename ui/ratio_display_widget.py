
import config
import trader_utils
from PySide6.QtWidgets import QWidget

from ui.designer.gen.ratio_display_wdiget_generated import Ui_ratioDisplayWidget
from utils.event_system import EventSystem

class RatioDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ui_widget = Ui_ratioDisplayWidget()
        self.ui_widget.setupUi(self)
        self.ui_widget.showRatioButton.clicked.connect(self.on_show_ratio_button_clicked)

        #初始化下拉框
        self.numerator_index = 0
        self.denominator_index = 0
        self.stock_keys = [key for key in config.global_stock_list]

        #分子下拉框
        self.ui_widget.denominatorComboBox.addItems([config.global_stock_list[key].name for key in self.stock_keys])
        self.ui_widget.denominatorComboBox.currentIndexChanged.connect(self.on_denominator_index_changed)

        #分母下拉框
        self.ui_widget.numeratorComboBox.addItems([config.global_stock_list[key].name for key in self.stock_keys])
        self.ui_widget.numeratorComboBox.currentIndexChanged.connect(self.on_numerator_index_changed)

    def on_denominator_index_changed(self, index):
        print(f"denominator change: {self.stock_keys[index]}")
        self.denominator_index = index
        
    def on_numerator_index_changed(self, index):
        print(f"numerator change: {self.stock_keys[index]}")
        self.numerator_index = index

    def on_show_ratio_button_clicked(self):
        if (self.denominator_index == self.numerator_index):
            print("分子分母不能相同")
            return
        print(f"show ratio clicked, {self.stock_keys[self.numerator_index]}, {self.stock_keys[self.denominator_index]}")
        ratio_data = trader_utils.get_ratio_data(self.stock_keys[self.numerator_index], self.stock_keys[self.denominator_index])

        show_data = config.create_show_data()
        show_data["values"]["ratio"] = []
        for ratio in ratio_data:
            show_data["date"].append(ratio.date)
            show_data["values"]["ratio"].append(ratio.value)

        EventSystem.get_instance().notify_listeners(config.EventID.SHOW_DATA, show_data)
