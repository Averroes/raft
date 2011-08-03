#
# class to represent form fill values
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

import json

class FormFillPatterns():

    def __init__(self):
        # initial to default values
        self.FirstName = 'fname|firstname'
        self.LastName = 'lname|lastname'
        self.EmailAddress = 'email|e.mail'
        self.Company = 'company|companyname'
        self.Address1 = 'address|addr|addr1'
        self.Address2 = 'addr2|address2'
        self.City = 'city'
        self.State = 'state'
        self.ZipCode = 'zip|zipcode'
        self.Country = 'country|countrycode'
        self.Phone = 'phone|telephone'
        self.SSN = 'ssn|social'
        self.BirthDate = 'birthdate|dob'
        self.Passport = 'passport'
        self.CreditCard = 'creditcard|cc|ccnum'
        self.PostalCode = 'postal|postalcode'
        self.IDNumber = 'id|tin|taxid'
        self.HomePageUrl = 'url|homepage'
        self.Username = 'username|user'
        self.Password = 'password|pass'
        self.FullName = 'fullname|name'

    def rehydrate(self, blob):
        if not blob:
            return
        try:
            obj = json.loads(blob)
            for name, value in obj.iteritems():
                if not name:
                    pass
                elif 'FirstName' == name:
                    self.FirstName = value
                elif 'LastName' == name:
                    self.LastName = value
                elif 'EmailAddress' == name:
                    self.EmailAddress = value
                elif 'Company' == name:
                    self.Company = value
                elif 'Address1' == name:
                    self.Address1 = value
                elif 'Address2' == name:
                    self.Address2 = value
                elif 'City' == name:
                    self.City = value
                elif 'State' == name:
                    self.State = value
                elif 'ZipCode' == name:
                    self.ZipCode = value
                elif 'Country' == name:
                    self.Country = value
                elif 'Phone' == name:
                    self.Phone = value
                elif 'SSN' == name:
                    self.SSN = value
                elif 'BirthDate' == name:
                    self.BirthDate = value
                elif 'Passport' == name:
                    self.Passport = value
                elif 'CreditCard' == name:
                    self.CreditCard = value
                elif 'PostalCode' == name:
                    self.PostalCode = value
                elif 'IDNumber' == name:
                    self.IDNumber = value
                elif 'HomePageUrl' == name:
                    self.HomePageUrl = value
                elif 'Username' == name:
                    self.Username = value
                elif 'Password' == name:
                    self.Password = value
                elif 'FullName' == name:
                    self.FullName = value
                else:
                    # TODO: warn?
                    pass
        except ValueError:
            pass

    def flatten(self):
        values = {
            'FirstName' : self.FirstName,
            'LastName' : self.LastName,
            'EmailAddress' : self.EmailAddress,
            'Company' : self.Company,
            'Address1' : self.Address1,
            'Address2' : self.Address2,
            'City' : self.City,
            'State' : self.State,
            'ZipCode' : self.ZipCode,
            'Country' : self.Country,
            'Phone' : self.Phone,
            'SSN' : self.SSN,
            'BirthDate' : self.BirthDate,
            'Passport' : self.Passport,
            'CreditCard' : self.CreditCard,
            'PostalCode' : self.PostalCode,
            'IDNumber' : self.IDNumber,
            'HomePageUrl' : self.HomePageUrl,
            'Username' : self.Username,
            'Password' : self.Password,
            'FullName' : self.FullName,
            }

        return json.dumps(values)

