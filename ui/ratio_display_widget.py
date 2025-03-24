
import Config
import TraderUtils
from PySide6.QtWidgets import QWidget
from UI.Designer.Ui_RatioDisplayWidget import Ui_ratioDisplayWidget

class RatioDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ui_widget = Ui_ratioDisplayWidget()
        self.ui_widget.setupUi(self)
        self.ui_widget.showRatioButton.clicked.connect(self.on_show_ratio_button_clicked)

        #初始化下拉框
        self.numerator_index = 0
        self.denominator_index = 0
        self.stock_keys = [key for key in Config.global_stock_list]

        #分子下拉框
        self.ui_widget.denominatorComboBox.addItems([Config.global_stock_list[key].name for key in self.stock_keys])
        self.ui_widget.denominatorComboBox.currentIndexChanged.connect(self.on_denominator_index_changed)

        #分母下拉框
        self.ui_widget.numeratorComboBox.addItems([Config.global_stock_list[key].name for key in self.stock_keys])
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

        TraderUtils.get_ratio_data(self.stock_keys[self.numerator_index], self.stock_keys[self.denominator_index])
