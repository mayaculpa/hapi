#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Master Controller v1.0
Author: Tyler Reed
Release: June 2016 Alpha

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

import sqlite3
import json

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

connection = sqlite3.connect("hapi.db")
connection.row_factory = dict_factory

cursor = connection.cursor()

cursor.execute("select * from sensor_data")

# fetch all or one we'll go for all.

results = cursor.fetchall()

f = open('sensor_data.json', 'wb')
f.write(json.dumps(results))
f.close()

print results

connection.close()
