# -*- coding: utf-8 -*-
#!/usr/bin/python

# HAPI Master Controller v1.0
# Author: Tyler Reed
# Release: June 24th, 2016
#*********************************************************************
#Copyright 2016 Maya Culpa, LLC
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#*********************************************************************

import sqlite3
import telnetlib
import sys
import operator
import time
import schedule
import datetime
import urllib2
import json

# wunderground key ffb22aac10a07be6

rtus = []
reload(sys)
sys.setdefaultencoding('UTF-8')

def get_weather():
    response = ""
    f = urllib2.urlopen('http://api.wunderground.com/api/ffb22aac10a07be6/geolookup/conditions/q/OH/Columbus.json')
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

def get_image():
    response = ""
    f = urllib2.urlopen('http://api.wunderground.com/api/ffb22aac10a07be6/geolookup/conditions/q/OH/Columbus.json')
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

class RemoteTerminalUnit(object):
    def __init__(self):
        self.rtuid = ""
        self.protocol = ""
        self.address = ""
        self.version = ""
        self.online = 0
        self.pin_modes = {}

class IntervalJob(object):

    def __init__(self):
        self.job_id = -1
        self.job_name = ""
        self.rtuid = ""
        self.command = ""
        self.time_unit = ""
        self.interval = -1
        self.at_time = ""
        self.enabled = 0

class PinMode(object):
    def __init__(self):
        self.pin = ""
        self.mode = 0
        self.default_value = 0
        self.pos = 0

class Asset(object):
    def __init__(self):
        self.asset_id = -1
        self.rtuid = ""
        self.abbreviation = ""
        self.name = ""
        self.pin = ""
        self.unit = ""

def push_log_data(sensor_name):
    log = RawLog()
    log.read_raw_log()
    for entry in log.log_entries:
        data = json.loads(entry.data)
        print data.rtuid, data.timestamp, sensor_name, data[sensor_name]


def get_rtu_list():
    rtu_list = []
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()
        db_elements = c.execute("SELECT rtuid, protocol, address, version, online FROM rtus WHERE online = 1;")
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

def get_pin_modes(rtu):
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()

        sql = "SELECT p.pin, p.mode, p.def_value, p.pos FROM pins p WHERE p.rtuid = \'" + rtu.rtuid + "\' ORDER BY p.pos;"
        db_elements = c.execute(sql)
        for unit in db_elements:
            pin_mode = PinMode()
            pin_mode.pin = unit[0]
            pin_mode.mode = unit[1]
            pin_mode.default_value = unit[2]
            pin_mode.pos = unit[3]
            rtu.pin_modes.update({pin_mode.pin : pin_mode})
        conn.close()
    except Exception, excpt:
        print "Error loading pin mode table. %s", excpt

    return

def get_assets():
    assets = []
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()
        sql = "SELECT asset_id, rtuid, abbreviation, name, pin, unit FROM assets;"
        rows = c.execute(sql)
        for field in rows:
            asset = Asset()
            asset.asset_id = field[0]
            asset.rtuid = field[1]
            asset.abbreviation = field[2]
            asset.name = field[3]
            asset.pin = field[4]
            asset.unit = field[5]
            assets.append(asset)
        conn.close()
    except Exception, excpt:
        print "Error loading asset table. %s", excpt

    return assets

def validate_environment(rtus):
    print "Validating environment..."
    problem_rtus = []
    for rtu in rtus:
        if rtu.online == 1:
            try:
                print "Connecting to", rtu.rtuid, "at", rtu.address
                tn = telnetlib.Telnet()
                tn.open(rtu.address, 80, 5)
                print "Connected."
                tn.write("sta\n")
                response = tn.read_all()
                print response

                tn.close()
            except Exception, excpt:
                print "Error communicating with rtu", rtu.rtuid, excpt
                problem_rtus.append(rtu)

    # Check pin mode settings
    for rtu in rtus:
        if rtu not in problem_rtus:
            print "Getting pin modes from", rtu.rtuid
            tn = telnetlib.Telnet()
            tn.open(rtu.address, 80, 5)
            tn.write("gpm\n")
            pmode_from_rtu = tn.read_all()
            tn.close()
            #print "Pin mode from rtu:", pmode_from_rtu

            pmode_from_db = ""
            for db_pin_mode in sorted(rtu.pin_modes.values(), key=operator.attrgetter('pos')):
                pmode_from_db += db_pin_mode.pin
                pmode_from_db += str(db_pin_mode.mode)

            #print "Pin mode from ref:", pmode_from_db

            pin_mode_ok = True
            for i in range(0, len(pmode_from_rtu) - 2):
                if pmode_from_rtu[i] != pmode_from_db[i]:
                    pin_mode_ok = False
                    #print "Pin mode mismatch (rtu:db:pos)", pmode_from_rtu[i], ":", pmode_from_db[i], ":", i/2
                #print pmode_from_rtu[i], pmode_from_db[i]
            if pin_mode_ok == False:
                print "RTU", rtu.rtuid, "has a non-congruent pin mode."
                problem_rtus.append(rtu)
            else:
                print "Pin mode congruence verified between", rtu.rtuid, "and the database."

    return problem_rtus

def load_interval_schedule():
    job_list = []
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()

        db_jobs = c.execute("SELECT job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled FROM interval_schedule;")
        for row in db_jobs:
            job = IntervalJob()
            job.job_id = row[0]
            job.job_name = row[1]
            job.rtuid = row[2]
            job.command = row[3].encode("ascii")
            job.time_unit = row[4]
            job.interval = row[5]
            job.at_time = row[6]
            job.enabled = row[7]
            job_list.append(job)

        conn.close()
    except Exception, excpt:
        print "Error loading interval_schedule. %s", excpt

    return job_list

def prepare_jobs(jobs):
    for job in jobs:
        if job.time_unit.lower() == "month":
            if job.interval > -1:
                schedule.every(job.interval).months.do(run_job, job)
                print "Found a monthly job:", job.job_name
        elif job.time_unit.lower() == "week":
            if job.interval > -1:
                schedule.every(job.interval).weeks.do(run_job, job)
                print "Found a weekly job:", job.job_name
        elif job.time_unit.lower() == "day":
            if job.interval > -1:
                schedule.every(job.interval).days.do(run_job, job)
                print "Found a daily job:", job.job_name
            else:
                schedule.every().day.at(job.at_time).do(run_job, job)
                print "Found a daily job:", job.job_name
        elif job.time_unit.lower() == "hour":
            if job.interval > -1:
                schedule.every(job.interval).hours.do(run_job, job)
                print "Found an hourly job:", job.job_name
        elif job.time_unit.lower() == "minute":
            if job.interval > -1:
                schedule.every(job.interval).minutes.do(run_job, job)
                print "Found a minute job:", job.job_name
            else:
                schedule.every().minute.do(run_job, job)
                print "Found a minute job:", job.job_name

def run_job(job):
    print 'Running', job.command, "on", job.rtuid
    command = ""
    response = ""
    job_rtu = None


    if job.rtuid.lower() == "virtual":
        response = eval(job.command)
        print response
        log_sensor_data(response, True)
    else:
        try:
            for rtu_el in rtus:
                if rtu_el.rtuid == job.rtuid:
                    if rtu_el.online == 1:
                        job_rtu = rtu_el

            if (job_rtu != None):
                tn = telnetlib.Telnet()
                tn.open(job_rtu.address, 80, 5)
                command = job.command
                tn.write(command)
                response = tn.read_all()
                tn.close()

                if (job.job_name == "Log Data"):
                    log_sensor_data(response, False)
                elif (job.job_name == "Log Status"):
                    pass
                else:
                    log_command(job)

        except Exception, excpt:
            print "Error running job", job.job_name, "on", job_rtu.rtuid, excpt

def log_command(job):

    timestamp = '"' + str(datetime.datetime.now()) + '"'
    command = "INSERT INTO command_log (rtuid, timestamp, command) VALUES (" + job.rtuid + ", " + timestamp + ", " + job.job_name + ")"
    print command
    conn = sqlite3.connect('hapi.db')
    c=conn.cursor()
    c.execute(command)
    conn.commit()
    conn.close()

def log_sensor_data(data, virtual):
    assets = get_assets()
    if virtual == False:
        for asset in assets:
            parsed_json = json.loads(data)
            if asset.rtuid == parsed_json['name']:
                value = parsed_json[asset.pin]
                timestamp = '"' + str(datetime.datetime.now()) + '"'
                unit = asset.unit
                command = "INSERT INTO sensor_data (asset_id, timestamp, value, unit) VALUES (" + str(asset.asset_id) + ", " + timestamp + ", " + value + ", " + unit + ")"
                print command
                conn = sqlite3.connect('hapi.db')
                c=conn.cursor()
                c.execute(command)
                conn.commit()
                conn.close()
    else:
        # For virtual assets, assume that the data is already parsed JSON
        for asset in assets:
            if asset.rtuid == "virtual":
                if asset.abbreviation == "weather":
                    value = data[asset.pin]
                    timestamp = '"' + str(datetime.datetime.now()) + '"'
                    command = "INSERT INTO sensor_data (asset_id, timestamp, value) VALUES (" + str(asset.asset_id) + ", " + timestamp + ", " + str(value) + ")"
                    print command
                    conn = sqlite3.connect('hapi.db')
                    c=conn.cursor()
                    c.execute(command)
                    conn.commit()
                    conn.close()


    #location = parsed_json['location']['city']
    #temp_f = parsed_json['current_observation']['temp_f']
    #temp_c = parsed_json['current_observation']['temp_c']
    #rel_hmd = parsed_json['current_observation']['relative_humidity']
    #pressure = parsed_json['current_observation']['pressure_mb']
    #print "Current weather in %s" % (location)
    #print "    Temperature is: %sF, %sC" % (temp_f, temp_c)
    #print "    Relative Humidity is: %s" % (rel_hmd)
    #print "    Atmospheric Pressure is: %smb" % (pressure)
    #response = parsed_json['current_observation']



def main(argv):
    global rtus
    #push_log_data('trm')
    rtus = get_rtu_list()
    problem_rtus = validate_environment(rtus)
    for rtu in problem_rtus:
        print "RTU", rtu.rtuid, "could not be found or has incongruent pin modes."

    if len(rtus) == 0:
        print "There are no RTUs online."
    elif len(rtus) == 1:
        print "There is 1 RTU online."
    else:
        print "There are", len(rtus), "online."
    jobs = load_interval_schedule()
    prepare_jobs(jobs)

    #print len(jobs)
    while 1:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main(sys.argv[1:])
