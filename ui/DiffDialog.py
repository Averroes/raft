# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DiffDialog.ui'
#
# Created: Mon Jun 20 20:16:48 2011
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DiffDialog(object):
    def setupUi(self, DiffDialog):
        DiffDialog.setObjectName(_fromUtf8("DiffDialog"))
        DiffDialog.resize(802, 557)
        self.verticalLayout = QtGui.QVBoxLayout(DiffDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.customButton = QtGui.QToolButton(DiffDialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("images/diff-icon-16.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.customButton.setIcon(icon)
        self.customButton.setObjectName(_fromUtf8("customButton"))
        self.horizontalLayout_2.addWidget(self.customButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.splitter_2 = QtGui.QSplitter(DiffDialog)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.splitter = QtGui.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.leftTree = QtGui.QTreeWidget(self.splitter)
        self.leftTree.setObjectName(_fromUtf8("leftTree"))
        self.rightTree = QtGui.QTreeWidget(self.splitter)
        self.rightTree.setObjectName(_fromUtf8("rightTree"))
        self.diffView = QtWebKit.QWebView(self.splitter_2)
        self.diffView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.diffView.setObjectName(_fromUtf8("diffView"))
        self.verticalLayout.addWidget(self.splitter_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.clearButton = QtGui.QPushButton(DiffDialog)
        self.clearButton.setObjectName(_fromUtf8("clearButton"))
        self.horizontalLayout.addWidget(self.clearButton)
        self.closeButton = QtGui.QPushButton(DiffDialog)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.horizontalLayout.addWidget(self.closeButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(DiffDialog)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DiffDialog.close)
        QtCore.QMetaObject.connectSlotsByName(DiffDialog)

    def retranslateUi(self, DiffDialog):
        DiffDialog.setWindowTitle(QtGui.QApplication.translate("DiffDialog", "Diff Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.customButton.setText(QtGui.QApplication.translate("DiffDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.leftTree.headerItem().setText(0, QtGui.QApplication.translate("DiffDialog", "Id", None, QtGui.QApplication.UnicodeUTF8))
        self.leftTree.headerItem().setText(1, QtGui.QApplication.translate("DiffDialog", "URL", None, QtGui.QApplication.UnicodeUTF8))
        self.rightTree.headerItem().setText(0, QtGui.QApplication.translate("DiffDialog", "Id", None, QtGui.QApplication.UnicodeUTF8))
        self.rightTree.headerItem().setText(1, QtGui.QApplication.translate("DiffDialog", "URL", None, QtGui.QApplication.UnicodeUTF8))
        self.clearButton.setText(QtGui.QApplication.translate("DiffDialog", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("DiffDialog", "Close", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
