#
# This module contains logic for accessing the database
#
# Authors: 
#          Nathan Hamiel
#          Gregory Fleischer (gfleischer@gmail.com)
#          Justin Engler
#          Seth Law
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

import os, hashlib, zlib, traceback
import shutil
import time,datetime
import uuid
import sqlite3
from sqlite3 import dbapi2 as sqlite

from PyQt4.QtCore import QMutex
from core.database.constants import *

class Compressed(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

def adapt_compressed(compressed):
    return buffer(zlib.compress(compressed.value))

def convert_compressed(blob):
    return Compressed(zlib.decompress(str(blob)))

class Db:
    """ Db database class """

    def __init__(self, version):
        self.version = version

    def connect(self, filename):

        version = self.version

        # Register the adapter
        sqlite.register_adapter(Compressed, adapt_compressed)
        sqlite.register_converter("compressed", convert_compressed)

        self.conn = self.get_connection(filename, version)

        self.filename = filename
        self.threadMutex = QMutex()
        self.threadCursors = []
        self.qlock = QMutex()

        self.hashval_lookup = {}
        self.hashalgo = hashlib.sha256

        # perform any upgrade now that all internal values are setup
        cursor = self.conn.cursor()
        need_upgrade, dbversion = self.upgrade_is_needed(cursor, version)
        if need_upgrade:
            cursor.close()
            self.conn.close()
            self.do_backup(self.filename)
            self.conn = self.get_connection(self.filename, version)
            cursor = self.conn.cursor()
            self.perform_upgrade(cursor, dbversion, version)

    def get_connection(self, filename, version):
        if os.path.exists(filename):
            conn = sqlite.connect(filename, detect_types=sqlite.PARSE_DECLTYPES, check_same_thread = False)
            if not self.validate_db(conn):
                conn.close()
                self.create_raft_db(filename, self.version)
                conn = sqlite.connect(filename, detect_types=sqlite.PARSE_DECLTYPES, check_same_thread = False)
        else:
            self.create_raft_db(filename, self.version)
            conn = sqlite.connect(filename, detect_types=sqlite.PARSE_DECLTYPES, check_same_thread = False)
        
        #disabled for speed tests
        #conn.row_factory=sqlite3.Row
        return conn

    def close(self):
        # TODO: lock?
        for cur in self.threadCursors:
            cur.close()
        self.conn.close()

    def create_raft_db(self, filename, version):
        """ Creates a new blank RAFT database. """
        
        # Register the adapter
        sqlite.register_adapter(Compressed, adapt_compressed)
        sqlite.register_converter("compressed", convert_compressed)

        conn = sqlite.connect(filename, detect_types=sqlite.PARSE_DECLTYPES)
        cursor = conn.cursor()

        cursor.execute(""" CREATE TABLE raft (Name TEXT PRIMAY KEY NOT NULL UNIQUE, Value TEXT NULL) """)
        cursor.execute("""INSERT INTO raft (Name, Value) values (?, ?)""", ['VERSION', version])
        cursor.execute("""INSERT INTO raft (Name, Value) values (?, ?)""", ['UUID', uuid.uuid4().hex])

        cursor.execute(""" CREATE TABLE content_data (Hashval VARCHAR(64)  PRIMARY KEY NOT NULL UNIQUE, Data compressed) """)

        cursor.execute(""" CREATE TABLE responses (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                Url TEXT, ReqHeaders compressed, ReqDataHashval VARCHAR(64), ResHeaders compressed,
                ResContentHashval VARCHAR(64), Status INTEGER, Length INTEGER, ReqTime INTEGER, ReqDate TEXT,
                Notes TEXT, Results TEXT, Confirmed BOOL,
                ReqMethod TEXT, HostIP TEXT, ResContentType TEXT, DataOrigin TEXT, ReqHost TEXT) """)

        cursor.execute(""" CREATE TABLE analysis (Id INTEGER PRIMARY KEY NOT NULL UNIQUE, Results TEXT) """)

        cursor.execute(""" CREATE TABLE differ_items (response_id INTEGER PRIMARY KEY NOT NULL UNIQUE, time_added INTEGER) """)

        cursor.execute(""" CREATE TABLE configuration (
                       Component TEXTNOT NULL,
                       ConfigName TEXT, 
                       ConfigValue compressed,
                       PRIMARY KEY (Component, ConfigName)
                       ) """)

        cursor.execute(""" CREATE TABLE vulnerabilities (
                       Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                       Hostname TEXT NOT NULL,
                       Port INTEGER NOT NULL,
                       Vulnerability TEXT NOT NULL,
                       Severity TEXT NOT NULL,
                       Url TEXT NOT NULL,
                       FalsePositive BOOL NOT NULL,
                       Remediation compressed
                       )""")

        cursor.execute("""CREATE TABLE vulnerability_parameters (
                       Vulnerability_Id INTEGER NOT NULL,
                       Num INTEGER NOT NULL,
                       ParamName INTEGER NOT NULL,
                       Payload TEXT,
                       Example TEXT,
                       PRIMARY KEY (Vulnerability_Id, Num),
                       FOREIGN KEY (Vulnerability_Id) REFERENCES vulnerabilities (Id)
                       )""")

        cursor.execute("""CREATE INDEX vulnerability_parameters_idx_1 ON vulnerability_parameters (Vulnerability_Id)""")

        cursor.execute("""CREATE TABLE requester_history (
                          Response_Id INTEGER PRIMARY KEY,
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                      )""")

        cursor.execute("""CREATE TABLE fuzzer_history (
                          Response_Id INTEGER PRIMARY KEY,
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                      )""")

        # TODO: finish this once what is needed is clearer
        cursor.execute("""CREATE TABLE sequences (
                          Id INTEGER PRIMARY KEY  AUTOINCREMENT NOT NULL UNIQUE, 
                          Name TEXT NOT NULL UNIQUE,
                          Sequence_Type TEXT,
                          Session_Detection BOOL NOT NULL,
                          Include_Media BOOL NOT NULL,
                          Use_Browser BOOL NOT NULL,
                          InSession_Pattern TEXT,
                          InSession_RE BOOL NOT NULL,
                          OutOfSession_Pattern TEXT,
                          OutOfSession_RE BOOL NOT NULL,
                          Dynamic_Data BOOL NOT NULL
                          )""")

        cursor.execute("""CREATE TABLE sequence_steps (
                          Sequence_Id INTEGER NOT NULL, 
                          StepNum INTEGER NOT NULL, 
                          Response_Id INTEGER NOT NULL, 
                          Is_Enabled BOOL NOT NULL,
                          Is_Hidden BOOL NOT NULL,
                          PRIMARY KEY (Sequence_Id, StepNum),
                          FOREIGN KEY (Sequence_Id) REFERENCES sequences (Id),
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )""")

        cursor.execute("""CREATE TABLE sequence_source_parameters (
                          Sequence_Id INTEGER NOT NULL, 
                          Response_Id INTEGER NOT NULL, 
                          Input_Location TEXT NOT NULL,
                          Input_Position INTEGER NOT NULL,
                          Input_Name TEXT,
                          Input_Type TEXT,
                          Input_Value Compressed,
                          Is_Dynamic BOOL NOT NULL,
                          PRIMARY KEY (Sequence_Id, Response_Id, Input_Location, Input_Position, Input_Type, Input_Name),
                          FOREIGN KEY (Sequence_Id) REFERENCES sequences (Id),
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )""")

        cursor.execute("""CREATE TABLE sequence_target_parameters (
                          Sequence_Id INTEGER NOT NULL, 
                          Response_Id INTEGER NOT NULL, 
                          Input_Location TEXT NOT NULL,
                          Input_Position INTEGER NOT NULL,
                          Input_Name TEXT,
                          Input_Value Compressed,
                          Is_Dynamic BOOL NOT NULL,
                          PRIMARY KEY (Sequence_Id, Response_Id, Input_Location, Input_Position, Input_Name),
                          FOREIGN KEY (Sequence_Id) REFERENCES sequences (Id),
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )""")

        cursor.execute("""CREATE TABLE sequence_cookies (
                          Sequence_Id INTEGER NOT NULL, 
                          Cookie_Domain TEXT NOT NULL,
                          Cookie_Name TEXT NOT NULL,
                          Cookie_Raw_Value Compressed,
                          Is_Dynamic BOOL NOT NULL,
                          PRIMARY KEY (Sequence_Id, Cookie_Domain, Cookie_Name),
                          FOREIGN KEY (Sequence_Id) REFERENCES sequences (Id)
                          )""")

        cursor.execute("""CREATE TABLE sequence_manual_items (
                          Response_Id INTEGER NOT NULL, 
                          Time_Added INTEGER,
                          PRIMARY KEY (Response_Id),
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )""")
        
        cursor.execute("""CREATE TABLE AnalysisRuns (
                                AnalysisRun_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                                timeran TIMESTAMP
                                );
                            """)

        cursor.execute("""CREATE TABLE AnalysisInstances (
                               AnalysisInstance_ID INTEGER PRIMARY KEY  AUTOINCREMENT NOT NULL UNIQUE,
                               friendlyName TEXT,
                               desc TEXT,
                               className TEXT,
                               AnalysisRun INTEGER,
                               resultclass TEXT,
                               FOREIGN KEY (AnalysisRun) REFERENCES AnalysisRuns (AnalysisRun_ID)
                               );
                            """)
        cursor.execute("""CREATE INDEX IDX_FK_AnalysisRun ON AnalysisInstances(AnalysisRun);""")
        
        cursor.execute("""CREATE TABLE AnalysisResultSet (
                                AnalysisResultSet_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                                AnalysisInstance INTEGER,
                                Response_analyzed INTEGER,
                                isOverallResult BOOLEAN,
                                context TEXT,
                                resultclass TEXT,
                                FOREIGN KEY (AnalysisInstance) REFERENCES AnalysisInstances(AnalysisInstance_ID)
                                --Can't make this an FK, is null sometimes.
                                --FOREIGN KEY (Response_analyzed) REFERENCES responses(Id) NULL
                                );
                            """)  
        cursor.execute("""CREATE INDEX IDX_FK_AnalysisInstance ON AnalysisResultSet(AnalysisInstance);""")
        cursor.execute("""CREATE INDEX IDX_FK_Response_analyzed ON AnalysisResultSet(Response_analyzed);""")
        
        cursor.execute("""CREATE TABLE AnalysisStats (
                               AnalysisStat_ID INTEGER PRIMARY KEY  AUTOINCREMENT NOT NULL UNIQUE,
                               statName TEXT,
                               statValue TEXT,
                               AnalysisResultSet INTEGER,
                               FOREIGN KEY (AnalysisResultSet) REFERENCES AnalysisResultSet (AnalysisResultSet_ID)
                               );
                            """)
        cursor.execute("""CREATE INDEX IDX_FK_AnalysisResultSet ON AnalysisStats(AnalysisResultSet);""")
        
        cursor.execute("""CREATE TABLE AnalysisSingleResult (
                               AnalysisSingleResult_ID INTEGER PRIMARY KEY  AUTOINCREMENT NOT NULL UNIQUE,
                               severity TEXT,
                               certainty TEXT,
                               type TEXT,
                               desc TEXT,
                               data TEXT,
                               spanstart INTEGER,
                               spanend INTEGER,
                               AnalysisResultSet INTEGER,
                               resultclass TEXT,
                               FOREIGN KEY (AnalysisResultSet) REFERENCES AnalysisResultSet (AnalysisResultSet_ID)
                               );
                            """)
        cursor.execute("""CREATE INDEX IDX_FK_AnalysisResultSetResult ON AnalysisSingleResult(AnalysisResultSet);""")


        cursor.execute("""CREATE TABLE dom_fuzzer_queue (
                          Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
                          Response_Id INTEGER NOT NULL,
                          Url TEXT NOT NULL, 
                          Target TEXT NOT NULL,
                          Param TEXT NOT NULL,
                          Test TEXT NOT NULL,
                          Status TEXT NOT NULL,
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )
                          """)

        cursor.execute("""CREATE TABLE dom_fuzzer_results (
                          Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
                          Response_Id INTEGER NOT NULL,
                          Url TEXT NOT NULL, 
                          Target TEXT NOT NULL,
                          Param TEXT NOT NULL,
                          Test TEXT NOT NULL,
                          Confidence TEXT NOT NULL,
                          Rendered_Data Compressed,
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id)
                          )
                          """)

        cursor.execute("""CREATE TABLE spider_pending_responses (
                          Response_Id INTEGER NOT NULL,
                          Request_Type TEXT NOT NULL,
                          Depth INTEGER NOT NULL,
                          Status TEXT NOT NULL,
                          FOREIGN KEY (Response_Id) REFERENCES responses (Id),
                          PRIMARY KEY (Response_Id, Request_Type)
                          )
                          """)

        cursor.execute("""CREATE TABLE spider_pending_analysis (
                          Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
                          Analysis_Type TEXT NOT NULL,
                          Content Compressed,
                          Url TEXT NOT NULL,
                          Depth INTEGER NOT NULL
                          )
                          """)

        cursor.execute("""CREATE TABLE spider_queue (
                          Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
                          Method TEXT NOT NULL, 
                          Url TEXT NOT NULL, 
                          Query_Params TEXT NOT NULL,
                          Encoding_Type TEXT NOT NULL,
                          Form_Params TEXT NOT NULL,
                          Referer TEXT NOT NULL,
                          Status TEXT NOT NULL,
                          Depth INTEGER NOT NULL
                          )
                          """)

        cursor.execute("""CREATE TABLE spider_internal_state (
                          State_Category TEXT NOT NULL, 
                          State_Key TEXT NOT NULL, 
                          State_Count INTEGER, 
                          State_Value TEXT, 
                          PRIMARY KEY (State_Category, State_Key)
                          )
                          """)

        cursor.execute("""INSERT INTO configuration (Component, ConfigName, ConfigValue) values (?, ?, ?)""", ['RAFT', 'black_hole_network', Compressed(str(True))])

        conn.commit()
        cursor.close()
        conn.close()

    def validate_db(self, conn):
        cursor = conn.cursor()
        cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""")
        rows = cursor.fetchall()
        found = False
        count = 0
        for row in rows:
            count += 1
            if 'raft' == str(row[0]):
                found = True
                break

        if not found and count > 0:
            raise Exception('Existing SQLITE database is not RAFT format')

        cursor.close()
        return found

    def upgrade_is_needed(self, cursor, version):
        cursor.execute("""SELECT Value FROM raft WHERE Name='VERSION'""")
        row = cursor.fetchone()
        dbversion = str(row[0])
        if version != dbversion:
            return True, dbversion
        return False, ''

    def do_backup(self, filename):
        backup_filename =  '%s.%d-backup' % (filename, int(time.time()))
        print('backing up %s to %s' % (filename, backup_filename))
        shutil.copy(filename, backup_filename)

    def perform_upgrade(self, cursor, dbversion, version):
        print('upgrading %s to version %s from %s' % (self.filename, version, dbversion))
        while version != dbversion:
            if '2011.7.14-alpha' == dbversion:
                dbversion = self.upgrade_to_2011_8_31_alpha(cursor)
            elif '2011.8.31-alpha' == dbversion:
                dbversion = self.upgrade_to_2011_9_1_alpha(cursor)
            else:
                raise Exception('Implement upgrade from %s to %s' % (dbversion, version))

    def read_responses_by_id(self, cursor, Id):
        """ Read a single row from the database providing the Id of the row to be returned. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                               cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, content_data cd1, content_data cd2 \
                               WHERE \
                               cd1.Hashval = ReqDataHashval and cd2.Hashval = ResContentHashval \
                               and Id=?", [str(Id)])
            response = cursor.fetchone()
            return(response)
        finally:
            self.qlock.unlock()

    def read_responses_info_by_id(self, cursor, Id):
        """ Read info for a single response row from the database providing the Id of the row to be returned. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, '' ReqHeaders, '' ReqData, '' ResHeaders, \
                               '' ResContent, Status, Length, ReqTime, ReqDate, '' Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses \
                               WHERE \
                               Id=?", [str(Id)])
            response = cursor.fetchone()
            return(response)
        finally:
            self.qlock.unlock()

    def read_responses_by_url(self, cursor, url):
        """ Read rows from the database providing the Url of the rows to be returned. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                               cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, content_data cd1, content_data cd2 \
                               WHERE \
                               cd1.Hashval = ReqDataHashval AND cd2.Hashval = ResContentHashval \
                               AND Url=?", [str(url)])
            return(cursor)
        finally:
            self.qlock.unlock()

    def read_responses_starting_with_url(self, cursor, url):
        """ Read rows from the database providing the Url of the rows to be returned. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                           cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                           Results, Confirmed, \
                           ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                           FROM responses, content_data cd1, content_data cd2 \
                           WHERE \
                           cd1.Hashval = ReqDataHashval AND cd2.Hashval = ResContentHashval \
                           AND Url LIKE ?", [str(url)+'%'])
            return(cursor)
        finally:
            self.qlock.unlock()

    def read_newer_responses_info(self, cursor, startId):
        """ Return all of the responses info from the database greater than startId. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, '' ReqHeaders, '' ReqData, '' ResHeaders, \
                           '' ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                           Results, Confirmed, \
                           ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                           FROM responses where Id > ?", [int(startId)])
            return(cursor)
        finally:
            self.qlock.unlock()

    def read_all_responses(self, cursor):
        """ Return all of the results from the database. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                           cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                           Results, Confirmed, \
                           ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                           FROM responses, content_data cd1, content_data cd2 \
                           WHERE \
                           cd1.Hashval = ReqDataHashval and cd2.Hashval = ResContentHashval")
            return(cursor)
        finally:
            self.qlock.unlock()

    def read_all_newer_responses(self, cursor, latestId):
        """ Return all of the results from the database. """
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                               cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, content_data cd1, content_data cd2 \
                               WHERE \
                               cd1.Hashval = ReqDataHashval and cd2.Hashval = ResContentHashval \
                               and Id > ?", [int(latestId)])
            return(cursor)
        finally:
            self.qlock.unlock()

    def get_sitemap_info(self, cursor, lastId):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, Status, ResHeaders FROM responses where Id > ?", [int(lastId)])
            return cursor
        finally:
            self.qlock.unlock()

    def get_all_sequences(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, \
                              Name, \
                              Sequence_Type, \
                              Session_Detection, \
                              Include_Media, \
                              Use_Browser, \
                              InSession_Pattern, \
                              InSession_RE, \
                              OutOfSession_Pattern, \
                              OutOfSession_RE, \
                              Dynamic_Data \
                           FROM sequences ORDER BY Id")
            return cursor
        finally:
            self.qlock.unlock()

    def get_sequence_items(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Name FROM sequences ORDER BY Id")
            return cursor
        finally:
            self.qlock.unlock()

    def get_sequence_by_id(self, cursor, sequenceId):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, \
                              Name, \
                              Sequence_Type, \
                              Session_Detection, \
                              Include_Media, \
                              Use_Browser, \
                              InSession_Pattern, \
                              InSession_RE, \
                              OutOfSession_Pattern, \
                              OutOfSession_RE, \
                              Dynamic_Data \
                           FROM sequences \
                           WHERE \
                              Id = ?", [sequenceId])
            return cursor.fetchone()
        finally:
            self.qlock.unlock()

    def insert_new_sequence(self, cursor, insertlist):
        self.qlock.lock()
        try:
            rowid = None
            cursor.execute("INSERT INTO sequences (\
                            Id, Name, Sequence_Type, Session_Detection, Include_Media, Use_Browser, \
                            InSession_Pattern, InSession_RE, \
                            OutOfSession_Pattern, OutOfSession_RE, Dynamic_Data \
                           ) values ( \
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? \
                           )", insertlist)

            cursor.execute('SELECT last_insert_rowid()')
            results = cursor.fetchone()
            if results:
                rowid = int(results[0])

            return rowid
        finally:
            self.qlock.unlock()

    def update_sequence(self, cursor, updatelist):
        self.qlock.lock()
        try:
            rowid = None
            cursor.execute("UPDATE sequences SET \
                            Name=?, Sequence_Type=?, Session_Detection=?, Include_Media=?, Use_Browser=?, \
                            InSession_Pattern=?, InSession_RE=?, \
                            OutOfSession_Pattern=?, OutOfSession_RE=?, Dynamic_Data=? \
                            WHERE Id=?", updatelist)
        finally:
            self.qlock.unlock()

    def get_sequence_steps(self, cursor, sequenceId):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Sequence_Id, StepNum, Response_Id, Is_Enabled, Is_Hidden FROM sequence_steps WHERE Sequence_Id=? ORDER BY StepNum", [sequenceId])
            return cursor
        finally:
            self.qlock.unlock()

    def clear_sequence_steps(self, cursor, sequenceId):
        self.qlock.lock()
        try:
            cursor.execute("DELETE FROM sequence_steps WHERE Sequence_Id=?", [sequenceId])
        finally:
            self.qlock.unlock()

    def insert_sequence_step(self, cursor, insertlist):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO sequence_steps ( \
                              Sequence_Id, StepNum, Response_Id, Is_Enabled, Is_Hidden \
                            ) values ( \
                              ?, ?, ?, ?, ? \
                            )", insertlist)

        finally:
            self.qlock.unlock()

    def delete_sequence(self, cursor, sequenceId):
        self.qlock.lock()
        try:
            cursor.execute("DELETE FROM sequence_cookies WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequence_target_parameters WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequence_source_parameters WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequence_steps WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequences WHERE Id=?", [sequenceId])
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.qlock.unlock()

    def clear_sequence_parameters(self, cursor, sequenceId):
        self.qlock.lock()
        try:
            cursor.execute("DELETE FROM sequence_source_parameters WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequence_target_parameters WHERE Sequence_Id=?", [sequenceId])
            cursor.execute("DELETE FROM sequence_cookies WHERE Sequence_Id=?", [sequenceId])
        finally:
            self.qlock.unlock()

    def insert_sequence_source_parameter(self, cursor, insertlist):
        self.qlock.lock()
        try:
            insertlist[SequenceSourceParameters.INPUT_VALUE] = Compressed(str(insertlist[SequenceSourceParameters.INPUT_VALUE]))
            cursor.execute("""INSERT INTO sequence_source_parameters (
                              Sequence_Id, 
                              Response_Id, 
                              Input_Location,
                              Input_Position,
                              Input_Type,
                              Input_Name,
                              Input_Value,
                              Is_Dynamic
                           ) values (
                             ?, ?, ?, ?, ?, ?, ?, ?
                           )""", insertlist)
        except Exception as error:
            print('FIX ME! ERROR: %s' % (traceback.format_exc(error)))
            for i in range(0, len(insertlist)):
                if i not in [SequenceSourceParameters.INPUT_VALUE]:
                    print('[%d] %s' % (i, insertlist[i]))
        finally:
            self.qlock.unlock()

    def insert_sequence_target_parameter(self, cursor, insertlist):
        self.qlock.lock()
        try:
            insertlist[SequenceTargetParameters.INPUT_VALUE] = Compressed(str(insertlist[SequenceTargetParameters.INPUT_VALUE]))
            cursor.execute("""INSERT INTO sequence_target_parameters (
                              Sequence_Id, 
                              Response_Id, 
                              Input_Location,
                              Input_Position,
                              Input_Name,
                              Input_Value,
                              Is_Dynamic
                           ) values (
                             ?, ?, ?, ?, ?, ?, ?
                           )""", insertlist)
        except Exception as error:
            print('FIX ME! ERROR: %s' % (traceback.format_exc(error)))
            for i in range(0, len(insertlist)):
                if i not in [SequenceTargetParameters.INPUT_VALUE]:
                    print('[%d] %s' % (i, insertlist[i]))
        finally:
            self.qlock.unlock()

    def insert_sequence_cookie(self, cursor, insertlist):
        self.qlock.lock()
        try:
            insertlist[SequenceCookies.COOKIE_RAW_VALUE] = Compressed(str(insertlist[SequenceCookies.COOKIE_RAW_VALUE]))
            cursor.execute("""INSERT INTO sequence_cookies (
                              Sequence_Id, 
                              Cookie_Domain,
                              Cookie_Name,
                              Cookie_Raw_Value,
                              Is_Dynamic
                           ) values (
                             ?, ?, ?, ?, ?
                           )""", insertlist)
        finally:
            self.qlock.unlock()

    def get_sequence_builder_manual_items(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Response_Id FROM sequence_manual_items ORDER BY Time_Added")
            return cursor
        finally:
            self.qlock.unlock()
        
    def add_sequence_builder_manual_item(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO sequence_manual_items (Response_Id, Time_Added) values (?, ?)", [int(Id), int(time.time())])
            self.commit()
            return True
        except sqlite.IntegrityError:
            return False
        finally:
            self.qlock.unlock()

    def clear_sequence_builder_manual_items(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("DELETE FROM sequence_manual_items")
            self.commit()
        finally:
            self.qlock.unlock()

    def get_all_vulnerabilities(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Hostname, Port, Vulnerability, Severity, Url, FalsePositive, Remediation \
                               FROM vulnerabilities")
            return cursor
        finally:
            self.qlock.unlock()

    def get_vulnerability_by_id(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Hostname, Port, Vulnerability, Severity, Url, FalsePositive, Remediation \
                               FROM vulnerabilities \
                               WHERE \
                               Id=?", [str(Id)])
            response = cursor.fetchone()
            return response
        finally:
            self.qlock.unlock()

    def insert_new_vulnerability(self, cursor, insertlist, AutoCommit = True):
        self.qlock.lock()
        try:
            insertlist[7] = Compressed(insertlist[7])
            cursor.execute("INSERT into vulnerabilities (\
                                 Id, Hostname, Port, Vulnerability, Severity, Url, FalsePositive, Remediation \
                                ) values (?, ?, ?, ?, ?, ?, ?, ?)", insertlist)
            if AutoCommit:
                self.commit()
        finally:
            self.qlock.unlock()

    def update_vulnerability(self, cursor, insertlist, AutoCommit = True):
        self.qlock.lock()
        try:
            insertlist[6] = Compressed(insertlist[6])
            cursor.execute("UPDATE vulnerabilities SET \
                                 Hostname=?, Port=?, Vulnerability=?, Severity=?, Url=?, FalsePositive=?, Remediation=? \
                                 WHERE Id=?", insertlist)
            if AutoCommit:
                self.commit()
        finally:
            self.qlock.unlock()

    def upsert_vulnerability_parameter(self, cursor, vulnerabilityId, insertlist, AutoCommit = True):
        self.qlock.lock()
        try:
            cursor.execute("SELECT count(1) FROM  vulnerability_parameters WHERE Vulnerability_id=? and Num=?",
                                [vulnerabilityId, insertlist[0]])
            count = int(cursor.fetchone()[0])
            if 0 == count:
                # TODO: gross
                insertlist.insert(0, vulnerabilityId)
                cursor.execute("INSERT INTO vulnerability_parameters (Vulnerability_id, Num, ParamName, Payload, Example) \
                                    VALUES (?,?,?,?,?)", insertlist)

            else:
                updatelist = insertlist[1:]
                updatelist.append(vulnerabilityId)
                updatelist.append(insertlist[0])
                cursor.execute("UPDATE vulnerability_parameters SET \
                                 ParamName=?, Payload=?, Example=?\
                                 WHERE Vulnerability_Id=? and Num=?", updatelist)
            if AutoCommit:
                self.commit()
        finally:
            self.qlock.unlock()

    def get_vulnerability_parameters(self, cursor, vulnerabilityId):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Num, ParamName, Payload, Example FROM vulnerability_parameters where \
                                 Vulnerability_Id=?", [vulnerabilityId])
            return cursor.fetchall()
        finally:
            self.qlock.unlock()


    def get_vulnerability_parameter_by_num(self, cursor, vulnerabilityId, Num):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Num, ParamName, Payload, Example FROM vulnerability_parameters where \
                                 Vulnerability_Id=? and Num = ?", [vulnerabilityId, Num])
            return cursor.fetchone()
        finally:
            self.qlock.unlock()

    def update_responses(self, cursor, notes, results, confirmed, Id):
        self.qlock.lock()
        try:
            """ Update specified values in the capture database. """
            cursor.execute("UPDATE responses SET Notes=?, Results=?, Confirmed=? WHERE Id=?", [notes, results, confirmed, Id])
            self.commit()
        finally:
            self.qlock.unlock()

    def truncate_response_data(self, cursor):
        self.qlock.lock()
        try:
            """ Truncate the responses table. """
            cursor.execute("DELETE FROM differ_items")
            cursor.execute("DELETE FROM responses")
            cursor.execute("DELETE FROM content_data")
            self.hashval_lookup.clear()
            self.commit()
        finally:
            self.qlock.unlock()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def set_insert_pragmas(self, cursor):
        cursor.execute('PRAGMA synchronous = OFF')
        cursor.execute('PRAGMA temp_store = MEMORY')

    def reset_pragmas(self, cursor):
        cursor.execute('PRAGMA synchronous = NORMAL')
        cursor.execute('PRAGMA temp_store = 0') # DEFAULT

    def insert_content_data(self, cursor, value):
        if not value or len(value) == 0:
            digest = ''
            value = ''
        else:
            h = self.hashalgo()
            h.update(value)
            digest = h.hexdigest()
        if not self.hashval_lookup.has_key(digest):
            try:
                cursor.execute("INSERT INTO content_data (Hashval, Data) VALUES (?, ?)", [digest, Compressed(value)])
                self.hashval_lookup[digest] = True
            except sqlite.IntegrityError:
                # okay if exists
                self.hashval_lookup[digest] = True
            except sqlite.DatabaseError, e:
                # okay if exists
                if 'not unique' in str(e):
                    self.hashval_lookup[digest] = True
                else:
                    raise
        return digest

    def insert_responses(self, cursor, values, AutoCommit = True):
        self.qlock.lock()
        try:
            """ Insert data in to the database """
            # Insert a Python list into the database
            values[ResponsesTable.REQ_HEADERS] = Compressed(values[ResponsesTable.REQ_HEADERS])
            values[ResponsesTable.RES_HEADERS] = Compressed(values[ResponsesTable.RES_HEADERS])
            values[ResponsesTable.REQ_DATA] = self.insert_content_data(cursor, values[ResponsesTable.REQ_DATA])
            values[ResponsesTable.RES_DATA] = self.insert_content_data(cursor, values[ResponsesTable.RES_DATA])
            rowid = 0
            cursor.execute("INSERT INTO responses(Id, Url, ReqHeaders, ReqDataHashval, \
                                    ResHeaders, ResContentHashval, Status, Length, ReqTime, ReqDate, \
                                    Notes, Results, Confirmed, \
                                    ReqMethod, HostIP, ResContentType, DataOrigin, ReqHost) \
                                    values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
            cursor.execute('SELECT last_insert_rowid()')
            results = cursor.fetchone()
            if results:
                rowid = int(results[0])

            if AutoCommit:
                self.conn.commit()

            return rowid

        except Exception, error:
            print('FIX ME! ERROR: %s' % (traceback.format_exc(error)))
            for i in range(0, len(values)):
                if i not in [ResponsesTable.REQ_DATA, ResponsesTable.RES_DATA]:
                    print('[%d] %s' % (i, values[i]))

        finally:
            self.qlock.unlock()

    def get_all_requester_history(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, '' ReqHeaders, '' ReqData, '' ResHeaders, \
                               '' ResContent, Status, Length, ReqTime, ReqDate, '' Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, requester_history \
                               WHERE \
                               Id = Response_Id")
            return(cursor)
        finally:
            self.qlock.unlock()

    def insert_requester_history(self, cursor, response_id, AutoCommit = True):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO requester_history (Response_Id) VALUES (?)", [response_id])
            if AutoCommit:
                self.conn.commit()
        finally:
            self.qlock.unlock()

    def clear_requester_history(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("DELETE from requester_history")
            self.conn.commit()
        finally:
            self.qlock.unlock()
        
    def get_all_fuzzer_history(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Id, Url, '' ReqHeaders, '' ReqData, '' ResHeaders, \
                               '' ResContent, Status, Length, ReqTime, ReqDate, '' Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, fuzzer_history \
                               WHERE \
                               Id = Response_Id")
            return(cursor)
        finally:
            self.qlock.unlock()

    def insert_fuzzer_history(self, cursor, response_id, AutoCommit = True):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO fuzzer_history (Response_Id) VALUES (?)", [response_id])
            if AutoCommit:
                self.conn.commit()
        finally:
            self.qlock.unlock()

    def clear_fuzzer_history(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("DELETE from fuzzer_history")
            self.conn.commit()
        finally:
            self.qlock.unlock()

    def read_all_config_values(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT Component, ConfigName, ConfigValue FROM configuration")
            return cursor
        finally:
            self.qlock.unlock()
        
    def get_config_value(self, cursor, component, name, rtype = str, default_value = None):
        self.qlock.lock()
        try:
            cursor.execute("SELECT ConfigValue FROM configuration WHERE Component=? AND ConfigName=?", [component, name])
            row = cursor.fetchone()
            if row is None:
                if default_value is not None:
                    return default_value
                else:
                    value = ''
            else:
                value = str(row[0])
            if rtype == bool:
                if not value:
                    return False
                return value.lower() in ['true', 'yes', 'y', '1']
            elif rtype == int:
                try:
                    return int(value)
                except ValueError:
                    return 0
            else:
                # TODO: implement more types
                return value
        finally:
            self.qlock.unlock()

    def update_config_value(self, cursor, component, name, value, is_locked = False):
        if not is_locked:
            self.qlock.lock()
        try:
            cursor.execute("UPDATE configuration SET ConfigValue=? WHERE Component=? AND ConfigName=?", [Compressed(str(value)), component, name])
            self.commit()
        finally:
            if not is_locked:
                self.qlock.unlock()
            
    def set_config_value(self, cursor, component, name, value):
        self.qlock.lock()
        try:
            cursor.execute("SELECT count(1) FROM configuration WHERE Component=? AND ConfigName=?", [component, name])
            count = int(cursor.fetchone()[0])
            if 0 == count:
                # TODO: gross
                cursor.execute("INSERT INTO configuration (Component, ConfigName, ConfigValue) VALUES (?, ?, ?)", [component, name, Compressed(str(value))])
                self.commit()
            else:
                self.update_config_value(cursor, component, name, value, True)
        finally:
            self.qlock.unlock()

    def clear_config_value(self, cursor, component, name=None):
        if name is None:
            cursor.execute("""DELETE FROM configuration 
                                WHERE Component=?
                            """,[component])
        else:
            cursor.execute("""DELETE FROM configuration 
                                WHERE Component=? AND ConfigName=?
                            """, [component,name])
        
    def add_differ_item(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO differ_items (response_id, time_added) values (?, ?)", [Id, time.time()])
            self.commit()
            return True
        except sqlite.IntegrityError:
            return False
        finally:
            self.qlock.unlock()

    def clear_differ_items(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("DELETE FROM differ_items")
            self.commit()
        finally:
            self.qlock.unlock()


    def get_differ_ids(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("SELECT r.Id, r.Url FROM responses r, differ_items d WHERE r.id=d.response_id ORDER BY time_added")
            return cursor
        finally:
            self.qlock.unlock()

    def analysis_start(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO AnalysisRuns (timeran) values (?)", [datetime.datetime.now()])

            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            #self.conn.commit()
            return rowid
        finally:
            self.qlock.unlock()
    
    def analysis_add_analyzer_instance(self, cursor, analysisrunid, classname, friendlyname, desc, resultclass):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO AnalysisInstances (AnalysisRun, friendlyName, desc, className, resultclass) values (?,?,?,?,?)", 
                                [analysisrunid, friendlyname, desc, classname, resultclass])
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            #self.conn.commit()
            return rowid
        finally:
            self.qlock.unlock()
    
    def analysis_add_resultset(self, cursor, analyzerinstanceid,responseid,isOverallResult,context, resultclass):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO AnalysisResultSet (AnalysisInstance, Response_analyzed, isOverallResult, context, resultclass) values (?,?,?,?,?)", 
                                [analyzerinstanceid, responseid, isOverallResult, context,resultclass])
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            #self.conn.commit()
            return rowid
        finally:
            self.qlock.unlock()
    
    def analysis_add_singleresult(self, cursor, resultsetid,severity,certainty,type,desc,data,span,resultclass):
        self.qlock.lock()
        try:
            if span is None:
                span=(None,None)
            cursor.execute("INSERT INTO AnalysisSingleResult (AnalysisResultSet,severity,certainty,type,"\
                                "desc,data,spanstart,spanend,resultclass) values (?,?,?,?,?,?,?,?,?)", 
                                [resultsetid,severity,certainty,type,desc,data,span[0],span[1],resultclass])
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            #self.conn.commit()
            return rowid
        finally:
            self.qlock.unlock()
    
    def analysis_add_stat(self, cursor, resultsetid, statname, statvalue):
        self.qlock.lock()
        try:
            cursor.execute("INSERT INTO AnalysisStats (AnalysisResultSet, statName, statValue) values (?,?,?)", 
                                [resultsetid, statname, statvalue])
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            #self.conn.commit()
            return rowid
        finally:
            self.qlock.unlock()

    def analysis_get_runs(self, cursor,lastx=None):
        self.qlock.lock()
        try:
            mainquery="""SELECT AnalysisRun_ID,timeran, 
                            (SELECT COUNT(*) 
                            FROM AnalysisInstances AS ai
                            INNER JOIN AnalysisResultSet ON AnalysisInstance=AnalysisInstance_ID
                            INNER JOIN AnalysisSingleResult ON AnalysisResultSet=AnalysisResultSet_ID
                            WHERE ai.AnalysisRun=AnalysisRun_ID) as numresults
                            FROM AnalysisRuns
                            ORDER BY AnalysisRun_ID
                            """
            if lastx is None:
                cursor.execute(mainquery)
            else:
                query="".join((mainquery," DESC LIMIT ?"))
                cursor.execute(query,[lastx,])

            return cursor.fetchall()
        finally:
            self.qlock.unlock()
    
    
    def analysis_get_instances_per_run(self, cursor, runid):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT AnalysisInstance_ID, friendlyName, desc, className, resultclass,
                                (SELECT COUNT(*) 
                                    FROM  AnalysisResultSet AS ars
                                    INNER JOIN AnalysisSingleResult ON AnalysisResultSet=AnalysisResultSet_ID
                                    WHERE ars.AnalysisInstance=AnalysisInstance_ID) as numresults
                                FROM AnalysisInstances 
                                WHERE AnalysisRun=?""", 
                                [runid])
            return cursor.fetchall()
        finally:
            self.qlock.unlock()
    
    def analysis_get_resultsets_per_instance(self, cursor, instanceid):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT AnalysisResultSet_ID, Response_analyzed, isOverallResult, context, resultclass,
                                    (SELECT COUNT(*) 
                                    FROM  AnalysisSingleResult AS asr
                                    WHERE asr.AnalysisResultSet=AnalysisResultSet_ID) as numresults 
                                FROM AnalysisResultSet 
                                WHERE AnalysisInstance=?""", 
                                [instanceid])
            return cursor.fetchall()
        finally:
            self.qlock.unlock()
    
    def analysis_get_singleresults_per_resultset(self, cursor, resultsetid):
        self.qlock.lock()
        try:
            cursor.execute("SELECT AnalysisSingleResult_ID, severity, certainty, type, desc,data, spanstart,spanend, resultclass FROM AnalysisSingleResult WHERE AnalysisResultSet=?", 
                                [resultsetid])
            return cursor.fetchall()
        finally:
            self.qlock.unlock()
    
    def analysis_get_stats_per_resultset(self,cursor, resultsetid):
        self.qlock.lock()
        try:
            cursor.execute("SELECT AnalysisStat_ID, statName, statValue FROM AnalysisStats WHERE AnalysisResultSet=?", 
                                [resultsetid])
            return cursor.fetchall()
        finally:
            self.qlock.unlock()
    
    def analysis_clear_configuration(self, cursor, name=None):
        cursor.execute("""DELETE FROM configuration 
                            WHERE Component='ANALYSIS'
                        """)
        cursor.execute("""DELETE FROM configuration 
                            WHERE Component='ANALYSISENABLED'
                        """)

    def get_dom_fuzzer_queue_items(self, cursor, status_filter = None):
        self.qlock.lock()
        try:
            base_query = """SELECT 
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Status
                              FROM dom_fuzzer_queue"""
            order_by = " ORDER BY Id"
            if status_filter:
                cursor.execute(base_query + " WHERE Status = ? " + order_by, [status_filter])
            else:
                cursor.execute(base_query + order_by)

            return cursor
        finally:
            self.qlock.unlock()

    def get_dom_fuzzer_queue_item_by_id(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT 
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Status
                              FROM dom_fuzzer_queue
                              WHERE Id = ?""", [Id])
            return cursor.fetchone()
        finally:
            self.qlock.unlock()

    def add_dom_fuzzer_queue_item(self, cursor, insertlist):
        self.qlock.lock()
        try:
            cursor.execute("""INSERT INTO dom_fuzzer_queue (
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Status
                              ) VALUES (
                              ?, ?, ?, ?, ?, ?, ?
                              )""", insertlist)
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            self.commit()
            return rowid
        finally:
            self.qlock.unlock()

    def update_dom_fuzzer_queue_item_status(self, cursor, Id, status):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE dom_fuzzer_queue SET status=? where Id=?""", [status, Id])
            self.commit()
        finally:
            self.qlock.unlock()

    def clear_dom_fuzzer_queue(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE dom_fuzzer_queue SET status='D' where Status='P'""")
            self.commit()
        finally:
            self.qlock.unlock()

    def add_dom_fuzzer_results_item(self, cursor, insertlist):
        self.qlock.lock()
        try:
            insertlist[DomFuzzerResultsTable.RENDERED_DATA] = Compressed(insertlist[DomFuzzerResultsTable.RENDERED_DATA])
            cursor.execute("""INSERT INTO dom_fuzzer_results (
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Confidence,
                              Rendered_Data
                              ) VALUES (
                              ?, ?, ?, ?, ?, ?, ?, ?
                              )""", insertlist)
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            self.commit()
            return rowid
        finally:
            self.qlock.unlock()

    def read_dom_fuzzer_results_info(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT 
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Confidence,
                              '' Rendered_Data
                              FROM dom_fuzzer_results ORDER BY Id""")
            return cursor
        finally:
            self.qlock.unlock()

    def read_dom_fuzzer_results_by_id(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT 
                              Id, 
                              Response_Id,
                              Url, 
                              Target,
                              Param,
                              Test,
                              Confidence,
                              Rendered_Data
                              FROM dom_fuzzer_results WHERE Id = ?""", [Id])
            return cursor.fetchone()
        finally:
            self.qlock.unlock()

    def read_spider_pending_responses(self, cursor, status_filter = None):
        self.qlock.lock()
        try:
            if status_filter:
                cursor.execute("""SELECT Response_Id, Request_Type, Depth, Status from spider_pending_responses WHERE Status=?""", [status_filter])
            else:
                cursor.execute("""SELECT Response_Id, Request_Type, Depth, Status from spider_pending_responses""")
            return cursor
        finally:
            self.qlock.unlock()

    def spider_pending_response_exists(self, cursor, Id, Request_Type):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT count(1) from spider_pending_responses WHERE Response_Id=? and Request_Type=?""", [Id, Request_Type])
            row = cursor.fetchone()
            if row:
                rcount = int(row[0])
                if 0 != rcount:
                    return True
            return False
        finally:
            self.qlock.unlock()

    def add_spider_pending_response_id(self, cursor, insertlist):
        self.qlock.lock()
        try:
            cursor.execute("""INSERT INTO spider_pending_responses (Response_Id, Request_Type, Depth, Status) VALUES (?,?,?,?)""", insertlist)
            self.commit()
            return True
        except sqlite.IntegrityError:
            # okay if duplicates
            return False
        finally:
            self.qlock.unlock()

    def update_spider_pending_response_id(self, cursor, Status, Id, Request_Type):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE spider_pending_responses SET Status = ? WHERE Response_Id=? and Request_Type=?""", [Status, Id, Request_Type])
            self.commit()
        finally:
            self.qlock.unlock()

    def clear_spider_pending_responses(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE spider_pending_responses SET Status='D' where Status='P'""")
            self.commit()
        finally:
            self.qlock.unlock()

    def reset_spider_pending_responses(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""DELETE FROM spider_pending_responses""")
            self.commit()
        finally:
            self.qlock.unlock()

    def clear_spider_queue(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE spider_queue SET status='D' where Status='P'""")
            self.commit()
        finally:
            self.qlock.unlock()

    def reset_spider_queue(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""DELETE from spider_queue""")
            self.commit()
        finally:
            self.qlock.unlock()

    def read_spider_pending_analysis(self, cursor):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT Id, Analysis_Type, Content, Url, Depth FROM spider_pending_analysis""")
            return cursor
        finally:
            self.qlock.unlock()

    def delete_spider_pending_analysis(self, cursor, Id):
        self.qlock.lock()
        try:
            cursor.execute("""DELETE FROM spider_pending_analysis WHERE Id=?""", [Id])
            self.commit()
        finally:
            self.qlock.unlock()

    def add_spider_pending_analysis(self, cursor, insertlist, AutoCommit = True):
        self.qlock.lock()
        try:
            duplist = insertlist[:]
            duplist[SpiderPendingAnalysisTable.CONTENT] = Compressed(str(duplist[SpiderPendingAnalysisTable.CONTENT]))
            cursor.execute("""INSERT INTO spider_pending_analysis (Id, Analysis_Type, Content, Url, Depth) VALUES (?,?,?,?,?)""", duplist)

            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            self.commit()
            return rowid

        except:
            print(insertlist)
            raise
        finally:
            self.qlock.unlock()

    def add_spider_queue_item(self, cursor, insertlist):
        self.qlock.lock()
        try:
            cursor.execute("""INSERT INTO spider_queue (
                              Id, 
                              Method, 
                              Url, 
                              Query_Params,
                              Encoding_Type,
                              Form_Params,
                              Referer,
                              Status,
                              Depth
                              ) VALUES (
                              ?, ?, ?, ?, ?, ?, ?, ?, ?
                              )""", insertlist)
            cursor.execute("SELECT last_insert_rowid()")
            rowid = int(cursor.fetchone()[0])
            self.commit()
            return rowid
        finally:
            self.qlock.unlock()

    def get_spider_queue_items(self, cursor, status_filter = None):
        self.qlock.lock()
        try:
            base_query = """SELECT 
                              Id, 
                              Method, 
                              Url, 
                              Query_Params,
                              Encoding_Type,
                              Form_Params,
                              Referer,
                              Status,
                              Depth
                              FROM spider_queue"""
            order_by = " ORDER BY Id"
            if status_filter:
                cursor.execute(base_query + " WHERE Status = ? " + order_by, [status_filter])
            else:
                cursor.execute(base_query + order_by)

            return cursor
        finally:
            self.qlock.unlock()

    def read_spider_queue_by_url(self, cursor, Url):
        self.qlock.lock()
        try:
            cursor.execute("""SELECT 
                              Id, 
                              Method, 
                              Url, 
                              Query_Params,
                              Encoding_Type,
                              Form_Params,
                              Referer,
                              Status,
                              Depth
                              FROM spider_queue
                              WHERE Url = ?""", [Url])
            return cursor
        finally:
            self.qlock.unlock()

    def update_spider_queue_item_status(self, cursor, Id, status):
        self.qlock.lock()
        try:
            cursor.execute("""UPDATE spider_queue SET status=? where Id=?""", [status, Id])
            self.commit()
        finally:
            self.qlock.unlock()

    def get_db_uuid(self, in_cursor = None):
        if in_cursor is None:
            cursor = self.allocate_thread_cursor()
        else:
            cursor = in_cursor
        self.qlock.lock()
        try:
            cursor.execute("""SELECT Value FROM raft where Name='UUID'""")
            ret = cursor.fetchone()
            if ret:
                ret = str(ret[0])
            return ret
        finally:
            self.qlock.unlock()
            if in_cursor is None:
                self.release_thread_cursor(cursor)
            
    def allocate_thread_cursor(self):
        self.threadMutex.lock()
        try:
            cur = self.conn.cursor()
            self.threadCursors.append(cur)
            return cur
        finally:
            self.threadMutex.unlock()

    def release_thread_cursor(self, cursor):
        self.threadMutex.lock()
        try:
            index = self.threadCursors.index(cursor)
            self.threadCursors.pop(index)
        finally:
            self.threadMutex.unlock()

    def execute_search(self, cursor, includeBody):
        self.qlock.lock()
        try:
            if not includeBody:
                cursor.execute("SELECT Id, Url, ReqHeaders, '' ReqData, ResHeaders, \
                               '' ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses")
            else:
                cursor.execute("SELECT Id, Url, ReqHeaders, cd1.Data ReqData, ResHeaders, \
                               cd2.Data ResContent, Status, Length, ReqTime, ReqDate, Notes, \
                               Results, Confirmed, \
                               ReqMethod, HostIP, ResContentType, DataOrigin, ReqDataHashval, ResContentHashval, ReqHost \
                               FROM responses, content_data cd1, content_data cd2 \
                               WHERE \
                               cd1.Hashval = ReqDataHashval and cd2.Hashval = ResContentHashval")
            return cursor.fetchall()
        finally:
            self.qlock.unlock()

    def upgrade_to_2011_8_31_alpha(self, cursor):

        version = '2011.8.31-alpha'

        cursor.execute("""INSERT INTO raft (Name, Value) values (?, ?)""", ['UUID', uuid.uuid4().hex])
        
        cursor.execute("UPDATE raft SET Value=? WHERE Name=?", [version, 'VERSION'])
        self.conn.commit()

        return version

    def upgrade_to_2011_9_1_alpha(self, cursor):

        version = '2011.9.1-alpha'

        cursor.execute("""SELECT Component, ConfigName, ConfigValue from configuration where Component in ('ANALYSIS', 'ANALYSISENABLED')""")
        rows = cursor.fetchall()
        for row in rows:
            component = str(row[0])
            old_name = str(row[1])
            old_value = row[2]
            new_name = old_name.replace('analayis.analyzers.', 'analyzers.')
            if new_name != old_name:
                cursor.execute("""INSERT INTO configuration (Component, ConfigName, ConfigValue) values (?, ?, ?)""", [component, new_name, old_value])
                cursor.execute("""DELETE FROM configuration WHERE Component=? and ConfigName=?""", [component, old_name])
        
        cursor.execute("UPDATE raft SET Value=? WHERE Name=?", [version, 'VERSION'])
        self.conn.commit()

        return version
