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

# Attention: a lot of these comments should be deleted!

# BOBP system modules first, then third-libs and local modules
from __future__ import print_function
import sys
import datetime
import logging
import sqlite3

# We should consider a way to handle those variable. Loading them on each module doesn't seem
# like a good idea
# BOBP - constants with all CAPS
VERSION = "3.0 Alpha"
SM_LOGGER = "smart_module"
HAPI_DATABASE = "hapi_core.db"

# Not sure...
def trim(docstring):
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

class Alert(object):
    def __init__(self):
        self.id = -1
        self.lower_threshold = 0.0
        self.upper_threshold = 0.0
        self.message = ""
        self.response_type = ""

    # See if it's necessary to change the parameters
    # I believe we should receive a copy of Asset and the sm name
    def check_alert(self, asset_id, asset_value):
        #alert_params = self.get_alert_params()
        logging.getLogger(SM_LOGGER).info("Checking asset for alert conditions: %s :: %s",
                                          asset_id, asset_value)
        # Consider a better approach for the following code
        try:
            for ap in alert_params:
                if ap.asset_id == asset_id:
                    try:
                        # timestamp not in use? Why
                        # timestamp = datetime.datetime.now()
                        # asset is define in smart_module.py
                        # fix it
                        print(asset.name, 'is', asset.value)
                        print('Lower Threshold is', ap.lower_threshold)
                        print('Upper Threshold is', ap.upper_threshold)
                        if not ap.lower_threshold < asset_value < ap.upper_threshold:
                            logging.getLogger(SM_LOGGER).info("Alert condition detected: %s :: %s",
                                                              asset_id, asset_value)
                            # It's not possible to have an object of a class inside its class def
                            # fix it
                            alert = Alert()
                            alert.asset_id = asset_id
                            alert.value = asset_value
                            self.log_alert_condition(alert)
                            self.send_alert_condition(self, alert, ap)
                    except Exception, excpt:
                        logging.getLogger(SM_LOGGER).exception("Error getting asset data: %s",
                                                               excpt)
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).exception("Error getting asset data: %s", excpt)

    def log_alert_condition(self, alert):
        try:
            now = str(datetime.datetime.now())
            command = '''
                INSERT INTO alert_log (asset_id, value, timestamp)
                VALUES (?, ?, ?)
            ''', (str(alert.id), str(alert.value), now)
            conn = sqlite3.connect('hapi_history.db')
            c = conn.cursor()
            c.execute(*command)
            conn.commit()
            conn.close()
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).exception("Error logging alert condition: %s", excpt)

    # Not sure how we'll handle SMS alert notifications
    def send_alert_condition(self, alert, alert_param):
        try:
            if alert_param.response_type.lower() == "sms":
                # Attention it gets information from smart module class, such as name
                message = '''
                    Alert from {name}: {id}
                    {message}
                    Value: {value}
                    Timestamp: "{now}"
                '''.format(
                    name=self.name,
                    id=alert.asset_id,
                    message=alert_param.message,
                    value=alert.value,
                    now=datetime.datetime.now(),
                )
                message = trim(message) + '\n'
                message = message.replace('\n', '\r\n')  #??? ugly! necessary? write place?
                # if (self.twilio_acct_sid is not "") and (self.twilio_auth_token is not ""):
                # client = TwilioRestClient(self.twilio_acct_sid, self.twilio_auth_token)
                # client.messages.create(to="+receiving number", from_="+sending number",
                #                        body=message)
                logging.getLogger(SM_LOGGER).info("Alert condition sent.")
        except Exception, excpt:
            print('Error sending alert condition.', excpt)

    def get_alert_params(self):
        ''' Update the object to hold its alert information '''
        field_names = '''
            asset_id
            lower_threshold
            upper_threshold
            message
            response_type
        '''.split()
        try:
            conn = sqlite3.connect(HAPI_DATABASE)
            c = conn.cursor()
            # Isn't this confusing? Using the field name for a variable called field_names?
            sql = 'SELECT {field_names} FROM alert_params WHERE asset_id={asset};'.format(
                field_names=', '.join(field_names), asset=self.id)
            row = c.execute(sql)
            for field_name, field_value in zip(field_names, row):
                # Not sure if this will work
                setattr(self, field_name, field_value)
            self.lower_threshold = float(self.lower_threshold)
            self.upper_threshold = float(self.upper_threshold)
            conn.close()
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).exception("Error getting alert parameters: %s", excpt)
