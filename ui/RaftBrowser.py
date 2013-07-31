# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RaftBrowser.ui'
#
# Created: Tue Aug  2 16:27:13 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_RaftBrowserDialog(object):
    def setupUi(self, RaftBrowserDialog):
        RaftBrowserDialog.setObjectName(_fromUtf8("RaftBrowserDialog"))
        RaftBrowserDialog.resize(1080, 564)
        self.verticalLayout = QtGui.QVBoxLayout(RaftBrowserDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.raftBrowserWebFrame = QtGui.QFrame(RaftBrowserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.raftBrowserWebFrame.sizePolicy().hasHeightForWidth())
        self.raftBrowserWebFrame.setSizePolicy(sizePolicy)
        self.raftBrowserWebFrame.setMinimumSize(QtCore.QSize(0, 320))
        self.raftBrowserWebFrame.setObjectName(_fromUtf8("raftBrowserWebFrame"))
        self.verticalLayout.addWidget(self.raftBrowserWebFrame)

        self.retranslateUi(RaftBrowserDialog)
        QtCore.QMetaObject.connectSlotsByName(RaftBrowserDialog)

    def retranslateUi(self, RaftBrowserDialog):
        RaftBrowserDialog.setWindowTitle(QtGui.QApplication.translate("RaftBrowserDialog", "RAFT - Web Browser", None, QtGui.QApplication.UnicodeUTF8))

