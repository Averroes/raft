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
        self.formFillValues.FirstName = self.mainWindow.formFillFirstNameEdit.text()
        self.formFillValues.LastName = self.mainWindow.formFillLastNameEdit.text()
        self.formFillValues.EmailAddress = self.mainWindow.formFillEmailAddressEdit.text()
        self.formFillValues.Company = self.mainWindow.formFillCompanyEdit.text()
        self.formFillValues.Address1 = self.mainWindow.formFillAddress1Edit.text()
        self.formFillValues.Address2 = self.mainWindow.formFillAddress2Edit.text()
        self.formFillValues.City = self.mainWindow.formFillCityEdit.text()
        self.formFillValues.State = self.mainWindow.formFillStateEdit.text()
        self.formFillValues.ZipCode = self.mainWindow.formFillZipCodeEdit.text()
        self.formFillValues.Country = self.mainWindow.formFillCountryEdit.text()
        self.formFillValues.Phone = self.mainWindow.formFillPhoneEdit.text()
        self.formFillValues.SSN = self.mainWindow.formFillSSNEdit.text()
        self.formFillValues.BirthDate = self.mainWindow.formFillBirthDateEdit.text()
        self.formFillValues.Passport = self.mainWindow.formFillPassportEdit.text()
        self.formFillValues.CreditCard = self.mainWindow.formFillCreditCardEdit.text()
        self.formFillValues.PostalCode = self.mainWindow.formFillPostalCodeEdit.text()
        self.formFillValues.IDNumber = self.mainWindow.formFillIDNumberEdit.text()
        self.formFillValues.HomePageUrl = self.mainWindow.formFillHomePageUrlEdit.text()
        self.formFillValues.Username = self.mainWindow.formFillUsernameEdit.text()
        self.formFillValues.Password = self.mainWindow.formFillPasswordEdit.text()
        self.formFillValues.UnknownText = self.mainWindow.formFillUnknownTextEdit.text()
        self.formFillValues.UnknownNumber = self.mainWindow.formFillUnknownNumberEdit.text()

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
        self.formFillPatterns.FirstName = self.mainWindow.formFillFirstNamePattern.text()
        self.formFillPatterns.LastName = self.mainWindow.formFillLastNamePattern.text()
        self.formFillPatterns.EmailAddress = self.mainWindow.formFillEmailAddressPattern.text()
        self.formFillPatterns.Company = self.mainWindow.formFillCompanyPattern.text()
        self.formFillPatterns.Address1 = self.mainWindow.formFillAddress1Pattern.text()
        self.formFillPatterns.Address2 = self.mainWindow.formFillAddress2Pattern.text()
        self.formFillPatterns.City = self.mainWindow.formFillCityPattern.text()
        self.formFillPatterns.State = self.mainWindow.formFillStatePattern.text()
        self.formFillPatterns.ZipCode = self.mainWindow.formFillZipCodePattern.text()
        self.formFillPatterns.Country = self.mainWindow.formFillCountryPattern.text()
        self.formFillPatterns.Phone = self.mainWindow.formFillPhonePattern.text()
        self.formFillPatterns.SSN = self.mainWindow.formFillSSNPattern.text()
        self.formFillPatterns.BirthDate = self.mainWindow.formFillBirthDatePattern.text()
        self.formFillPatterns.Passport = self.mainWindow.formFillPassportPattern.text()
        self.formFillPatterns.CreditCard = self.mainWindow.formFillCreditCardPattern.text()
        self.formFillPatterns.PostalCode = self.mainWindow.formFillPostalCodePattern.text()
        self.formFillPatterns.IDNumber = self.mainWindow.formFillIDNumberPattern.text()
        self.formFillPatterns.HomePageUrl = self.mainWindow.formFillHomePageUrlPattern.text()
        self.formFillPatterns.Username = self.mainWindow.formFillUsernamePattern.text()
        self.formFillPatterns.Password = self.mainWindow.formFillPasswordPattern.text()
        self.formFillPatterns.FullName = self.mainWindow.formFillFullNamePattern.text()

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
            
            
    
            
