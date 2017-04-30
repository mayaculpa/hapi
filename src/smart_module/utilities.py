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
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60

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
