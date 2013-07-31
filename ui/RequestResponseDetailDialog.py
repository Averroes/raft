# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RequestResponseDetailDialog.ui'
#
# Created: Tue Jun 21 19:53:27 2011
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_RequestResponseDetailDialog(object):
    def setupUi(self, RequestResponseDetailDialog):
        RequestResponseDetailDialog.setObjectName(_fromUtf8("RequestResponseDetailDialog"))
        RequestResponseDetailDialog.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(RequestResponseDetailDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitter = QtGui.QSplitter(RequestResponseDetailDialog)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.detailWidget = QtGui.QFrame(self.splitter)
        self.detailWidget.setFrameShape(QtGui.QFrame.StyledPanel)
        self.detailWidget.setFrameShadow(QtGui.QFrame.Raised)
        self.detailWidget.setObjectName(_fromUtf8("detailWidget"))
        self.tabWidget = QtGui.QTabWidget(self.splitter)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(RequestResponseDetailDialog)
        QtCore.QMetaObject.connectSlotsByName(RequestResponseDetailDialog)

    def retranslateUi(self, RequestResponseDetailDialog):
        RequestResponseDetailDialog.setWindowTitle(QtGui.QApplication.translate("RequestResponseDetailDialog", "Response Detail", None, QtGui.QApplication.UnicodeUTF8))

