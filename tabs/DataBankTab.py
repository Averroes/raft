#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#         Nathan Hamiel
#
# Copyright (c) 2011 RAFT Team
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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex

import PyQt4
from PyQt4.QtGui import *

from core.data.FormFillValues import FormFillValues
from core.data.FormFillPatterns import FormFillPatterns
from core.fuzzer import Payloads

class DataBankTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.formFillValues = FormFillValues()
        self.formFillPatterns = FormFillPatterns()

        self.mainWindow.dbankPayloadsBox.activated.connect(self.fill_fuzz_values)
        
        self.Attacks = Payloads.Payloads(self.framework)
        self.fill_payload_combo_box()

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_values()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def do_save_databank(self):
        self.save_formFillValues()
        self.save_formFillPatterns()

    def fill_values(self):
        self.fill_formFillValues()
        self.fill_formFillPatterns()

    def fill_formFillValues(self):
        self.formFillValues.rehydrate(self.framework.get_raft_config_value('FORMFILL.VALUES'))

        self.mainWindow.formFillFirstNameEdit.setText(self.formFillValues.FirstName)
        self.mainWindow.formFillLastNameEdit.setText(self.formFillValues.LastName)
        self.mainWindow.formFillEmailAddressEdit.setText(self.formFillValues.EmailAddress)
        self.mainWindow.formFillCompanyEdit.setText(self.formFillValues.Company)
        self.mainWindow.formFillAddress1Edit.setText(self.formFillValues.Address1)
        self.mainWindow.formFillAddress2Edit.setText(self.formFillValues.Address2)
        self.mainWindow.formFillCityEdit.setText(self.formFillValues.City)
        self.mainWindow.formFillStateEdit.setText(self.formFillValues.State)
        self.mainWindow.formFillZipCodeEdit.setText(self.formFillValues.ZipCode)
        self.mainWindow.formFillCountryEdit.setText(self.formFillValues.Country)
        self.mainWindow.formFillPhoneEdit.setText(self.formFillValues.Phone)
        self.mainWindow.formFillSSNEdit.setText(self.formFillValues.SSN)
        self.mainWindow.formFillBirthDateEdit.setText(self.formFillValues.BirthDate)
        self.mainWindow.formFillPassportEdit.setText(self.formFillValues.Passport)
        self.mainWindow.formFillCreditCardEdit.setText(self.formFillValues.CreditCard)
        self.mainWindow.formFillPostalCodeEdit.setText(self.formFillValues.PostalCode)
        self.mainWindow.formFillIDNumberEdit.setText(self.formFillValues.IDNumber)
        self.mainWindow.formFillHomePageUrlEdit.setText(self.formFillValues.HomePageUrl)
        self.mainWindow.formFillUsernameEdit.setText(self.formFillValues.Username)
        self.mainWindow.formFillPasswordEdit.setText(self.formFillValues.Password)
        self.mainWindow.formFillUnknownTextEdit.setText(self.formFillValues.UnknownText)
        self.mainWindow.formFillUnknownNumberEdit.setText(self.formFillValues.UnknownNumber)
        
    def save_formFillValues(self):
        self.formFillValues.FirstName = str(self.mainWindow.formFillFirstNameEdit.text().toUtf8())
        self.formFillValues.LastName = str(self.mainWindow.formFillLastNameEdit.text().toUtf8())
        self.formFillValues.EmailAddress = str(self.mainWindow.formFillEmailAddressEdit.text().toUtf8())
        self.formFillValues.Company = str(self.mainWindow.formFillCompanyEdit.text().toUtf8())
        self.formFillValues.Address1 = str(self.mainWindow.formFillAddress1Edit.text().toUtf8())
        self.formFillValues.Address2 = str(self.mainWindow.formFillAddress2Edit.text().toUtf8())
        self.formFillValues.City = str(self.mainWindow.formFillCityEdit.text().toUtf8())
        self.formFillValues.State = str(self.mainWindow.formFillStateEdit.text().toUtf8())
        self.formFillValues.ZipCode = str(self.mainWindow.formFillZipCodeEdit.text().toUtf8())
        self.formFillValues.Country = str(self.mainWindow.formFillCountryEdit.text().toUtf8())
        self.formFillValues.Phone = str(self.mainWindow.formFillPhoneEdit.text().toUtf8())
        self.formFillValues.SSN = str(self.mainWindow.formFillSSNEdit.text().toUtf8())
        self.formFillValues.BirthDate = str(self.mainWindow.formFillBirthDateEdit.text().toUtf8())
        self.formFillValues.Passport = str(self.mainWindow.formFillPassportEdit.text().toUtf8())
        self.formFillValues.CreditCard = str(self.mainWindow.formFillCreditCardEdit.text().toUtf8())
        self.formFillValues.PostalCode = str(self.mainWindow.formFillPostalCodeEdit.text().toUtf8())
        self.formFillValues.IDNumber = str(self.mainWindow.formFillIDNumberEdit.text().toUtf8())
        self.formFillValues.HomePageUrl = str(self.mainWindow.formFillHomePageUrlEdit.text().toUtf8())
        self.formFillValues.Username = str(self.mainWindow.formFillUsernameEdit.text().toUtf8())
        self.formFillValues.Password = str(self.mainWindow.formFillPasswordEdit.text().toUtf8())
        self.formFillValues.UnknownText = str(self.mainWindow.formFillUnknownTextEdit.text().toUtf8())
        self.formFillValues.UnknownNumber = str(self.mainWindow.formFillUnknownNumberEdit.text().toUtf8())

        self.framework.set_raft_config_value('FORMFILL.VALUES', self.formFillValues.flatten())

    def fill_formFillPatterns(self):
        self.formFillPatterns.rehydrate(self.framework.get_raft_config_value('FORMFILL.PATTERNS'))

        self.mainWindow.formFillFirstNamePattern.setText(self.formFillPatterns.FirstName)
        self.mainWindow.formFillLastNamePattern.setText(self.formFillPatterns.LastName)
        self.mainWindow.formFillEmailAddressPattern.setText(self.formFillPatterns.EmailAddress)
        self.mainWindow.formFillCompanyPattern.setText(self.formFillPatterns.Company)
        self.mainWindow.formFillAddress1Pattern.setText(self.formFillPatterns.Address1)
        self.mainWindow.formFillAddress2Pattern.setText(self.formFillPatterns.Address2)
        self.mainWindow.formFillCityPattern.setText(self.formFillPatterns.City)
        self.mainWindow.formFillStatePattern.setText(self.formFillPatterns.State)
        self.mainWindow.formFillZipCodePattern.setText(self.formFillPatterns.ZipCode)
        self.mainWindow.formFillCountryPattern.setText(self.formFillPatterns.Country)
        self.mainWindow.formFillPhonePattern.setText(self.formFillPatterns.Phone)
        self.mainWindow.formFillSSNPattern.setText(self.formFillPatterns.SSN)
        self.mainWindow.formFillBirthDatePattern.setText(self.formFillPatterns.BirthDate)
        self.mainWindow.formFillPassportPattern.setText(self.formFillPatterns.Passport)
        self.mainWindow.formFillCreditCardPattern.setText(self.formFillPatterns.CreditCard)
        self.mainWindow.formFillPostalCodePattern.setText(self.formFillPatterns.PostalCode)
        self.mainWindow.formFillIDNumberPattern.setText(self.formFillPatterns.IDNumber)
        self.mainWindow.formFillHomePageUrlPattern.setText(self.formFillPatterns.HomePageUrl)
        self.mainWindow.formFillUsernamePattern.setText(self.formFillPatterns.Username)
        self.mainWindow.formFillPasswordPattern.setText(self.formFillPatterns.Password)
        self.mainWindow.formFillFullNamePattern.setText(self.formFillPatterns.FullName)
        
    def save_formFillPatterns(self):
        self.formFillPatterns.FirstName = str(self.mainWindow.formFillFirstNamePattern.text().toUtf8())
        self.formFillPatterns.LastName = str(self.mainWindow.formFillLastNamePattern.text().toUtf8())
        self.formFillPatterns.EmailAddress = str(self.mainWindow.formFillEmailAddressPattern.text().toUtf8())
        self.formFillPatterns.Company = str(self.mainWindow.formFillCompanyPattern.text().toUtf8())
        self.formFillPatterns.Address1 = str(self.mainWindow.formFillAddress1Pattern.text().toUtf8())
        self.formFillPatterns.Address2 = str(self.mainWindow.formFillAddress2Pattern.text().toUtf8())
        self.formFillPatterns.City = str(self.mainWindow.formFillCityPattern.text().toUtf8())
        self.formFillPatterns.State = str(self.mainWindow.formFillStatePattern.text().toUtf8())
        self.formFillPatterns.ZipCode = str(self.mainWindow.formFillZipCodePattern.text().toUtf8())
        self.formFillPatterns.Country = str(self.mainWindow.formFillCountryPattern.text().toUtf8())
        self.formFillPatterns.Phone = str(self.mainWindow.formFillPhonePattern.text().toUtf8())
        self.formFillPatterns.SSN = str(self.mainWindow.formFillSSNPattern.text().toUtf8())
        self.formFillPatterns.BirthDate = str(self.mainWindow.formFillBirthDatePattern.text().toUtf8())
        self.formFillPatterns.Passport = str(self.mainWindow.formFillPassportPattern.text().toUtf8())
        self.formFillPatterns.CreditCard = str(self.mainWindow.formFillCreditCardPattern.text().toUtf8())
        self.formFillPatterns.PostalCode = str(self.mainWindow.formFillPostalCodePattern.text().toUtf8())
        self.formFillPatterns.IDNumber = str(self.mainWindow.formFillIDNumberPattern.text().toUtf8())
        self.formFillPatterns.HomePageUrl = str(self.mainWindow.formFillHomePageUrlPattern.text().toUtf8())
        self.formFillPatterns.Username = str(self.mainWindow.formFillUsernamePattern.text().toUtf8())
        self.formFillPatterns.Password = str(self.mainWindow.formFillPasswordPattern.text().toUtf8())
        self.formFillPatterns.FullName = str(self.mainWindow.formFillFullNamePattern.text().toUtf8())

        self.framework.set_raft_config_value('FORMFILL.PATTERNS', self.formFillPatterns.flatten())
        
    
    def fill_payload_combo_box(self):
        
        comboBox = self.mainWindow.dbankPayloadsBox
        comboBox.clear()
        
        payloads = self.Attacks.list_files()
        for item in payloads:
            if item.startswith("."):
                pass
            else:
                comboBox.addItem(item)
                
    def fill_fuzz_values(self):
        """ Fill the textedit with the fuzz values of the selected payload file """
        
        filename = self.mainWindow.dbankPayloadsBox.currentText()
        
        # Clear the textedit
        self.mainWindow.dbankFuzzValuesEdit.clear()
        
        values = self.Attacks.read_data(str(filename))
        
        for item in values:
            self.mainWindow.dbankFuzzValuesEdit.appendPlainText(item)
            
