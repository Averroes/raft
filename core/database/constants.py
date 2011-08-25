#
# This module contains constants for accessing the database
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

class ResponsesTable():
    """ This allows items to be read from, inserted, and updated to the RAFT database by ordinal.
    
    [0] Id - (Integer) - Unique ID for request
    [1] Url - (Text) - URL of request
    [2] ReqHeaders - (Text) - Request Headers
    [3] ReqData - (Blob) - Request Data
    [4] ResHeaders - (Text) - Response Headers
    [5] ResContent - (Blob) - Response Content
    [6] Status - (Integer) - HTTP Status code
    [7] Length - (Integer) - Content Length of response
    [8] ReqTime - (Integer) - Time the request took to complete
    [9] ReqDate - (Text) - date and time of request
    [10] Notes - (Text) - User supplied notes
    [11] Results - (Text) - Results of analysis run from the tool
    [12] Confirmed - (Boolean) - Confirmed vulnerability for the specific request
    [13] ReqMethod - (Text) - Request Method
    [14] HostIP - (Text) - Host IP
    [15] ResContentType - (Text) - Response Content Type
    [16] DataOrigin - (Text) Origin of response data
    [17] ReqDataHashval - (Varchar(64)) SHA256 hash of request data or empty
    [18] ResContentHashval - (Varchar(64)) SHA256 hash of result content or empty
    [19] ReqHost - (Text) - Request Host name
    """
       
    ID=0
    URL=1
    REQ_HEADERS=2
    REQ_DATA=3
    RES_HEADERS=4
    RES_DATA=5
    STATUS=6
    RES_LENGTH=7
    REQTIME=8
    REQDATE=9
    NOTES=10
    RESULTS=11
    CONFIRMED=12
    REQ_METHOD = 13
    HOST_IP = 14
    RES_CONTENT_TYPE = 15
    DATA_ORIGIN = 16
    REQ_DATA_HASHVAL = 17
    RES_DATA_HASHVAL = 18
    REQ_HOST = 19
    
class SequencesTable():
    ID=0
    NAME=1
    SEQUENCE_TYPE=2
    SESSION_DETECTION=3
    INCLUDE_MEDIA=4
    USE_BROWSER=5
    INSESSION_PATTERN=6
    INSESSION_RE=7
    OUTOFSESSION_PATTERN=8
    OUTOFSESSION_RE=9
    DYNAMIC_DATA=10

class SequenceStepsTable():
    SEQUENCE_ID = 0
    STEPNUM = 1
    RESPONSE_ID = 2
    IS_ENABLED = 3
    IS_HIDDEN = 4

class SequenceSourceParameters():
    SEQUENCE_ID = 0
    RESPONSE_ID = 1
    INPUT_LOCATION = 2
    INPUT_POSITION = 3
    INPUT_TYPE = 4
    INPUT_NAME = 5
    INPUT_VALUE = 6
    IS_DYNAMIC = 7

class SequenceTargetParameters():
    SEQUENCE_ID = 0
    RESPONSE_ID = 1
    INPUT_LOCATION = 2
    INPUT_POSITION = 3
    INPUT_NAME = 4
    INPUT_VALUE = 5
    IS_DYNAMIC = 6

class SequenceCookies():
    SEQUENCE_ID = 0
    COOKIE_DOMAIN = 1
    COOKIE_NAME = 2
    COOKIE_RAW_VALUE = 3
    IS_DYNAMIC = 4

class DomFuzzerQueueTable():
    ID =  0
    RESPONSE_ID = 1
    URL =  2
    TARGET = 3 
    PARAM = 4
    TEST = 5
    STATUS = 6

class DomFuzzerResultsTable():
    ID =  0
    RESPONSE_ID = 1
    URL =  2
    TARGET = 3 
    PARAM = 4
    TEST = 5
    CONFIDENCE = 6
    RENDERED_DATA = 7

class SpiderPendingResponsesTable():
    RESPONSE_ID = 0
    REQUEST_TYPE = 1
    DEPTH = 2
    STATUS = 3

class SpiderQueueTable():
    ID = 0
    METHOD = 1
    URL = 2
    QUERY_PARAMS = 3
    ENCODING_TYPE = 4
    FORM_PARAMS = 5
    REFERER = 6
    STATUS = 7
    DEPTH = 8

class SpiderPendingAnalysisTable():
    ID = 0
    ANALYSIS_TYPE = 1
    CONTENT = 2
    URL = 3
    DEPTH = 4

class SpiderInternalStateTable():
    STATE_CATEGORY = 0
    STATE_KEY = 1
    STATE_COUNT = 2
    STATE_VALUE = 3

class ConfigurationTable():
    COMPONENT = 0
    CONFIG_NAME = 1
    CONFIG_VALUE = 2

