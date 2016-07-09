# -*- coding: utf-8 -*-
#!/usr/bin/python

# HAPI Master Controller v1.0
# Author: Tyler Reed
# Release: June 2016 Alpha
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
import subprocess

rtus = []
reload(sys)
sys.setdefaultencoding('UTF-8')

def get_sensor_data():
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
     
    connection = sqlite3.connect("hapi.db")
    connection.row_factory = dict_factory
     
    cursor = connection.cursor()
     
    cursor.execute("select a.rtuid, a.name, s.timestamp, s.value, s.unit from assets a INNER JOIN sensor_data s on a.asset_id = s.asset_id ORDER by s.timestamp")
     
    # fetch all or one we'll go for all.
    results = cursor.fetchall()
    f = open("sensor_data.json", "wb")
    f.write(json.dumps(results))
    f.close()
     
    connection.close()

def get_weather():
    response = ""
    f = urllib2.urlopen('http://api.wunderground.com/api/' + site.wunder_key + '/geolookup/conditions/q/OH/Columbus.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    response = parsed_json['current_observation']
    f.close()
    return response

def get_image():
    command = "fswebcam -p YUYV -d /dev/video0 -r 1280x720 image.jpg"
    # ex: to store a image in to db
    # public void insertImg(int id , Bitmap img ) {   
    #     byte[] data = getBitmapAsByteArray(img); // this is a function
    #     insertStatement_logo.bindLong(1, id);       
    #     insertStatement_logo.bindBlob(2, data);
    #     insertStatement_logo.executeInsert();
    #     insertStatement_logo.clearBindings() ;
    # }

    #  public static byte[] getBitmapAsByteArray(Bitmap bitmap) {
    #     ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
    #     bitmap.compress(CompressFormat.PNG, 0, outputStream);       
    #     return outputStream.toByteArray();
    # }

    # to retrieve a image from db
    # public Bitmap getImage(int i){
    #     String qu = "select img  from table where feedid=" + i ;
    #     Cursor cur = db.rawQuery(qu, null);
    #     if (cur.moveToFirst()){
    #         byte[] imgByte = cur.getBlob(0);
    #         cur.close();
    #         return BitmapFactory.decodeByteArray(imgByte, 0, imgByte.length);
    #     }
    #     if (cur != null && !cur.isClosed()) {
    #         cur.close();
    #     }       
    #     return null ;
    # } 
    response = parsed_json['current_observation']
    f.close()
    return response

class Site(object):
    """docstring for Site"""
    def __init__(self):
        self.site_id = ""
        self.name = ""
        self.wunder_key = ""
        self.operator = ""
        self.email = ""
        self.phone = ""
        self.location = ""
        self.longitude = ""
        self.latitude = ""

def load_site_data():
    the_site = None
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()
        db_elements = c.execute("SELECT site_id, name, wunder_key, operator, email, phone, location, longitude, latitude FROM site LIMIT 1;")
        for field in db_elements:
            the_site = Site()
            the_site.site_id = field[0]
            the_site.name = field[1]
            the_site.wunder_key = field[2]
            the_site.operator = field[3]
            the_site.email = field[4]
            the_site.phone = field[5]
            the_site.location = field[6]
            the_site.longitude = field[7]
            the_site.latitude = field[8]
        conn.close()
    except Exception, excpt:
        print "Error loading Site table. %s", excpt
        return None
    return the_site

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

def scan_for_rtus():
    rtu_addresses = []
    try:
        print "Scanning local network for RTUs..."
        netscan = subprocess.check_output(["arp-scan", "--interface=eth1", "--localnet"])
        netscan = netscan.split('\n')
        for machine in netscan:
            if machine.find("de:ad:be:ef") > -1:
                els = machine.split("\t")
                ip_address = els[0]
                print "Found RTU at: ", ip_address
                rtu_addresses.append(ip_address)

    except Exception, excpt:
        print "Error scanning local network. %s", excpt

    return rtu_addresses

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

def discover_rtus():
    print "Discovering RTUs..."
    valid_ip_addresses = scan_for_rtus()
    online_rtus = []

    for ip_address in valid_ip_addresses:
        print "Connecting to RTU at", ip_address
        try:
            tn = telnetlib.Telnet()
            tn.open(ip_address, 80, 5)
            tn.write("sta\n")
            response = tn.read_all().split('\r\n')
            tn.close()
            print response[0], "found at", ip_address, "running", response[1]
            rtu = RemoteTerminalUnit()
            rtu.rtuid = response[0]
            rtu.address = ip_address
            rtu.version = response[1]
            rtu.online = True
            get_pin_modes(rtu)
            online_rtus.append(rtu)
        except Exception, excpt:
            print "Error communicating with rtu at", ip_address, excpt

    return online_rtus

def validate_pin_modes(online_rtus):
    print "Validating pin modes..."
    problem_rtus = []

    # Check pin mode settings
    for rtu in online_rtus:
        tn = telnetlib.Telnet()
        tn.open(rtu.address, 80, 5)
        tn.write("gpm\n")
        pmode_from_rtu = tn.read_all()
        tn.close()

        pmode_from_db = ""
        for db_pin_mode in sorted(rtu.pin_modes.values(), key=operator.attrgetter('pos')):
            pmode_from_db += db_pin_mode.pin
            pmode_from_db += str(db_pin_mode.mode)

        pin_mode_ok = True
        for i in range(0, len(pmode_from_rtu) - 2):
            if pmode_from_rtu[i] != pmode_from_db[i]:
                pin_mode_ok = False
        if pin_mode_ok == False:
            print "RTU", rtu.rtuid, "has an incongruent pin mode."
            print "RTU pins", pmode_from_rtu
            print "DB pins", pmode_from_db
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
                print "Loading monthly job:", job.job_name
        elif job.time_unit.lower() == "week":
            if job.interval > -1:
                schedule.every(job.interval).weeks.do(run_job, job)
                print "Loading weekly job:", job.job_name
        elif job.time_unit.lower() == "day":
            if job.interval > -1:
                schedule.every(job.interval).days.do(run_job, job)
                print "Loading daily job:", job.job_name
            else:
                schedule.every().day.at(job.at_time).do(run_job, job)
                print "Loading daily job:", job.job_name
        elif job.time_unit.lower() == "hour":
            if job.interval > -1:
                schedule.every(job.interval).hours.do(run_job, job)
                print "Loading hourly job:", job.job_name
        elif job.time_unit.lower() == "minute":
            if job.interval > -1:
                schedule.every(job.interval).minutes.do(run_job, job)
                print "Loading minute job:", job.job_name
            else:
                schedule.every().minute.do(run_job, job)
                print "Loading minute job:", job.job_name

def run_job(job):
    print 'Running', job.command, "on", job.rtuid
    command = ""
    response = ""
    job_rtu = None

    if job.rtuid.lower() == "virtual":
        response = eval(job.command)
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
    name = '"' + job.job_name + '"'
    rtuid = '"' + job.rtuid + '"'
    command = "INSERT INTO command_log (rtuid, timestamp, command) VALUES (" + rtuid + ", " + timestamp + ", " + name + ")"
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
                unit = '"' + asset.unit + '"'
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
                    value = float(str(data[asset.pin]).replace("%", ""))
                    timestamp = '"' + str(datetime.datetime.now()) + '"'
                    unit = '"' + asset.unit + '"'
                    command = "INSERT INTO sensor_data (asset_id, timestamp, value, unit) VALUES (" + str(asset.asset_id) + ", " + timestamp + ", " + str(value) + ", " + unit + ")"
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
    global site
    #get_sensor_data()
    #scan_for_rtus()
    online_rtus = discover_rtus()
    problem_rtus = validate_pin_modes(online_rtus)

    site = load_site_data()
    if site != None:
        for rtu in problem_rtus:
            print "RTU", rtu.rtuid, "has pin modes incongruent with the database."

        if len(online_rtus) == 0:
            print "There are no RTUs online."
        elif len(online_rtus) == 1:
            print "There is 1 RTU online."
        else:
            print "There are", len(online_rtus), "online."

        jobs = load_interval_schedule()
        prepare_jobs(jobs)

        #print len(jobs)
        while 1:
            schedule.run_pending()
            time.sleep(60)
    else:
        print "Could not load site data. Exiting controller..."

if __name__ == "__main__":
    main(sys.argv[1:])
