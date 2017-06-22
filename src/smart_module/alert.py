#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Smart Module v2.1.2
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
import sqlite3
import log
from utilities import DB_CORE

class Alert(object):
    """Hold Alert information fetched from database and check for alerts."""

    def __init__(self, asset_id=""):
        """Create object with null values."""
        self.alert_id = asset_id
        self.lower_threshold = 0.0
        self.upper_threshold = 0.0
        self.message = ""
        self.response_type = ""
        self.value_current = 0.0
        self.logger = log.Log("alert.log")

    def __str__(self):
        """Use to pass Alert information in JSON."""
        return str({"id": self.alert_id,
                    "lower": self.lower_threshold,
                    "upper": self.upper_threshold,
                    "message": self.message,
                    "response": self.response_type,
                    "value_current": self.value_current})

    def update_alert(self, asset_id):
        """Fetch alert parameters from database."""
        self.alert_id = asset_id
        try:
            self.logger.info("Fetching alert parameters from database.")
            field_names = '''
                lower_threshold
                upper_threshold
                message
                response_type
            '''.split()
            sql = "SELECT {fields} FROM alert_params WHERE asset_id = '{asset}' LIMIT 1;".format(
                fields=', '.join(field_names), asset=str(asset_id))
            database = sqlite3.connect(DB_CORE)
            row = database.cursor().execute(sql).fetchone()
            for key, value in zip(field_names, row):
                setattr(self, key, value)
            self.lower_threshold = float(self.lower_threshold)
            self.upper_threshold = float(self.upper_threshold)
        except Exception as excpt:
            self.logger.exception("Error fetching alert parameters from database: %s.", excpt)
        finally:
            database.close()
            self.logger.info("Closing Alert database connection.")

    def check_alert(self, current_value):
        """Check for alert to a given _value_."""
        self.value_current = current_value
        if self.lower_threshold <= float(current_value) <= self.upper_threshold:
            return False

        self.logger.info("[!] ALERT DETECTED. Value: %s.", current_value)
        return True
