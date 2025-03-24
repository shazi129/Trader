# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UpdateModule.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_UpdateModule(object):
    def setupUi(self, UpdateModule):
        if not UpdateModule.objectName():
            UpdateModule.setObjectName(u"UpdateModule")
        UpdateModule.resize(400, 300)
        self.comboBox = QComboBox(UpdateModule)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(50, 30, 131, 22))
        self.pushButton = QPushButton(UpdateModule)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(70, 100, 75, 24))
        self.label = QLabel(UpdateModule)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 30, 54, 16))
        self.pushButton_2 = QPushButton(UpdateModule)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(200, 30, 75, 24))

        self.retranslateUi(UpdateModule)

        QMetaObject.connectSlotsByName(UpdateModule)
    # setupUi

    def retranslateUi(self, UpdateModule):
        UpdateModule.setWindowTitle(QCoreApplication.translate("UpdateModule", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("UpdateModule", u"\u5168\u90e8\u66f4\u65b0", None))
        self.label.setText(QCoreApplication.translate("UpdateModule", u"\u540d\u79f0\uff1a", None))
        self.pushButton_2.setText(QCoreApplication.translate("UpdateModule", u"\u66f4\u65b0", None))
    # retranslateUi

