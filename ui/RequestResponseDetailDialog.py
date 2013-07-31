# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RequestResponseDetailDialog.ui'
#
# Created: Fri Jul 26 13:41:09 2013
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_RequestResponseDetailDialog(object):
    def setupUi(self, RequestResponseDetailDialog):
        RequestResponseDetailDialog.setObjectName(_fromUtf8("RequestResponseDetailDialog"))
        RequestResponseDetailDialog.resize(400, 300)
        RequestResponseDetailDialog.setMaximumSize(QtCore.QSize(1024, 768))
        self.verticalLayout = QtGui.QVBoxLayout(RequestResponseDetailDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitter = QtGui.QSplitter(RequestResponseDetailDialog)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.detailWidget = QtGui.QFrame(self.splitter)
        self.detailWidget.setMaximumSize(QtCore.QSize(1024, 768))
        self.detailWidget.setFrameShape(QtGui.QFrame.StyledPanel)
        self.detailWidget.setFrameShadow(QtGui.QFrame.Raised)
        self.detailWidget.setObjectName(_fromUtf8("detailWidget"))
        self.tabWidget = QtGui.QTabWidget(self.splitter)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(RequestResponseDetailDialog)
        QtCore.QMetaObject.connectSlotsByName(RequestResponseDetailDialog)

    def retranslateUi(self, RequestResponseDetailDialog):
        RequestResponseDetailDialog.setWindowTitle(_translate("RequestResponseDetailDialog", "Response Detail", None))

