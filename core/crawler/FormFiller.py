#
# Class to manage filling form values
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
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

from PyQt4.QtCore import Qt, QObject, SIGNAL

from core.data.FormFillValues import FormFillValues
from core.data.FormFillPatterns import FormFillPatterns

import re

class FormFiller(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework

        self.formFillValues = FormFillValues()
        self.formFillPatterns = FormFillPatterns()

        self.re_number_pattern = re.compile('num|number', re.I)

        self.pattern_matches = []
    
        self.framework.subscribe_raft_config_populated(self.configuration_populated)
        self.framework.subscribe_raft_config_updated(self.configuration_updated)

    def configuration_populated(self):
        self.formFillValues.rehydrate(self.framework.get_raft_config_value('FORMFILL.VALUES'))
        self.formFillPatterns.rehydrate(self.framework.get_raft_config_value('FORMFILL.PATTERNS'))
        self.make_pattern_matches()

    def configuration_updated(self, name, value):
        if name == 'FORMFILL.VALUES':
            self.formFillValues.rehydrate(value)
        elif name == 'FORMFILL.PATTERNS':
            self.formFillPatterns.rehydrate(value)
            self.make_pattern_matches()

    def make_pattern_matches(self):
        new_pattern_matches = []

        self.add_pattern(new_pattern_matches, self.formFillPatterns.FirstName, self.fill_FirstName)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.LastName, self.fill_LastName)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.EmailAddress, self.fill_EmailAddress)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Company, self.fill_Company)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Address1, self.fill_Address1)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Address2, self.fill_Address2)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.City, self.fill_City)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.State, self.fill_State)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.ZipCode, self.fill_ZipCode)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Country, self.fill_Country)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Phone, self.fill_Phone)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.SSN, self.fill_SSN)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.BirthDate, self.fill_BirthDate)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Passport, self.fill_Passport)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.CreditCard, self.fill_CreditCard)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.PostalCode, self.fill_PostalCode)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.IDNumber, self.fill_IDNumber)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.HomePageUrl, self.fill_HomePageUrl)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Username, self.fill_Username)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.Password, self.fill_Password)
        self.add_pattern(new_pattern_matches, self.formFillPatterns.FullName, self.fill_FullName)

        self.pattern_matches = new_pattern_matches
    
    def add_pattern(self, new_pattern_matches, match_string, func):
        new_pattern_matches.append((re.compile(match_string, re.I), func))

    def fill_FirstName(self):
        return (self.formFillValues.FirstName, 'FirstName')
    def fill_LastName(self):
        return (self.formFillValues.LastName, 'LastName')
    def fill_EmailAddress(self):
        return (self.formFillValues.EmailAddress, 'EmailAddress')
    def fill_Company(self):
        return (self.formFillValues.Company, 'Company')
    def fill_Address1(self):
        return (self.formFillValues.Address1, 'Address1')
    def fill_Address2(self):
        return (self.formFillValues.Address2, 'Address2')
    def fill_City(self):
        return (self.formFillValues.City, 'City')
    def fill_State(self):
        return (self.formFillValues.State, 'State')
    def fill_ZipCode(self):
        return (self.formFillValues.ZipCode, 'ZipCode')
    def fill_Country(self):
        return (self.formFillValues.Country, 'Country')
    def fill_Phone(self):
        return (self.formFillValues.Phone, 'Phone')
    def fill_SSN(self):
        return (self.formFillValues.SSN, 'SSN')
    def fill_BirthDate(self):
        return (self.formFillValues.BirthDate, 'BirthDate')
    def fill_Passport(self):
        return (self.formFillValues.Passport, 'Passport')
    def fill_CreditCard(self):
        return (self.formFillValues.CreditCard, 'CreditCard')
    def fill_PostalCode(self):
        return (self.formFillValues.PostalCode, 'PostalCode')
    def fill_IDNumber(self):
        return (self.formFillValues.IDNumber, 'IDNumber')
    def fill_HomePageUrl(self):
        return (self.formFillValues.HomePageUrl, 'HomePageUrl')
    def fill_Username(self):
        return (self.formFillValues.Username, 'Username')
    def fill_Password(self):
        return (self.formFillValues.Password, 'Password')
    def fill_FullName(self):
        # TODO: added Last, First ?
        return (self.formFillValues.FirstName + ' ' + self.formFillValues.LastName, 'FullName')
    def fill_UnknownText(self):
        return (self.formFillValues.UnknownText, 'UnknownText')
    def fill_UnknownNumber(self):
        return (self.formFillValues.UnknownNumber, 'UnknownNumber')

    def fill_GenericData(self, name, Id, Class):
        if self.re_number_pattern.search(name) or self.re_number_pattern.search(Id) or self.re_number_pattern.search(Class):
            return_value, return_type =  self.fill_UnknownNumber()
        else:
            return_value, return_type =  self.fill_UnknownText()
        return return_value, return_type

    def populate_generic_value(self, name, Id, value, Type, Class, required, maxlength, accept, label):
        return_value, return_type = self.fill_GenericData(name, Id, Class)
        return return_value

    def populate_form_value(self, name, Id, value, Type, Class, required, maxlength, accept, label):
        match = None
        if Type and Type in ('telephone',): # TODO: complete HTML5 list
            match = self.get_match(Type)
        if not match and name:
            match = self.get_match(name)
        if not match and Id:
            match = self.get_match(Id)
        if not match and Class:
            match = self.get_match(Class)
        if not match and label:
            match = self.get_match(label)

        if match:
            return_value, return_type = match
        elif not match and not value:
            return_value, return_type = self.fill_GenericData(name, Id, Class)
        else:
            return_value = value
            return_type = 'Default'

        return return_value, return_type

    def get_match(self, input_string):
        if not input_string:
            return None
        for pattern_match in self.pattern_matches:
            re_pattern, func = pattern_match
            # TODO: or match?
            m = re_pattern.search(input_string)
            if m:
                # TODO: in future, consider longest match?
                return func()
        return None
