#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Smart Module v2.1.2
Release: April 2017 Beta Milestone

First attempt of implement small log functionality.
-> Standard option has memory leak when running multithreaded systems.
--> This is a testing!

This module is really simple and small. It should be improved if sticking to it.

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
import datetime
from utilities import LOGGING_FILE

class Log(object):
    """Write logging information."""

    @staticmethod
    def build_string(self, log_type, information):
        """Build string with mask and return it."""
        mask = "{date} - {name} - {log_type} - {string}"
        string = mask.format(
            date=datetime.datetime.now(),
            name=LOGGING_FILE,
            log_type=log_type,
            string=str(information),
        )
        return str(string)

    @staticmethod
    def info(self, format_str, *values):
        """Append INFO in format % values to file."""
        string = self.build_string("INFO", format_str % values)
        with open(LOGGING_FILE, "a") as log:
            log.write(string + "\n")
        print(string)

    @staticmethod
    def exception(self, format_str, *values):
        """Append ERROR in format % values to file."""
        string = self.build_string("[!!] ERROR", format_str % values)
        with open(LOGGING_FILE, "a") as log:
            log.write(string + "\n")
        print(string)
