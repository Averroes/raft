#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2013 RAFT Team
#
# This file is part of RAFT.
#
# RAFT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# RAFT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RAFT.  If not, see <http://www.gnu.org/licenses/>.
#

import PyQt4
from PyQt4.QtCore import Qt, QObject, SIGNAL, QDateTime, QSize
from PyQt4.QtGui import *

from PyQt4 import Qsci

from actions import encoderlib
from utility.HexDump import HexDump

from utility import ScintillaHelpers

class EncoderTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.hexDump = HexDump()

        self.mainWindow.encodeButton.clicked.connect(self.encode_data)
        self.mainWindow.encodeWrapButton.clicked.connect(self.encode_wrap)
        self.mainWindow.encodeClearButton.clicked.connect(self.encode_clear_data)

        self.mainWindow.decodeButton.clicked.connect(self.decode_data)
        self.mainWindow.decodeWrapButton.clicked.connect(self.decode_wrap)
        self.mainWindow.decodeClearButton.clicked.connect(self.decode_clear_data)

        self.encoder_tabs = []
        self.decoder_tabs = []
        self.mainTab = QWidget(self.mainWindow.encoderTabWidget)
        self.make_encoder_decoder_display_tab(self.mainTab)
        self.mainWindow.encoderTabWidget.addTab(self.mainTab, 'Encoding/Decoding')

    def make_encoder_decoder_display_tab(self, parentWidget):
        currentWidget = parentWidget
        vbox_layout = QVBoxLayout(currentWidget)

        encoderTabWidget = QTabWidget(currentWidget)
        decoderTabWidget = QTabWidget(currentWidget)

        # TODO: finish making this dynamically expandable
        self.encoderTextEdit, self.encoderHexEdit = self.make_text_hex_tab(encoderTabWidget)
        self.decoderTextEdit, self.decoderHexEdit = self.make_text_hex_tab(decoderTabWidget)

        vbox_layout.addWidget(encoderTabWidget)
        vbox_layout.addWidget(decoderTabWidget)

        encoderTabWidget.currentChanged.connect(self.encoder_tab_change)
        decoderTabWidget.currentChanged.connect(self.decoder_tab_change)

        self.encoder_tabs.append(encoderTabWidget)
        self.decoder_tabs.append(decoderTabWidget)

    def make_text_hex_tab(self, currentWidget):

        thisTabWidget = currentWidget

        textTab = QWidget(thisTabWidget)
        thisTabWidget.addTab(textTab, 'Text')
        hexTab = QWidget(thisTabWidget)
        thisTabWidget.addTab(hexTab, 'Hex')

        vlayout_text = QVBoxLayout(textTab)
        thisTextEdit = QTextEdit(textTab)
        vlayout_text.addWidget(thisTextEdit)

        vlayout_hex = QVBoxLayout(hexTab)
        thisHexEdit = Qsci.QsciScintilla(hexTab)
        ScintillaHelpers.SetScintillaProperties(self.framework, thisHexEdit, 'monospace')

        vlayout_hex.addWidget(thisHexEdit)

        return (thisTextEdit, thisHexEdit)

    def encode_data(self):
        """ Encode the specified value """
        tabInstance = self.encoder_tabs[self.mainWindow.encoderTabWidget.currentIndex()]
        if 0 == tabInstance.currentIndex():
            # read from text
            encode_value = self.encoderTextEdit.toPlainText()
        elif 1 == tabInstance.currentIndex():
            # read from hex
            encode_value = self.hexDump.undump(self.encoderHexEdit.text())
        encode_method = self.mainWindow.encodingMethodCombo.currentText()
        value = encoderlib.encode_values(encode_value, encode_method)
        self.decoderTextEdit.setPlainText(value)
        self.decoderHexEdit.setText(self.hexDump.dump(value.encode('utf-8')))
        
    def encode_wrap(self):
        """ Wrap the specified values in the encode window """
        
        encode_value = str(self.encoderTextEdit.toPlainText())
        wrap_value = self.mainWindow.encodingWrapCombo.currentText()
        value = encoderlib.wrap_encode(encode_value, wrap_value)
        self.encoderTextEdit.setPlainText(value)

    def encode_clear_data(self):
        self.encoderTextEdit.setPlainText('')
        self.encoderHexEdit.setText('')
        
    def decode_data(self):
        """ Decode the specified value from the decoder interface """
        decode_value = str(self.decoderTextEdit.toPlainText())
        decode_method = self.mainWindow.decodeMethodCombo.currentText()
        value = encoderlib.decode_values(decode_value, decode_method)
        if isinstance(value, bytes):
            self.encoderTextEdit.setPlainText(value.decode('utf-8', 'replace'))
            self.encoderHexEdit.setText(self.hexDump.dump(value))
        else:
            self.encoderTextEdit.setPlainText(value)
            self.encoderHexEdit.setText(self.hexDump.dump(value.encode('utf-8')))

    def decode_wrap(self):
        """ Wrap the specified values in the decode window """
        decode_value = str(self.decoderTextEdit.toPlainText())
        wrap_value = self.mainWindow.decodeWrapCombo.currentText()
        value = encoderlib.wrap_decode(decode_value, wrap_value)
        self.decoderTextEdit.setPlainText(value)

    def decode_clear_data(self):
        self.decoderTextEdit.setPlainText('')
        self.decoderHexEdit.setText('')

    def encoder_tab_change(self, index):
        self.handle_text_hex_tab_switch(index, self.encoderTextEdit, self.encoderHexEdit)

    def decoder_tab_change(self, index):
        self.handle_text_hex_tab_switch(index, self.decoderTextEdit, self.decoderHexEdit)

    def handle_text_hex_tab_switch(self, index, textEdit, hexEdit):
        # TODO: make this dynamic instead of depending on hard-coded values
        currentIndex = self.mainWindow.encoderTabWidget.currentIndex()
        if 0 == currentIndex:
            if 0 == index:
                # Going to Text
                value = hexEdit.text()
                if value:
                    data = self.hexDump.undump(value)
                    textEdit.setPlainText((data.decode('utf-8', 'replace')))
            elif 1 == index:
                value = textEdit.toPlainText()
                if value:
                    hexEdit.setText(self.hexDump.dump(value.encode('utf-8')))
