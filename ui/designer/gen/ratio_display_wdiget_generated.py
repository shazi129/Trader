# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ratio_display_wdiget.ui'
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

class Ui_ratioDisplayWidget(object):
    def setupUi(self, ratioDisplayWidget):
        if not ratioDisplayWidget.objectName():
            ratioDisplayWidget.setObjectName(u"ratioDisplayWidget")
        ratioDisplayWidget.resize(665, 71)
        self.label = QLabel(ratioDisplayWidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(160, 20, 16, 21))
        self.numeratorComboBox = QComboBox(ratioDisplayWidget)
        self.numeratorComboBox.setObjectName(u"numeratorComboBox")
        self.numeratorComboBox.setGeometry(QRect(40, 20, 111, 22))
        self.denominatorComboBox = QComboBox(ratioDisplayWidget)
        self.denominatorComboBox.setObjectName(u"denominatorComboBox")
        self.denominatorComboBox.setGeometry(QRect(170, 20, 111, 22))
        self.showRatioButton = QPushButton(ratioDisplayWidget)
        self.showRatioButton.setObjectName(u"showRatioButton")
        self.showRatioButton.setGeometry(QRect(320, 20, 75, 24))

        self.retranslateUi(ratioDisplayWidget)

        QMetaObject.connectSlotsByName(ratioDisplayWidget)
    # setupUi

    def retranslateUi(self, ratioDisplayWidget):
        ratioDisplayWidget.setWindowTitle(QCoreApplication.translate("ratioDisplayWidget", u"Form", None))
        self.label.setText(QCoreApplication.translate("ratioDisplayWidget", u"/", None))
        self.showRatioButton.setText(QCoreApplication.translate("ratioDisplayWidget", u"\u751f\u6210", None))
    # retranslateUi

