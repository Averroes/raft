# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SimpleDialog.ui'
#
# Created: Fri Feb 11 21:37:53 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_simpleDialog(object):
    def setupUi(self, simpleDialog):
        simpleDialog.setObjectName(_fromUtf8("simpleDialog"))
        simpleDialog.resize(285, 188)
        self.layoutWidget = QtGui.QWidget(simpleDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(150, 150, 126, 32))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.closeButton = QtGui.QPushButton(self.layoutWidget)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.horizontalLayout.addWidget(self.closeButton)
        self.messageLabel = QtGui.QLabel(simpleDialog)
        self.messageLabel.setGeometry(QtCore.QRect(10, 10, 261, 121))
        self.messageLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setObjectName(_fromUtf8("messageLabel"))

        self.retranslateUi(simpleDialog)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), simpleDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(simpleDialog)

    def retranslateUi(self, simpleDialog):
        simpleDialog.setWindowTitle(QtGui.QApplication.translate("simpleDialog", "Message", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("simpleDialog", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.messageLabel.setText(QtGui.QApplication.translate("simpleDialog", "text", None, QtGui.QApplication.UnicodeUTF8))

