#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Master Controller v2.1.1
Author: Tyler Reed
Release: December 2016 Beta

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

import sqlite3                                      # https://www.sqlite.org/index.html
import sys
import operator
import time
import schedule                                     # sudo pip install schedule
import datetime
import urllib2
import json
import subprocess
import rtu_comm
import os
from multiprocessing import Process, Pipe, Queue
import gevent, gevent.server                        # sudo pip install gevent
from telnetsrv.green import TelnetHandler, command  # sudo pip install telnetsrv
import logging
import serial                                       # sudo pip install pyserial
from twilio.rest import TwilioRestClient            # sudo pip install twilio
from influxdb import InfluxDBClient

# for arp-scan: sudo apt install arp-scan
# the suid the program: sudo chmod u+s /usr/bin/arp-scan  (this is on Linux Mint)


rtus = []
reload(sys)
sys.setdefaultencoding('UTF-8')
version = "2.1.1"

class Asset(object):
    def __init__(self):
        self.asset_id = -1
        self.rtuid = ""
        self.abbreviation = ""
        self.name = ""
        self.pin = ""
        self.unit = ""
        self.context = ""
        self.system = ""
        self.value = 0.0
        self.timestamp = 0.0
        self.enabled = False

class Alert(object):
    def __init__(self):
        self.asset_id = -1
        self.value = 0.0

class AlertParam(object):
    def __init__(self):
        self.asset_id = -1
        self.lower_threshold = 0.0
        self.upper_threshold = 0.0
        self.message = ""
        self.response_type = "sms"

class RemoteTerminalUnit(object):
    """Represents a Remote Terminal Unit (RTU).

    Remote Terminal Units interface with sensors and hardware in a HAPI implementation

    Attributes:
        rtuid: The ID of the RTU. Hardcoded in Firmware.
        protocol: RTU communications protocol. E.g. Ethernet, Cellular, ESP8266, USB, WiFi
        address: The address of the RTU on it's specific protocol
        version: Firmware version.
        online: The last known online status/
        pin_modes: Mode settings of the RTUs I/O pins
    """    
    def __init__(self):
        self.rtuid = ""
        self.protocol = ""
        self.address = ""
        self.version = ""
        self.online = False
        self.pin_modes = {}

class Site(object):
    """Represents a HAPI Site (Implementation).

    Attributes:
        site_id: ID of the site
        name: Name of the site
        wunder_key: Weather Underground key to be used
        operator: Name of the primary site operator
        email: Email address of the primary site operator
        phone: Phone number of the primary site operator
        location: Location or Address of the site
        net_iface: Name of the Network Interface to use during auto-discovery
        rtus: List of discovered RTUs
        logger: Logging object to use for logging
    """ 
    
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
        self.net_iface = ""
        self.serial_port = ""
        self.twilio_acct_sid = ""
        self.twilio_auth_token = ""
        self.rtus = []
        self.logger = None

        # Setup Logging
        logger_level = logging.DEBUG
        self.logger = logging.getLogger('hapi_master_controller')
        self.logger.setLevel(logger_level)

        # create logging file handler
        file_handler = logging.FileHandler('hapi_mc.log', 'a')
        file_handler.setLevel(logger_level)

        # create logging console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger_level)

        #Set logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_assets(self):
        assets = []
        field_names = '''
            asset_id
            rtuid
            abbreviation
            name
            pin
            unit
            context
            system
            enabled
        '''.split()
        try:
            conn = sqlite3.connect('hapi.db')
            c=conn.cursor()
            sql = 'SELECT {field_names} FROM assets;'.format(
                field_names=', '.join(field_names))
            rows = c.execute(sql)
            for row in rows:
                asset = Asset()
                for field_name, field_value in zip(field_names, row):
                    setattr(asset, field_name, field_value)
                asset.enabled = bool(asset.enabled)  # Probably superfluous.

                assets.append(asset)
            conn.close()
        except Exception, excpt:
            self.logger.exception("Error loading site data: %s", excpt)

        return assets

    def load_site_data(self):
        field_names = '''
            site_id
            name
            wunder_key
            operator
            email
            phone
            location
            longitude
            latitude
            net_iface
            serial_port
            twilio_acct_sid
            twilio_auth_token
        '''.split()
        try:
            conn = sqlite3.connect('hapi.db')
            c = conn.cursor()
            sql = 'SELECT {field_names} FROM site LIMIT 1;'.format(
                field_names=', '.join(field_names))
            db_elements = c.execute(sql)
            for row in db_elements:
                for field_name, field_value in zip(field_names, row):
                    setattr(self, field_name, field_value)

            conn.close()
            self.logger.info("Site data loaded.")
        except Exception, excpt:
            self.logger.exception("Error loading site data: %s", excpt)

    def discover_rtus(self):
        valid_ip_addresses = self.scan_for_rtus()
        self.rtus = []

        for ip_address in valid_ip_addresses:
            self.logger.info("Connecting to RTU at " + ip_address)
            try:
                target_rtu = rtu_comm.RTUCommunicator()
                response = target_rtu.send_to_rtu(ip_address, 80, 5, "sta").split('\r\n')
                self.logger.info(response[0] + " at " + ip_address + " is running " + response[1])
                rtu = RemoteTerminalUnit()
                rtu.rtuid = response[0]
                rtu.address = ip_address
                rtu.version = response[1]
                rtu.online = True
                # get_pin_modes(rtu)
                self.rtus.append(rtu)
            except Exception, excpt:
                self.logger.exception("Error communicating with rtu at " + ip_address + ": %s", excpt)

        # try:
        #     self.logger.info("Polling USB for additional RTUs...")
        #     ser_response = ""
        #     ser = serial.Serial('/dev/ttyACM0', 115200)
        #     #response = target_rtu.send_to_rtu("usb", 80, 3, "sta").split('\r\n')

        #     if len(response) > 0:
        #         self.logger.info(response[0] + " on USB is running " + response[1])
        #         rtu = RemoteTerminalUnit()
        #         rtu.rtuid = response[0]
        #         rtu.address = "usb"
        #         rtu.version = response[1]
        #         rtu.online = True
        #         #get_pin_modes(rtu)
        #         self.rtus.append(rtu)
        # except Exception, excpt:
        #     if self.logger is not None:
        #         self.logger.warning("No RTU found on USB: %s", excpt)

        return self.rtus

    def scan_for_rtus(self):
        rtu_addresses = []
        try:
            self.logger.info("Scanning local network for RTUs...")
            iface = "--interface=" + self.net_iface
            netscan = subprocess.check_output(["arp-scan", iface, "--localnet"])
            netscan = netscan.split('\n')
            for machine in netscan:
                if machine.find("de:ad:be:ef") > -1:
                    els = machine.split("\t")
                    ip_address = els[0]
                    self.logger.info("Found RTU at: " + ip_address)
                    rtu_addresses.append(ip_address)

        except Exception, excpt:
            self.logger.exception("Error scanning local network: %s", excpt)

        return rtu_addresses
    
    def get_asset_value(self, asset_name):
        value = ""
        assets = self.get_assets()
        try:
            for asset in assets:
                print "!" + asset_name + "!" + "!" + asset.name + "!"
                if asset_name == asset.name.lower().strip():
                    for rtu in self.rtus:
                        print rtu.rtuid, asset.rtuid 
                        if rtu.rtuid == asset.rtuid:
                            try:
                                print 'Getting asset value', asset.name, "from", asset.rtuid
                                command = "env"
                                target_rtu = rtu_comm.RTUCommunicator()
                                data = target_rtu.send_to_rtu(rtu.address, 80, 5, command)
                                print data
                                parsed_json = json.loads(data)
                                asset.value = parsed_json[asset.pin]
                                asset.timestamp = datetime.datetime.now()
                                print asset.name, "is", asset.value
                                value = str(asset.value)
                            except Exception, excpt:
                                self.logger.exception("Error getting asset data: %s", excpt)
        except Exception, excpt:
            self.logger.exception("Error getting asset data: %s", excpt)

        return value

    def set_asset_value(self, asset_name, value):
        data = ""
        assets = self.get_assets()
        try:
            for asset in assets:
                print "!" + asset_name + "!" + "!" + asset.name + "!"
                if asset_name == asset.name.lower().strip():
                    for rtu in self.rtus:
                        print rtu.rtuid, asset.rtuid 
                        if rtu.rtuid == asset.rtuid:
                            try:
                                print 'Setting asset value', asset.name, "from", asset.rtuid
                                command = "doc" + asset.pin + value
                                print "set_asset_value: " + command
                                target_rtu = rtu_comm.RTUCommunicator()
                                data = target_rtu.send_to_rtu(rtu.address, 80, 5, command)
                            except Exception, excpt:
                                self.logger.exception("Error getting asset data: %s", excpt)
        except Exception, excpt:
            self.logger.exception("Error getting asset data: %s", excpt)

        return data

    def check_alerts(self):
        assets = self.get_assets()
        alert_params = get_alert_params()
        self.logger.info("Checking site for alert conditions.")
        print "Found", len(alert_params), "alert parameters."
        try:
            for alert_param in alert_params:
                for asset in assets:
                    if alert_param.asset_id == asset.asset_id:
                        for rtu in self.rtus:
                            if rtu.rtuid == asset.rtuid:
                                try:
                                    print 'Getting asset status', asset.name, "from", asset.rtuid
                                    command = "env"
                                    target_rtu = rtu_comm.RTUCommunicator()
                                    data = target_rtu.send_to_rtu(rtu.address, 80, 5, command)
                                    print data
                                    parsed_json = json.loads(data)
                                    asset.value = parsed_json[asset.pin]
                                    asset.timestamp = datetime.datetime.now()
                                    print asset.name, "is", asset.value
                                    print "Lower Threshold is", alert_param.lower_threshold
                                    print "Upper Threshold is", alert_param.upper_threshold
                                    if not (alert_param.lower_threshold < float(asset.value) < alert_param.upper_threshold):
                                        alert = Alert()
                                        alert.asset_id = asset.asset_id
                                        alert.value = asset.value
                                        log_alert_condition(alert, self.logger)
                                        send_alert_condition(self, asset, alert, alert_param, self.logger)
                                except Exception, excpt:
                                    self.logger.exception("Error getting asset data: %s", excpt)

        except Exception, excpt:
            self.logger.exception("Error getting asset data: %s", excpt)

    def assets(self):
        result_assets = []

        assets = self.get_assets()
        for asset in assets:
            result_assets.append(asset.name)
        return result_assets

    def assets_by_context(self, context):
        result_assets = []

        assets = self.get_assets()
        for asset in assets:
            if asset.context.lower() == context.lower():
                if asset.rtuid != "virtual":
                    for rtu in self.rtus:
                        if rtu.rtuid == asset.rtuid:
                            try:
                                print 'Getting asset status', asset.name, "from", asset.rtuid
                                command = "env"
                                target_rtu = rtu_comm.RTUCommunicator()
                                data = target_rtu.send_to_rtu(rtu.address, 80, 5, command)
                                print data
                                parsed_json = json.loads(data)
                                asset.value = parsed_json[asset.pin]
                                asset.timestamp = datetime.datetime.now()
                                print asset.name, "is", asset.value
                                result_assets.append(asset)
                            except Exception, excpt:
                                self.logger.exception("Error getting asset data: %s", excpt)
                else:
                    # For virtual assets, assume that the data is already parsed JSON
                    try:
                        for asset in assets:
                            if asset.rtuid == "virtual":
                                if asset.abbreviation == "weather":
                                    asset.value = float(str(data[asset.pin]).replace("%", ""))
                                    asset.timestamp = '"' + str(datetime.datetime.now()) + '"'
                                    result_assets.append(asset)
                    except Exception, excpt:
                        error = "Error getting virtual asset data: " + excpt
                        print error
                        if logger is not None:
                            logger.exception(error)
        return result_assets

    def log_sensor_data(self, data, virtual, logger):
        assets = self.get_assets()
        if not virtual:
            try:
                for asset in assets:
                    if asset.enabled:
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
                            self.push_data(asset.rtuid, asset.name, asset.context, str(datetime.datetime.now()), value, asset.unit)

            except Exception, excpt:
                print "Error logging sensor data.", excpt
        else:
            # For virtual assets, assume that the data is already parsed JSON
            try:
                for asset in assets:
                    if asset.enabled:
                        if asset.rtuid == "virtual":
                            if asset.abbreviation == "weather":
                                print "asset.pin", asset.pin
                                print "data[asset.pin]", data[asset.pin]

                                str(data[asset.pin])
                                value = str(data[asset.pin]).replace("%", "")
                                print "value", value
                                timestamp = '"' + str(datetime.datetime.now()) + '"'
                                unit = '"' + asset.unit + '"'
                                command = "INSERT INTO sensor_data (asset_id, timestamp, value, unit) VALUES (" + str(asset.asset_id) + ", " + timestamp + ", " + str(value) + ", " + unit + ")"
                                print command
                                conn = sqlite3.connect('hapi.db')
                                c=conn.cursor()
                                c.execute(command)
                                conn.commit()
                                self.push_data(asset.rtuid, asset.name, asset.context, str(datetime.datetime.now()), value, asset.unit)
                                conn.close()
            except Exception, excpt:
                print "Error logging sensor data.", excpt
                # error = "Error logging sensor data: " + excpt
                # print error
                # if logger is not None:
                #     logger.exception(error)


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

    def push_data(self, rtu_id, asset_name, asset_context, timestamp, value, unit):
        try:
            client = InfluxDBClient('138.197.74.74', 8086, 'early', 'adopter')
            dbs = client.get_list_database()
            found = False
            for item in dbs:
                if asset_context in item:
                    found = True
            
            if not found:
                client.query("CREATE DATABASE {0}".format('"' + asset_context + '"'))

            client = InfluxDBClient('138.197.74.74', 8086, 'early', 'adopter', asset_context)

            json_body = [
                {
                    "measurement": asset_context,
                    "tags": {
                        "site": self.name,
                        "rtu": rtu_id,
                        "asset": asset_name
                    },
                    "time": str(datetime.datetime.now()),
                    "fields": {
                        "value": value,
                        "unit": unit
                    }
                }
            ]
            print str(json_body)
            client.write_points(json_body)
            #self.logger.info("Wrote to analytic database: " + str(json_body))
        except Exception, excpt:
            self.logger.exception('Error writing to analytic database: %s', excpt)



    def get_weather(self):
        response = ""
        try:
            response = ""
            command = 'http://api.wunderground.com/api/' + site.wunder_key + '/geolookup/conditions/q/OH/Columbus.json'
            print command
            f = urllib2.urlopen(command)
            json_string = f.read()
            parsed_json = json.loads(json_string)
            response = parsed_json['current_observation']
            f.close()
        except Exception, excpt:
            print "Error getting weather data.", excpt
        return response

    def log_command(self, job):
        timestamp = '"' + str(datetime.datetime.now()) + '"'
        name = '"' + job.job_name + '"'
        rtuid = '"' + job.rtuid + '"'
        command = "INSERT INTO command_log (rtuid, timestamp, command) VALUES (" + rtuid + ", " + timestamp + ", " + name + ")"
        logger.info("Executed " + job.job_name + " on " + job.rtuid)
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()
        c.execute(command)
        conn.commit()
        conn.close()

    def log_alert_condition(self, alert, logger):
        try:
            timestamp = '"' + str(datetime.datetime.now()) + '"'
            command = "INSERT INTO alert_log (asset_id, value, timestamp) VALUES (" + str(alert.asset_id) + ", " + timestamp + ", " + str(alert.value) + ")"
            print command
            conn = sqlite3.connect('hapi.db')
            c=conn.cursor()
            c.execute(command)
            conn.commit()
            conn.close()
        except Exception, excpt:
            print "Error logging alert condition.", excpt

    def send_alert_condition(self, site, asset, alert, alert_param, logger):
        try:
            if alert_param.response_type.lower() == "sms":
                #ACCOUNT_SID = ""
                #AUTH_TOKEN = ""
                timestamp = '"' + str(datetime.datetime.now()) + '"'
                message = "Alert from " + site.name + ": " + asset.name + '\r\n'
                message = message + alert_param.message + '\r\n'
                message = message + "  Value: " + str(alert.value) + '\r\n'
                message = message + "  Timestamp: " + timestamp + '\r\n'
                #client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)      
                #client.messages.create(to="+receiving number", from_="+sending number", body=message, )
                print "Alert condition sent."

        except Exception, excpt:
            print "Error sending alert condition.", excpt

    def get_alert_params(self):
        alert_params = []
        field_names = '''
            asset_id
            lower_threshold
            upper_threshold
            message
            response_type
        '''.split()
        try:
            conn = sqlite3.connect('hapi.db')
            c=conn.cursor()
            sql = 'SELECT {field_names} FROM alert_params;'.format(
                field_names=', '.join(field_names))
            rows = c.execute(sql)
            for row in rows:
                alert_param = Asset()
                for field_name, field_value in zip(field_names, row):
                    setattr(alert_param, field_name, field_value)
                alert_param.lower_threshold = float(alert_param.lower_threshold)
                alert_param.upper_threshold = float(alert_param.upper_threshold)
                alert_params.append(alert_param)
            conn.close()
        except Exception, excpt:
            print "Error loading alert parameters. %s", excpt

        return alert_params

class Scheduler(object):
    def __init__(self):
        self.running = True
        self.logger = None
        self.site = None
        self.processes = []

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
            self.sequence = ""
            self.timeout = 0.0

    def process_sequence(self, seq_jobs, job, job_rtu, seq_result):
        for row in seq_jobs:
            seq_result.put("Running " + row[0] + ":" + row[2] + "(" + command + ")" + " on " + job.rtuid + " at " + job_rtu.address + ".")
            command = row[1].encode("ascii")
            timeout = int(row[3])
            target_rtu = rtu_comm.RTUCommunicator()
            seq_result.put(target_rtu.send_to_rtu(job_rtu.address, 80, 10, command) + "\r\n")
            seq_result.put("Sleeping for", timeout, "seconds.")
            time.sleep(timeout)

    def load_interval_schedule(self):
        job_list = []
        self.logger.info("Scheduler data loading...")
        field_names = '''
            job_id
            job_name
            rtuid
            command
            time_unit
            interval
            at_time
            enabled
            sequence
            timeout
        '''.split()
        try:
            conn = sqlite3.connect('hapi.db')
            c=conn.cursor()

            sql = 'SELECT {field_names} FROM interval_schedule;'.format(
                field_names=', '.join(field_names))
            db_jobs = c.execute(sql)
            for row in db_jobs:
                job = Scheduler.IntervalJob()
                for field_name, field_value in zip(field_names, row):
                    setattr(job, field_name, field_value)
                job.command = job.command.encode('ascii')
                job_list.append(job)

            conn.close()

        except Exception, excpt:
            self.logger.exception("Error loading interval_schedule. %s", excpt)

        return job_list

    def prepare_jobs(self, jobs):
        for job in jobs:
            if job.time_unit.lower() == "month":
                if job.interval > -1:
                    schedule.every(job.interval).months.do(self.run_job, job)
                    self.logger.info("  Loading monthly job: " + job.job_name)
            elif job.time_unit.lower() == "week":
                if job.interval > -1:
                    schedule.every(job.interval).weeks.do(self.run_job, job)
                    self.logger.info("  Loading weekly job: " + job.job_name)
            elif job.time_unit.lower() == "day":
                if job.interval > -1:
                    schedule.every(job.interval).days.do(self.run_job, job)
                    self.logger.info("  Loading daily job: " + job.job_name)
                else:
                    schedule.every().day.at(job.at_time).do(self.run_job, job)
                    self.logger.info("  Loading time-based job: " + job.job_name)
            elif job.time_unit.lower() == "hour":
                if job.interval > -1:
                    schedule.every(job.interval).hours.do(self.run_job, job)
                    self.logger.info("  Loading hourly job: " + job.job_name)
            elif job.time_unit.lower() == "minute":
                if job.interval > -1:
                    schedule.every(job.interval).minutes.do(self.run_job, job)
                    self.logger.info("  Loading minutes job: " + job.job_name)
                else:
                    schedule.every().minute.do(self.run_job, job)
                    self.logger.info("  Loading minute job: " + job.job_name)
            elif job.time_unit.lower() == "second":
                if job.interval > -1:
                    schedule.every(job.interval).seconds.do(self.run_job, job)
                    self.logger.info("  Loading seconds job: " + job.job_name)
                else:
                    schedule.every().second.do(self.run_job, job)
                    self.logger.info("  Loading second job: " + job.job_name)

    def run_job(self, job):
        if self.running:
            command = ""
            response = ""
            job_rtu = None

            if job.enabled:
                print "Job enabled"
                print "Job rtuid", job.rtuid
                print "Job command", job.command
                print "Job sequence", job.sequence
                if job.sequence is None:
                    job.sequence = ""

                if job.rtuid.lower() == "virtual":
                    print 'Running on virtual RTU', job.command, "on", job.rtuid
                    try:
                        response = eval(job.command)
                        if job.command != "spin":
                            self.site.log_sensor_data(response, True, self.logger)
                    except Exception, excpt:
                        error = "Error running job " + job.job_name + " on " + job_rtu.rtuid + ": " + excpt
                        print error
                        if self.logger is not None:
                            self.logger.exception(error)
                else:
                    try:
                        for rtu_el in self.site.rtus:
                            if rtu_el.rtuid == job.rtuid:
                                if rtu_el.online:
                                    job_rtu = rtu_el

                        if job_rtu is not None:
                            if str.strip(job.sequence) != "":
                                print 'Running sequence', job.sequence, "on", job.rtuid
                                conn = sqlite3.connect('hapi.db')
                                c=conn.cursor()
                                seq_jobs = c.execute('SELECT name, command, step_name, timeout FROM sequence WHERE name = "' + job.sequence + '" ORDER BY step ;')
                                print "len(seq_jobs) = "  + str(len(seq_jobs))
                                p = Process(target=self.process_sequence, args=(seq_jobs, job, job_rtu, seq_result,))
                                p.start()
                                conn.close()
                            else:
                                print 'Running command', job.command, "on", job.rtuid
                                command = job.command
                                target_rtu = rtu_comm.RTUCommunicator()
                                print "Sending", command, "to ", job_rtu.address
                                response = target_rtu.send_to_rtu(job_rtu.address, 80, job.timeout, command)
                                if job.job_name == "Log Data":
                                    self.site.log_sensor_data(response, False, self.logger)
                                elif job.job_name == "Log Status":
                                    pass
                                else:
                                    log_command(job)
                        else:
                            print "Could not find rtu."
                            if self.logger is not None:
                                self.logger.info("Could not find rtu " + job.rtuid)

                    except Exception, excpt:
                        logger.exception('Error running job: %s', excpt)

    def spin():
        for p in self.processes:
            if not p.is_alive():
                print p.exitcode

class HAPIListener(TelnetHandler):
    global the_rtu
    the_rtu = None
    global site
    site = Site()
    #site.logger = logger
    site.load_site_data()
    site.discover_rtus()

    global launch_time
    launch_time = datetime.datetime.now()

    if site is not None:
        WELCOME = "\n" + "Welcome to HAPI facility " + site.name + '\n'
        WELCOME = WELCOME + "Operator: " + site.operator + '\n'
        WELCOME = WELCOME + "Phone: " + site.phone + '\n'
        WELCOME = WELCOME + "Email: " + site.email + '\n'
        WELCOME = WELCOME + "Location: " + site.location + '\n'
        WELCOME = WELCOME + "\n" + 'Type "help" for a list of valid commands.' + '\n'
    else:
        WELCOME = "No site data found."

    PROMPT = site.name + "> "
    
    # def __init__(self, *args):
    #     print "Listener Init"
    #     print args

    def session_start(self):
        self.the_rtus = []
        self.the_rtus = site.rtus

        logger_level = logging.DEBUG
        self.logger = logging.getLogger('hapi_listener')
        self.logger.setLevel(logger_level)

        # create logging file handler
        file_handler = logging.FileHandler('hapi_listener.log', 'a')
        file_handler.setLevel(logger_level)

        # create logging console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger_level)

        #Set logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.info("Listener Session Started")

    @command('abc')
    def command_abc(self, params):
        '''<context of assets for data>
        Gets Asset data By Context.

        '''
        if len(params) > 0:
            context = params[0]
            self.writeresponse("Gathering asset data by context: " + context)
            data = site.assets_by_context(context)
            result = "{"
            for asset in data:
                result = result + '"' + asset.name + '":"' + asset.value + '"' + ','
            result = result + "}"
            self.writeresponse(result)
        else:
            self.writeresponse('No context provided.')

    @command('asset')
    def command_asset(self, params):
        '''<get value for named asset>
        Gets the current value for the named asset.
        '''
        asset = ""
        
        for param in params:
            asset = asset + " " + param.encode('utf-8').strip()

        asset = asset.lower().strip()
        print "MC:Listener:asset:", asset
        value = site.get_asset_value(asset)

        print "Sending asset", params[0], value
        self.writeline(value)

    @command('assets')
    def command_assets(self, params):
        '''<get all asset names>
        Gets all Asset names.

        '''
        self.writeline(str(site.assets()))

    @command('cmd')
    def command_cmd(self, params):
        '''<command to be run on connected RTU>
        Sends a command to the connected RTU

        '''
        if the_rtu is None:
            self.writeresponse("You are not connected to an RTU.")
        else:
            command = params[0]

            self.writeresponse("Executing " + command + " on " + the_rtu.rtuid + "...")
            target_rtu = rtu_comm.RTUCommunicator()
            response = target_rtu.send_to_rtu(the_rtu.address, 80, 1, command)
            self.writeresponse(response)
            job = IntervalJob()
            job.job_name = command
            job.rtuid = the_rtu.rtuid
            log_command(job)

    @command('connect')
    def command_connect(self, params):
        '''<Name of RTU>
        Connects to the specified RTU

        '''
        global the_rtu
        PROMPT = "HAPI> "
        rtu_name = params[0]

        the_rtu = None
        for rtu in site.rtus:
            if rtu.rtuid.lower() == rtu_name.lower():
                the_rtu = rtu
        if the_rtu is not None:
            self.writeresponse("Connecting to " + rtu_name + "...")
            target_rtu = rtu_comm.RTUCommunicator()
            response = target_rtu.send_to_rtu(the_rtu.address, 80, 3, "env")            
            self.writeresponse(response)
        else:
            self.writeresponse(rtu_name + " is not online at this site.")

    @command('continue')
    def command_continue(self, params):
        '''
        Starts the Master Controller's Scheduler

        '''
        f = open("ipc.txt", "wb")
        f.write("run")
        f.close() 

    @command('pause')
    def command_pause(self, params):
        '''
        Pauses the Master Controller's Scheduler

        '''
        f = open("ipc.txt", "wb")
        f.write("pause")
        f.close()

    @command('run')
    def command_run(self, params):
        '''
        Starts the Master Controller's Scheduler

        '''
        if the_rtu is None:
            self.writeresponse("You are not connected to an RTU.")
        else:
            command = params[0]

            scheduler = Scheduler()
            scheduler.site = site
            scheduler.logger = self.logger

            print "Running", params[0], params[1], "on", the_rtu.rtuid
            job = IntervalJob()
            job.job_name = "User-defined"
            job.enabled = True
            job.rtuid = the_rtu.rtuid

            if params[0] == "command":
                job.command = params[1]
            elif params[0] == "sequence":
                job.sequence = params[1]

            print "Passing job to the scheduler."
            scheduler.run_job(job)

    @command('rtus')
    def command_rtus(self, params):
        '''
        List all RTUs discovered at this site.

        '''
        self.writeresponse(str(len(self.the_rtus)) + " RTUs found on-site.")
        for rtu in self.the_rtus:
            self.writeresponse(rtu.rtuid + " at " + rtu.address + " is online and running HAPI " + rtu.version + ".")
    
    @command('status')
    def command_status(self, params):
        '''
        Return operational status of the Master Controller

        '''
        print "Received Status command."
        data = '\nMaster Controller Status\n'
        data = data + '  Software Version v' + version + '\n'
        data = data + '  Running on: ' + sys.platform + '\n'
        data = data + '  Encoding: ' + sys.getdefaultencoding() + '\n'
        data = data + '  Python Information\n'
        data = data + '   - Executable: ' + sys.executable + '\n'
        data = data + '   - v' + sys.version[0:7] + '\n'
        data = data + '   - location: ' + sys.executable + '\n'
        data = data + '  RTUs Online: ' + str(len(self.the_rtus)) + '\n'
        data = data + '  Timestamp: ' + str(datetime.datetime.now())[0:19] + '\n'
        uptime = datetime.datetime.now() - launch_time
        days = uptime.days
        hours = int(divmod(uptime.seconds, 86400)[1] / 3600)
        minutes = int(divmod(uptime.seconds, 3600)[1] / 60)
        uptime_str = "This listener has been online for " + str(days) + " days, " + str(hours) + " hours and " + str(minutes) + " minutes."
        data = data + '  Uptime: ' + uptime_str + '\n'
        #data = data + '  Copyright 2016, Maya Culpa, LLC\n'
        data = data + '###\n'
        self.writeresponse(data)

    @command('stop')
    def command_stop(self, params):
        '''
        Kills the HAPI listener service

        '''
        f = open("ipc.txt", "wb")
        f.write("stop")
        f.close()

    @command('turnoff')
    def command_turnoff(self, params):
        '''<Turn On Asset>
        Turn on the named asset.
        '''
        asset = ""
        
        for param in params:
            asset = asset + " " + param.encode('utf-8').strip()

        asset = asset.lower().strip()
        print "MC:Listener:asset:", asset
        value = site.set_asset_value(asset, "1")

        print "Sending asset", params[0], value
        self.writeline(value)

    @command('turnon')
    def command_turnon(self, params):
        '''<Turn On Asset>
        Turn on the named asset.
        '''
        asset = ""
        
        for param in params:
            asset = asset + " " + param.encode('utf-8').strip()

        asset = asset.lower().strip()
        print "MC:Listener:asset:", asset
        value = site.set_asset_value(asset, "0")

        print "Sending asset", params[0], value
        self.writeline(value)


def run_listener(conn):
    server = gevent.server.StreamServer(("", 8023), HAPIListener.streamserver_handle)
    server.serve_forever()

def main(argv):
    global rtus
    global site
    global logger

    # Setup Logging
    logger_level = logging.DEBUG
    logger = logging.getLogger('hapi_master_controller')
    logger.setLevel(logger_level)

    # create logging file handler
    file_handler = logging.FileHandler('hapi_mc.log', 'a')
    file_handler.setLevel(logger_level)

    # create logging console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger_level)

    #Set logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    try:
        site = Site()
        site.logger = logger
        site.load_site_data()
        rtus = site.discover_rtus()
        #ACCOUNT_SID = <your twilio account SID here>
        #AUTH_TOKEN = <your twilio account token here>
        #client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)      
        #client.messages.create(to=<+receiving number>, from_=<+sending number>, body="HAPI Master Controller is online.", )

        # problem_rtus = validate_pin_modes(rtus)
    except Exception, excpt:
        logger.exception("Error loading site information. %s", excpt)

    if site is not None:
        if len(site.rtus) == 0:
            logger.info("There are no RTUs online.")
        elif len(site.rtus) == 1:
            logger.info("There is 1 RTU online.")
        else:
            logger.info("There are " + str(len(site.rtus)) + " RTUs online.")
    try:
        logger.info("Initializing Listener...")
        listener_parent_conn, listener_child_conn = Pipe()
        p = Process(target=run_listener, args=(listener_child_conn,))
        p.start()
        logger.info("Listener is online.")
    except Exception, excpt:
        logger.exception("Error loading initializing listener. %s", excpt)

    # Loading scheduled jobs
    try:
        logger.info("Initializing scheduler...")
        scheduler = Scheduler()
        scheduler.site = site
        scheduler.logger = logger
        scheduler.prepare_jobs(scheduler.load_interval_schedule())
        count = 1
        logger.info("Scheduler is online.")
    except Exception, excpt:
        logger.exception("Error initializing scheduler. %s", excpt)

    while 1:
        #print listener_parent_conn.recv()
        try:
            if count % 60 == 0:
                print ".",
            time.sleep(5)
            count = count + 5
            schedule.run_pending()

            if os.path.isfile("ipc.txt"):
                f = open("ipc.txt", "rb")
                data = f.read()
                f.close()
                open("ipc.txt", 'w').close()
                if data != "":
                    if data == "run":
                        scheduler.running = True
                        logger.info("The scheduler is running.")
                    elif data == "pause":
                        logger.info("The scheduler has been paused.")
                        scheduler.running = False
                    else:
                        logger.info("Received from Listener: " + data)
        except Exception, excpt:
            logger.exception("Error in Master Controller main loop. %s", excpt)            

if __name__ == "__main__":
    main(sys.argv[1:])
