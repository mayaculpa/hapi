#!/bin/python

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
