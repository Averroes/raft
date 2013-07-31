# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DiffCustomDialog.ui'
#
# Created: Wed Oct 20 23:37:28 2010
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_CustomDiffDialog(object):
    def setupUi(self, CustomDiffDialog):
        CustomDiffDialog.setObjectName("CustomDiffDialog")
        CustomDiffDialog.resize(832, 552)
        self.verticalLayout = QtGui.QVBoxLayout(CustomDiffDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtGui.QLabel(CustomDiffDialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.label = QtGui.QLabel(CustomDiffDialog)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.splitter_2 = QtGui.QSplitter(CustomDiffDialog)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName("splitter_2")
        self.splitter = QtGui.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.leftEdit = QtGui.QPlainTextEdit(self.splitter)
        self.leftEdit.setObjectName("leftEdit")
        self.rightEdit = QtGui.QPlainTextEdit(self.splitter)
        self.rightEdit.setObjectName("rightEdit")
        self.diffView = QtWebKit.QWebView(self.splitter_2)
        self.diffView.setUrl(QtCore.QUrl("about:blank"))
        self.diffView.setObjectName("diffView")
        self.verticalLayout.addWidget(self.splitter_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.diffButton = QtGui.QPushButton(CustomDiffDialog)
        self.diffButton.setObjectName("diffButton")
        self.horizontalLayout.addWidget(self.diffButton)
        self.closeButton = QtGui.QPushButton(CustomDiffDialog)
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout.addWidget(self.closeButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CustomDiffDialog)
        QtCore.QMetaObject.connectSlotsByName(CustomDiffDialog)

    def retranslateUi(self, CustomDiffDialog):
        CustomDiffDialog.setWindowTitle(QtGui.QApplication.translate("CustomDiffDialog", "Custom Diff Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("CustomDiffDialog", "Item 1", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("CustomDiffDialog", "Item 2", None, QtGui.QApplication.UnicodeUTF8))
        self.diffButton.setText(QtGui.QApplication.translate("CustomDiffDialog", "Diff", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("CustomDiffDialog", "Close", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
