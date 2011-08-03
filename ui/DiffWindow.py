# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DiffWindow.ui'
#
# Created: Sun Oct  3 00:57:43 2010
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_DiffWindow(object):
    def setupUi(self, DiffWindow):
        DiffWindow.setObjectName("DiffWindow")
        DiffWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(DiffWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter_2 = QtGui.QSplitter(self.centralwidget)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName("splitter_2")
        self.splitter = QtGui.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.leftTree = QtGui.QTreeWidget(self.splitter)
        self.leftTree.setObjectName("leftTree")
        self.rightTree = QtGui.QTreeWidget(self.splitter)
        self.rightTree.setObjectName("rightTree")
        self.diffView = QtWebKit.QWebView(self.splitter_2)
        self.diffView.setUrl(QtCore.QUrl("about:blank"))
        self.diffView.setObjectName("diffView")
        self.verticalLayout.addWidget(self.splitter_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.diffCloseButton = QtGui.QPushButton(self.centralwidget)
        self.diffCloseButton.setObjectName("diffCloseButton")
        self.horizontalLayout.addWidget(self.diffCloseButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        DiffWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(DiffWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        DiffWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(DiffWindow)
        self.statusbar.setObjectName("statusbar")
        DiffWindow.setStatusBar(self.statusbar)

        self.retranslateUi(DiffWindow)
        QtCore.QObject.connect(self.diffCloseButton, QtCore.SIGNAL("clicked()"), DiffWindow.close)
        QtCore.QMetaObject.connectSlotsByName(DiffWindow)

    def retranslateUi(self, DiffWindow):
        DiffWindow.setWindowTitle(QtGui.QApplication.translate("DiffWindow", "Diff Window", None, QtGui.QApplication.UnicodeUTF8))
        self.leftTree.headerItem().setText(0, QtGui.QApplication.translate("DiffWindow", "Id", None, QtGui.QApplication.UnicodeUTF8))
        self.leftTree.headerItem().setText(1, QtGui.QApplication.translate("DiffWindow", "URL", None, QtGui.QApplication.UnicodeUTF8))
        self.rightTree.headerItem().setText(0, QtGui.QApplication.translate("DiffWindow", "Id", None, QtGui.QApplication.UnicodeUTF8))
        self.rightTree.headerItem().setText(1, QtGui.QApplication.translate("DiffWindow", "URL", None, QtGui.QApplication.UnicodeUTF8))
        self.diffCloseButton.setText(QtGui.QApplication.translate("DiffWindow", "Close", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
