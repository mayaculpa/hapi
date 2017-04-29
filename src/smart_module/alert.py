#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Smart Module v2.1.2
Authors: Tyler Reed, Pedro Freitas
Release: April 2017 Beta Milestone

Copyright 2016 Maya Culpa, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
import sys
import datetime
import logging
import sqlite3

VERSION = "3.0 Alpha"
SM_LOGGER = "smart_module"

def trim(docstring):
    """Trim docstring."""
    # Not sure...
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

class DatabaseConn(object):
    """Hold necessary information to connect and perform operations on SQLite3 database."""
    def __init__(self, connect=False, dbfile="hapi_core.db"):
        """Create object to hold and connect to SQLite3."""
        self.dbfile = dbfile
        self.connection = None
        self.cursor = None
        self.log = logging.getLogger(SM_LOGGER)
        if connect:
            self.connect()

    def connect(self):
        """Connect to the SQLite3 database and initialize cursor."""
        try:
            self.connection = sqlite3.connect(self.dbfile)
            self.cursor = self.connection.cursor()
        except Exception, excpt:
            self.log.exception("Error connection to database: %s", excpt)

    def __del__(self):
        """Close SQLite3 database connection."""
        try:
            self.connection.close()
            self.log.info("Database connection closed.")
        except Exception, excpt:
            self.log.exception("Error trying to close db connection: %s", excpt)

class Alert(object):
    def __init__(self, asset_id):
        self.id = asset_id
        self.lower_threshold = 0.0
        self.upper_threshold = 0.0
        self.current = 0.0
        self.message = ""
        self.response_type = ""
        self.log = logging.getLogger(SM_LOGGER)

    def __str__(self):
        return str([{"id": self.id,
                     "lower": self.lower_threshold,
                     "upper": self.upper_threshold,
                     "current": self.current,
                     "message": self.message,
                     "response": self.response_type
                    }])

    def check_alert(self, value, sm_name):
        """Check current value with threshold and send alert if necessary."""
        self.current = value
        self.get_alert_params()
        self.log.info("Checking asset for alert conditions: %s :: %s", self.id, str(self.current))
        print('Lower Threshold is', self.lower_threshold)
        print('Upper Threshold is', self.upper_threshold)
        if not self.lower_threshold < value < self.upper_threshold:
            self.log.info("Alert condition detected: %s :: %s", self.id, str(self.current))
            self.log_alert_condition()
            self.send_alert_condition(sm_name)

    def log_alert_condition(self):
        """Update database alert log."""
        now = str(datetime.datetime.now())
        command = '''
            INSERT INTO alert_log (asset_id, value, timestamp)
            VALUES (?, ?, ?)
        ''', (str(self.id), str(self.current), now)
        db = DatabaseConn(connect=True, dbfile="hapi_history.db")
        db.cursor.execute(*command)
        db.connection.commit()

    def send_alert_condition(self, sm_name):
        """Send alert according to 'self.response_type'."""
        message = '''
            Alert from {name}: {id}
            {message}
            Value: {value}
            Timestamp: "{now}"
        '''.format(
            name=str(sm_name),
            id=self.id,
            message=self.message,
            value=self.current,
            now=datetime.datetime.now(),
        )
        if self.response_type.lower() == "sms":
            # message = trim(message) + '\n'
            # message = message.replace('\n', '\r\n')  #??? ugly! necessary? write place?
            # if (self.twilio_acct_sid is not "") and (self.twilio_auth_token is not ""):
            # client = TwilioRestClient(self.twilio_acct_sid, self.twilio_auth_token)
            # client.messages.create(to="+receiving number", from_="+sending number",
            #                        body=message)
            print("sms sent (testing): ", trim(message))
            pass

        if self.response_type.lower() == "email":
            print("email sent (testing): ", trim(message))
            pass

        self.log.info("Alert condition sent.")

    def get_alert_params(self):
        """Update the object to hold its alert information."""
        self.log.info("Fetching alert parameters.")
        field_names = '''
            asset_id
            lower_threshold
            upper_threshold
            message
            response_type
        '''.split()
        # Isn't this confusing? Using the field name for a variable called field_names?
        sql = 'SELECT {field_names} FROM alert_params WHERE asset_id={asset};'.format(
            field_names=', '.join(field_names), asset=self.id)
        database = DatabaseConn(connect=True)
        row = database.cursor.execute(sql)
        row = database.cursor.fetchone()
        self.id, self.lower_threshold, self.upper_threshold, self.message, self.response_type = row
        #print(database.cursor.fetchone())
        # for field_name, field_value in zip(field_names, row):
        #     print(field_name, field_value)
        #     setattr(self, field_name, field_value)
        self.lower_threshold = float(self.lower_threshold)
        self.upper_threshold = float(self.upper_threshold)

if __name__ == "__main__":
    alert = Alert(1)
    alert.check_alert(20, "testing")
    print(alert)
