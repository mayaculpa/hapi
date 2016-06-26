# -*- coding: utf-8 -*-

import sqlite3
import sys
import operator
import time
import datetime
import urllib2
import json



def get_weather():
    response = ""
    f = urllib2.urlopen('http://api.wunderground.com/api/ffb22aac10a07be6/geolookup/conditions/q/TN/Nashville.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    #location = parsed_json['location']['city']
    #temp_f = parsed_json['current_observation']['temp_f']
    #temp_c = parsed_json['current_observation']['temp_c']
    #rel_hmd = parsed_json['current_observation']['relative_humidity']
    #pressure = parsed_json['current_observation']['pressure_mb']
    #print "Current weather in %s" % (location)
    #print "    Temperature is: %sF, %sC" % (temp_f, temp_c)
    #print "    Relative Humidity is: %s" % (rel_hmd)
    #print "    Atmospheric Pressure is: %smb" % (pressure)
    response = parsed_json['current_observation']
    f.close()
    return response

def get_raw_log():
    rtu_list = []
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()
        db_elements = c.execute("SELECT  FROM rtus WHERE online = 1;")
        for unit in db_elements:
            rtu = RemoteTerminalUnit()
            rtu.rtuid = unit[0]
            rtu.protocol = unit[1]
            rtu.address = unit[2]
            rtu.version = unit[3]
            rtu.online = unit[4]
            rtu_list.append(rtu)
            get_pin_modes(rtu)
        conn.close()
    except Exception, excpt:
        print "Error loading rtu table. %s", excpt

    return rtu_list