# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AnalysisConfig.ui'
#
# Created: Mon Aug  1 23:29:09 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_analysisConfigDialog(object):
    def setupUi(self, analysisConfigDialog):
        analysisConfigDialog.setObjectName(_fromUtf8("analysisConfigDialog"))
        analysisConfigDialog.resize(697, 524)
        self.horizontalLayout = QtGui.QHBoxLayout(analysisConfigDialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.DialogFrame = QtGui.QFrame(analysisConfigDialog)
        self.DialogFrame.setObjectName(_fromUtf8("DialogFrame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.DialogFrame)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.splitter = QtGui.QSplitter(self.DialogFrame)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.TopWidget = QtGui.QWidget(self.splitter)
        self.TopWidget.setObjectName(_fromUtf8("TopWidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.TopWidget)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.splitter_2 = QtGui.QSplitter(self.TopWidget)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.analyzerList = QtGui.QTreeWidget(self.splitter_2)
        self.analyzerList.setColumnCount(2)
        self.analyzerList.setObjectName(_fromUtf8("analyzerList"))
        self.analyzerList.header().setDefaultSectionSize(200)
        self.analyzerConfig = QtGui.QTreeWidget(self.splitter_2)
        self.analyzerConfig.setIndentation(20)
        self.analyzerConfig.setColumnCount(2)
        self.analyzerConfig.setObjectName(_fromUtf8("analyzerConfig"))
        self.analyzerConfig.header().setDefaultSectionSize(200)
        self.horizontalLayout_2.addWidget(self.splitter_2)
        self.BottomWidget = QtGui.QWidget(self.splitter)
        self.BottomWidget.setObjectName(_fromUtf8("BottomWidget"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.BottomWidget)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.saveButton = QtGui.QPushButton(self.BottomWidget)
        self.saveButton.setObjectName(_fromUtf8("saveButton"))
        self.horizontalLayout_4.addWidget(self.saveButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.addnodeButton = QtGui.QPushButton(self.BottomWidget)
        self.addnodeButton.setObjectName(_fromUtf8("addnodeButton"))
        self.horizontalLayout_4.addWidget(self.addnodeButton)
        self.delnodeButton = QtGui.QPushButton(self.BottomWidget)
        self.delnodeButton.setObjectName(_fromUtf8("delnodeButton"))
        self.horizontalLayout_4.addWidget(self.delnodeButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.analyzerDesc = QtGui.QTextEdit(self.BottomWidget)
        self.analyzerDesc.setEnabled(False)
        self.analyzerDesc.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.analyzerDesc.setObjectName(_fromUtf8("analyzerDesc"))
        self.verticalLayout_4.addWidget(self.analyzerDesc)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.defaultsButton = QtGui.QPushButton(self.BottomWidget)
        self.defaultsButton.setObjectName(_fromUtf8("defaultsButton"))
        self.horizontalLayout_3.addWidget(self.defaultsButton)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.closeButton = QtGui.QPushButton(self.BottomWidget)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.horizontalLayout_3.addWidget(self.closeButton)
        self.saveAllButton = QtGui.QPushButton(self.BottomWidget)
        self.saveAllButton.setEnabled(True)
        self.saveAllButton.setToolTip(_fromUtf8(""))
        self.saveAllButton.setObjectName(_fromUtf8("saveAllButton"))
        self.horizontalLayout_3.addWidget(self.saveAllButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.addWidget(self.splitter)
        self.horizontalLayout.addWidget(self.DialogFrame)

        self.retranslateUi(analysisConfigDialog)
        QtCore.QMetaObject.connectSlotsByName(analysisConfigDialog)

    def retranslateUi(self, analysisConfigDialog):
        analysisConfigDialog.setWindowTitle(QtGui.QApplication.translate("analysisConfigDialog", "Analysis Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.analyzerList.headerItem().setText(0, QtGui.QApplication.translate("analysisConfigDialog", "Analyzer", None, QtGui.QApplication.UnicodeUTF8))
        self.analyzerList.headerItem().setText(1, QtGui.QApplication.translate("analysisConfigDialog", "Enabled", None, QtGui.QApplication.UnicodeUTF8))
        self.analyzerConfig.headerItem().setText(0, QtGui.QApplication.translate("analysisConfigDialog", "Parameter", None, QtGui.QApplication.UnicodeUTF8))
        self.analyzerConfig.headerItem().setText(1, QtGui.QApplication.translate("analysisConfigDialog", "Value", None, QtGui.QApplication.UnicodeUTF8))
        self.saveButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "Save Selected Analyzer", None, QtGui.QApplication.UnicodeUTF8))
        self.addnodeButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "+", None, QtGui.QApplication.UnicodeUTF8))
        self.delnodeButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "-", None, QtGui.QApplication.UnicodeUTF8))
        self.defaultsButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "Defaults", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.saveAllButton.setText(QtGui.QApplication.translate("analysisConfigDialog", "Save All (currently Enable/Disable only)", None, QtGui.QApplication.UnicodeUTF8))

