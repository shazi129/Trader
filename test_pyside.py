import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtWidgets import QGridLayout, QMainWindow, QApplication, QListWidget


class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Username:")
        self.lineEdit = QLineEdit()
        self.button = QPushButton("Login")
        layout.addWidget(self.label)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.button)
        self.setLayout(layout)


class CalculatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.label = QLabel("Calculator")
        layout.addWidget(self.label, 0, 0, 1, 2)
        self.button = QPushButton("Calculate")
        layout.addWidget(self.button, 1, 0, 1, 2)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Application")
        self.setGeometry(100, 100, 400, 500)

        self.listView = QListWidget()
        self.listView.addItem("Login")
        self.listView.addItem("Calculator")
        self.listView.currentRowChanged.connect(self.on_list_item_selected)

        self.loginWidget = LoginWidget()
        self.calculatorWidget = CalculatorWidget()

        self.centralWidget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.listView)
        self.layout.addWidget(self.loginWidget)
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    def on_list_item_selected(self, index):
        if index == 0:
            self.loginWidget.show()
            self.calculatorWidget.hide()
        elif index == 1:
            self.loginWidget.hide()
            self.calculatorWidget.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())