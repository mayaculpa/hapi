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
from utilities import *

class Alert(object):
    """Hold information about current alert status about a given asset."""
    def __init__(self, asset_id):
        self.id = asset_id
        self.lower_threshold = 0.0
        self.upper_threshold = 0.0
        self.current = 0.0
        self.message = ""
        self.response_type = ""
        self.log = logging.getLogger(SM_LOGGER)

    def __str__(self):
        """Use to pass Alert information in JSON."""
        return str([{"id": self.id,
                     "lower": self.lower_threshold,
                     "upper": self.upper_threshold,
                     "current": self.current,
                     "message": self.message,
                     "response": self.response_type
                    }])

    def check_alert(self, value):
        """Check current value with threshold and send alert if necessary."""
        self.current = float(value)
        self.get_alert_params()
        self.log.info("Checking asset for alert conditions: %s :: %s", self.id, value)
        print('Lower Threshold is', self.lower_threshold)
        print('Upper Threshold is', self.upper_threshold)
        if not self.lower_threshold <= self.current <= self.upper_threshold:
            self.log.info("Alert condition detected: %s :: %s", self.id, str(self.current))
            self.log_alert_condition()
            self.send_alert_condition()

    def log_alert_condition(self):
        """Update database alert log."""
        command = '''
            INSERT INTO alert_log (asset_id, value, timestamp)
            VALUES (?, ?, ?)
        ''', (int(self.id), self.current, str(datetime.datetime.now()))
        db = DatabaseConn(connect=True, dbfile="hapi_history.db")
        db.cursor.execute(*command)
        db.connection.commit()

    def send_alert_condition(self):
        """Send alert according to 'self.response_type'."""
        message = '''
            Alert from: {id}
            {message}
            Value: {value}
            Timestamp: "{now}"
        '''.format(
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

        if self.response_type.lower() == "email":
            print("email sent (testing): ", trim(message))

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
        sql = 'SELECT {fields} FROM alert_params WHERE asset_id={asset};'.format(
            fields=', '.join(field_names), asset=int(self.id))
        database = DatabaseConn(connect=True)
        row = database.cursor.execute(sql).fetchone()
        self.id, self.lower_threshold, self.upper_threshold, self.message, self.response_type = row
        self.lower_threshold = float(self.lower_threshold)
        self.upper_threshold = float(self.upper_threshold)
