# -*- coding: utf-8 -*-
#!/usr/bin/env python

'''
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
'''

import sqlite3                                      # https://www.sqlite.org/index.html
import sys
import time
import schedule                                     # sudo pip install schedule
import datetime
import dateutil.parser
import urllib2
import json
import subprocess
import communicator
import socket
import psutil
from multiprocessing import Process
import logging
#from twilio.rest import TwilioRestClient            # sudo pip install twilio
from influxdb import InfluxDBClient
from status import SystemStatus

# the suid the program: sudo chmod u+s /usr/bin/arp-scan  (this is on Linux Mint)


rtus = []
reload(sys)
#sys.setdefaultencoding('UTF-8')
version = "2.1.1"
sm_logger = "smart_module"

class Asset(object):
    def __init__(self):
        self.asset_id = -1
        self.abbreviation = ""
        self.name = ""
        self.unit = ""
        self.context = ""
        self.system = ""
        self.enabled = False

    class AssetValue(object):
        def __init__(self):
            self.asset_id = -1
            self.timestamp = None
            self.value = None


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

class SmartModule(object):
    """Represents a HAPI Smart Module (Implementation).

    Attributes:
        site_id: ID of the site
        name: Name of the site
        wunder_key: Weather Underground key to be used
        operator: Name of the primary site operator
        email: Email address of the primary site operator
        phone: Phone number of the primary site operator
        location: Location or Address of the site
    """

    def __init__(self):
        logging.getLogger(sm_logger).info("Smart Module Initializing.")
        self.comm = communicator.Communicator()
        self.data_sync = DataSync()
        self.comm.site = self
        self.site_id = ""
        self.name = ""
        self.wunder_key = ""
        self.operator = ""
        self.email = ""
        self.phone = ""
        self.location = ""
        self.longitude = ""
        self.latitude = ""
        self.twilio_acct_sid = ""
        self.twilio_auth_token = ""
        self.launch_time = datetime.datetime.now()
        self.assets = []
        self.scheduler = None
        self.hostname = ""
        logging.getLogger(sm_logger).info("Smart Module initialization complete.")

    def discover(self):
        logging.getLogger(sm_logger).info("Performing Discovery...")
        subprocess.call("sudo ./host-hapi.sh", shell=True)
        self.comm.smart_module = self
        self.comm.client.loop_start()
        self.comm.connect()
        t_end = time.time() + 10
        while (time.time() < t_end) and (self.comm.is_connected is False):
            time.sleep(1)

        # while self.comm.is_connected == False:
        #     self.comm.connect()

        #     if self.comm.is_connected is False:
        #         logging.getLogger(sm_logger).info("No MQTT Broker found. Becoming the broker.")
        #         subprocess.call("sudo ./host-hapi.sh", shell=True)

        #logging.getLogger(sm_logger).info("Connected to mqttbroker.local")
        self.hostname = socket.gethostname()
        self.comm.send("ANNOUNCE", socket.gethostname() + " is online.")
        

        self.comm.subscribe("SCHEDULER/IDENT")
        self.comm.send("SCHEDULER/LOCATE", "Where are you?")
        t_end = time.time() + 2
        while (time.time() < t_end) and (self.comm.is_connected is False):
            time.sleep(1)

        if self.comm.scheduler_found == False:
            # Loading scheduled jobs
            try:
                logging.getLogger(sm_logger).info("No Scheduler found. Becoming the Scheduler.")
                self.scheduler = Scheduler()
                self.scheduler.site = self
                self.scheduler.running = True
                self.scheduler.prepare_jobs(self.scheduler.load_interval_schedule())
                self.comm.scheduler_found = True
                self.comm.subscribe("SCHEDULER/LOCATE")
                self.comm.unsubscribe("SCHEDULER/IDENT")
                self.comm.send("SCHEDULER/IDENT", socket.gethostname() + ".local")
                self.comm.send("ANNOUNCE", socket.gethostname() + ".local" + " is running the Scheduler.")
                logging.getLogger(sm_logger).info("Scheduler program loaded.")
            except Exception, excpt:
                logging.getLogger(sm_logger).exception("Error initializing scheduler. %s", excpt)

    def get_assets(self):
        try:
            conn = sqlite3.connect('hapi_core.db')
            c=conn.cursor()
            sql = "SELECT asset_id, abbreviation, name, unit, context, system, enabled FROM assets;"
            rows = c.execute(sql)
            for field in rows:
                asset = Asset()
                asset.asset_id = field[0]
                asset.abbreviation = field[1]
                asset.name = field[2]
                asset.unit = field[3]
                asset.context = field[4]
                asset.system = field[5]
                if field[6] == 1:
                    asset.enabled = True

                self.assets.append(asset)
            conn.close()
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error loading assets: %s", excpt)

        return assets

    def load_site_data(self):
        try:
            conn = sqlite3.connect('hapi_core.db')
            c = conn.cursor()
            sql = "SELECT site_id, name, wunder_key, operator, email, phone, location, longitude, latitude, twilio_acct_sid, twilio_auth_token FROM site LIMIT 1;"
            db_elements = c.execute(sql)
            for field in db_elements:
                self.site_id = field[0]
                self.name = field[1]
                self.wunder_key = field[2]
                self.operator = field[3]
                self.email = field[4]
                self.phone = field[5]
                self.location = field[6]
                self.longitude = field[7]
                self.latitude = field[8]
                self.twilio_acct_sid = field[9]
                self.twilio_auth_token = field[10]

            conn.close()
            logging.getLogger(sm_logger).info("Site data loaded.")
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error loading site data: %s", excpt)

    def get_status(self):
        SYSINFO = SystemStatus(update=True)
        return str(SYSINFO)

    def get_asset_value(self, asset_name):
        value = ""
        assets = self.get_assets()
        try:
            for asset in assets:
                if asset_name.lower().strip() == asset.name.lower().strip():
                    try:
                        print 'Getting asset value', asset.name, "from", asset.rtuid
                        self.comm.send("RESPONSE/ASSET/" + asset_name.lower().strip())

                    except Exception, excpt:
                        logging.getLogger(sm_logger).exception("Error getting asset data: %s", excpt)

        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error getting asset data: %s", excpt)

        return value

    def set_asset_value(self, asset_name, value):
        data = ""
        assets = self.get_assets()
        try:
            for asset in assets:
                if asset_name == asset.name.lower().strip():
                    self.comm.subscribe("RESPONSE/ASSET/" + asset_name.lower().strip())
                    self.comm.send("COMMAND/ASSET/" + asset_name.lower().strip(), value)
                    try:
                        print 'Setting asset value', asset.name, "from", asset.rtuid
                    except Exception, excpt:
                        logging.getLogger(sm_logger).exception("Error setting asset value: %s", excpt)
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error setting asset value: %s", excpt)

        return data

    def check_alerts(self):
        assets = self.get_assets()
        alert_params = self.get_alert_params()
        logging.getLogger(sm_logger).info("Checking site for alert conditions.")
        print "Found", len(alert_params), "alert parameters."
        try:
            for alert_param in alert_params:
                for asset in assets:
                    if alert_param.asset_id == asset.asset_id:
                        try:
                            print 'Getting asset status', asset.name, "from", asset.rtuid
                            data = "" # go get data
                            print data
                            parsed_json = json.loads(data)
                            asset.value = parsed_json[asset.pin]
                            asset.timestamp = datetime.datetime.now()
                            print asset.name, "is", asset.value
                            print "Lower Threshold is", alert_param.lower_threshold
                            print "Upper Threshold is", alert_param.upper_threshold
                            if (float(asset.value) < alert_param.lower_threshold) or (float(asset.value) > alert_param.upper_threshold):
                                alert = Alert()
                                alert.asset_id = asset.asset_id
                                alert.value = asset.value
                                log_alert_condition(alert)
                                send_alert_condition(self, asset, alert, alert_param)
                        except Exception, excpt:
                            logging.getLogger(sm_logger).exception("Error getting asset data: %s", excpt)

        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error getting asset data: %s", excpt)

    def log_sensor_data(self, data, virtual):
        assets = self.get_assets()
        if virtual == False:
            try:
                for asset in assets:
                    if asset.enabled is True:
                        parsed_json = json.loads(data)
                        if asset.rtuid == parsed_json['name']:
                            value = parsed_json[asset.pin]
                            timestamp = '"' + str(datetime.datetime.now()) + '"'
                            unit = '"' + asset.unit + '"'
                            command = "INSERT INTO sensor_data (asset_id, timestamp, value, unit) VALUES (" + str(asset.asset_id) + ", " + timestamp + ", " + value + ", " + unit + ")"
                            print command
                            conn = sqlite3.connect('hapi_history.db')
                            c=conn.cursor()
                            c.execute(command)
                            conn.commit()
                            conn.close()
                            self.push_data(asset.rtuid, asset.name, asset.context, value, asset.unit)
            except Exception, excpt:
                print "Error logging sensor data.", excpt
        else:
            # For virtual assets, assume that the data is already parsed JSON
            try:
                for asset in assets:
                    if asset.enabled is True:
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
                                conn = sqlite3.connect('hapi_history.db')
                                c=conn.cursor()
                                c.execute(command)
                                conn.commit()
                                self.push_data(asset.rtuid, asset.name, asset.context, value, asset.unit)
                                conn.close()
            except Exception, excpt:
                print "Error logging sensor data.", excpt

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

    def push_data(self, rtu_id, asset_name, asset_context, value, unit):
        try:
            client = InfluxDBClient('138.197.74.74', 8086, 'early', 'adopter')
            dbs = client.get_list_database()
            found = False
            for item in dbs:
                if asset_context in item:
                    found = True

            if found is False:
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
            logging.getLogger(sm_logger).info("Wrote to analytic database: " + str(json_body))
        except Exception, excpt:
            logging.getLogger(sm_logger).exception('Error writing to analytic database: %s', excpt)

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
        logging.getLogger(sm_logger).info("Executed " + job.job_name + " on " + job.rtuid)
        conn = sqlite3.connect('hapi_history.db')
        c=conn.cursor()
        c.execute(command)
        conn.commit()
        conn.close()

    def log_alert_condition(self, alert):
        try:
            timestamp = '"' + str(datetime.datetime.now()) + '"'
            command = "INSERT INTO alert_log (asset_id, value, timestamp) VALUES (" + str(alert.asset_id) + ", " + timestamp + ", " + str(alert.value) + ")"
            print command
            conn = sqlite3.connect('hapi_history.db')
            c=conn.cursor()
            c.execute(command)
            conn.commit()
            conn.close()
        except Exception, excpt:
            print "Error logging alert condition.", excpt

    def send_alert_condition(self, site, asset, alert, alert_param):
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
        try:
            conn = sqlite3.connect('hapi_core.db')
            c=conn.cursor()
            sql = "SELECT asset_id, lower_threshold, upper_threshold, message, response_type FROM alert_params;"
            rows = c.execute(sql)
            for field in rows:
                alert_param = AlertParam()
                alert_param.asset_id = field[0]
                alert_param.lower_threshold = float(field[1])
                alert_param.upper_threshold = float(field[2])
                alert_param.message = field[3]
                alert_param.response_type = field[4]
                alert_params.append(alert_param)
            conn.close()
        except Exception, excpt:
            print "Error loading alert parameters. %s", excpt

        return alert_params

    def execute_command(self, command):
        print "Executing command:", command
        if command.lower() == "status":
            data = '\nMaster Controller Status\n'
            data = data + '  Software Version v' + version + '\n'
            data = data + '  Running on: ' + sys.platform + '\n'
            data = data + '  Encoding: ' + sys.getdefaultencoding() + '\n'
            data = data + '  Python Information\n'
            data = data + '   - Executable: ' + sys.executable + '\n'
            data = data + '   - v' + sys.version[0:7] + '\n'
            data = data + '   - location: ' + sys.executable + '\n'
            data = data + '  Timestamp: ' + str(datetime.datetime.now())[0:19] + '\n'
            uptime = datetime.datetime.now() - self.launch_time
            days = uptime.days
            hours = int(divmod(uptime.seconds, 86400)[1] / 3600)
            minutes = int(divmod(uptime.seconds, 3600)[1] / 60)
            uptime_str = "This Smart Module has been online for " + str(days) + " days, " + str(hours) + " hours and " + str(minutes) + " minutes."
            data = data + '  Uptime: ' + uptime_str + '\n'
            data = data + '###\n'
            self.comm.send("STATUS", data)

class Scheduler(object):
    def __init__(self):
        self.running = True
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
            seq_result.put("Running " + row[0] + ":" + row[2] + "(" + job.command + ")" + " on " + job.rtuid + " at " + job_rtu.address + ".")
            command = row[1].encode("ascii")
            timeout = int(row[3])
            self.site.comm.send("COMMAND/" + job.rtuid, command)
            time.sleep(timeout)

    def load_interval_schedule(self):
        job_list = []
        logging.getLogger(sm_logger).info("Loading Schedule Data...")
        try:
            conn = sqlite3.connect('hapi_core.db')
            c=conn.cursor()

            db_jobs = c.execute("SELECT job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled, sequence, timeout FROM interval_schedule;")
            for row in db_jobs:
                job = Scheduler.IntervalJob()
                job.job_id = row[0]
                job.job_name = row[1]
                job.rtuid = row[2]
                job.command = row[3].encode("ascii")
                job.time_unit = row[4]
                job.interval = row[5]
                job.at_time = row[6]
                job.enabled = row[7]
                job.sequence = row[8]
                job.timeout = row[9]
                job_list.append(job)
            conn.close()
            logging.getLogger(sm_logger).info("Schedule Data Loaded.")
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error loading interval_schedule. %s", excpt)

        return job_list

    def prepare_jobs(self, jobs):
        for job in jobs:
            if job.time_unit.lower() == "month":
                if job.interval > -1:
                    #schedule.every(job.interval).months.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading monthly job: " + job.job_name)
            elif job.time_unit.lower() == "week":
                if job.interval > -1:
                    schedule.every(job.interval).weeks.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading weekly job: " + job.job_name)
            elif job.time_unit.lower() == "day":
                if job.interval > -1:
                    schedule.every(job.interval).days.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading daily job: " + job.job_name)
                else:
                    schedule.every().day.at(job.at_time).do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading time-based job: " + job.job_name)
            elif job.time_unit.lower() == "hour":
                if job.interval > -1:
                    schedule.every(job.interval).hours.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading hourly job: " + job.job_name)
            elif job.time_unit.lower() == "minute":
                if job.interval > -1:
                    schedule.every(job.interval).minutes.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading minutes job: " + job.job_name)
                else:
                    schedule.every().minute.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading minute job: " + job.job_name)
            elif job.time_unit.lower() == "second":
                if job.interval > -1:
                    schedule.every(job.interval).seconds.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading seconds job: " + job.job_name)
                else:
                    schedule.every().second.do(self.run_job, job)
                    logging.getLogger(sm_logger).info("  Loading second job: " + job.job_name)

    def run_job(self, job):
        return
        if self.running == True:
            response = ""
            job_rtu = None

            if job.enabled == 1:
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
                        self.site.log_sensor_data(response, True)
                    except Exception, excpt:
                        error = "Error running job " + job.job_name + " on " + job_rtu.rtuid + ": " + excpt
                        logging.getLogger(sm_logger).exception(error)
                else:
                    try:
                        for rtu_el in self.site.rtus:
                            if rtu_el.rtuid == job.rtuid:
                                if rtu_el.online == 1:
                                    job_rtu = rtu_el

                            if str.strip(job.sequence) != "":
                                if (job_rtu != None):
                                    print 'Running sequence', job.sequence, "on", job.rtuid
                                    conn = sqlite3.connect('hapi_core.db')
                                    c=conn.cursor()
                                    seq_jobs = c.execute('SELECT name, command, step_name, timeout FROM sequence WHERE name = "' + job.sequence + '" ORDER BY step ;')
                                    print "len(seq_jobs) = "  + str(len(seq_jobs))
                                    p = Process(target=self.process_sequence, args=(seq_jobs, job, job_rtu, seq_result,))
                                    p.start()
                                    conn.close()
                            else:
                                print 'Running command', job.command
                                # Check pre-defined jobs
                                if (job.job_name == "Log Data"):
                                    self.site.comm.send("QUERY/#", "query")
                                    # self.site.log_sensor_data(response, False, self.logger)

                                elif (job.job_name == "Log Status"):
                                    self.site.comm.send("REPORT/#", "report")

                                else:
                                    if (job_rtu != None):
                                        self.site.comm.send("COMMAND/" + job.rtuid, job.command)

                                log_command(job)

                    except Exception, excpt:
                        logging.getLogger(sm_logger).exception('Error running job: %s', excpt)

class DataSync(object):
    def read_db_version(self):
        version = ""
        try:
            conn = sqlite3.connect('hapi_core.db')
            c=conn.cursor()
            sql = "SELECT version FROM db_info;"
            data = c.execute(sql)
            for element in data:
                version = dateutil.parser.parse(element[0])
            conn.close()
            logging.getLogger(sm_logger).info("Read database version: " + str(version))
            return str(version)
        except Exception, excpt:
            logging.getLogger(sm_logger).info("Error reading database version: %s", excpt)

    def write_db_version(self):
        try:
            version = str(datetime.datetime.now().isoformat)
            command = 'UPDATE db_info SET version = "' + version + '";'
            conn = sqlite3.connect('hapi_core.db')
            c=conn.cursor()
            c.execute(command)
            conn.commit()
            conn.close()
            logging.getLogger(sm_logger).info("Wrote database version: " + version)
        except Exception, excpt:
            logging.getLogger(sm_logger).info("Error writing database version: %s", excpt)

    def publish_core_db(self, comm):
        try:
            f = open("hapi_core.db")
            data = f.read()
            byteArray = bytes(data)
            comm.unsubscribe("SYNCHRONIZE/DATA")
            comm.send("SYNCHRONIZE/DATA", byteArray)
            time.sleep(1)
            comm.subscribe("SYNCHRONIZE/DATA")
            logging.getLogger(sm_logger).info("Published database.")
        except Exception, excpt:
            logging.getLogger(sm_logger).info("Error publishing database: %s", excpt)

    def synchronize_core_db(self, data):
        try:
            with open('hapi_core.db', 'wb') as fd:
                fd.write(data)

            logging.getLogger(sm_logger).info("Synchronized database.")
        except Exception, excpt:
            logging.getLogger(sm_logger).info("Error synchronizing database: %s", excpt)


# class HAPIListener(TelnetHandler):
#     global launch_time
#     launch_time = datetime.datetime.now()

#     PROMPT = site.name + "> "

#     # def __init__(self, *args):
#     #     print "Listener Init"
#     #     print args

#     @command('abc')
#     def command_abc(self, params):
#         '''<context of assets for data>
#         Gets Asset data By Context.

#         '''
#         if len(params) > 0:
#             context = params[0]
#             self.writeresponse("Gathering asset data by context: " + context)
#             data = site.assets_by_context(context)
#             result = "{"
#             for asset in data:
#                 result = result + '"' + asset.name + '":"' + asset.value + '"' + ','
#             result = result + "}"
#             self.writeresponse(result)
#         else:
#             self.writeresponse('No context provided.')

#     @command('asset')
#     def command_asset(self, params):
#         '''<get value for named asset>
#         Gets the current value for the named asset.
#         '''
#         asset = ""

#         for param in params:
#             asset = asset + " " + param.encode('utf-8').strip()

#         asset = asset.lower().strip()
#         print "MC:Listener:asset:", asset
#         value = site.get_asset_value(asset)

#         print "Sending asset", params[0], value
#         self.writeline(value)

#     @command('assets')
#     def command_assets(self, params):
#         '''<get all asset names>
#         Gets all Asset names.

#         '''
#         self.writeline(str(site.assets()))

#     @command('cmd')
#     def command_cmd(self, params):
#         '''<command to be run on connected RTU>
#         Sends a command to the connected RTU

#         '''
#         if the_rtu == None:
#             self.writeresponse("You are not connected to an RTU.")
#         else:
#             command = params[0]

#             self.writeresponse("Executing " + command + " on " + the_rtu.rtuid + "...")
#             target_rtu = rtu_comm.RTUCommunicator()
#             response = target_rtu.send_to_rtu(the_rtu.address, 80, 1, command)
#             self.writeresponse(response)
#             job = IntervalJob()
#             job.job_name = command
#             job.rtuid = the_rtu.rtuid
#             log_command(job)

#     @command('continue')
#     def command_continue(self, params):
#         '''
#         Starts the Master Controller's Scheduler

#         '''
#         f = open("ipc.txt", "wb")
#         f.write("run")
#         f.close()

#     @command('pause')
#     def command_pause(self, params):
#         '''
#         Pauses the Master Controller's Scheduler

#         '''
#         f = open("ipc.txt", "wb")
#         f.write("pause")
#         f.close()

#     @command('run')
#     def command_run(self, params):
#         '''
#         Starts the Master Controller's Scheduler

#         '''
#         if the_rtu == None:
#             self.writeresponse("You are not connected to an RTU.")
#         else:
#             command = params[0]

#             scheduler = Scheduler()
#             scheduler.site = site
#             scheduler.logger = self.logger

#             print "Running", params[0], params[1], "on", the_rtu.rtuid
#             job = IntervalJob()
#             job.job_name = "User-defined"
#             job.enabled = 1
#             job.rtuid = the_rtu.rtuid

#             if params[0] == "command":
#                 job.command = params[1]
#             elif params[0] == "sequence":
#                 job.sequence = params[1]

#             print "Passing job to the scheduler."
#             scheduler.run_job(job)

#     @command('stop')
#     def command_stop(self, params):
#         '''
#         Kills the HAPI listener service

#         '''
#         f = open("ipc.txt", "wb")
#         f.write("stop")
#         f.close()

#     @command('turnoff')
#     def command_turnoff(self, params):
#         '''<Turn Off Asset>
#         Turn off the named asset.
#         '''
#         asset = ""

#         for param in params:
#             asset = asset + " " + param.encode('utf-8').strip()

#         asset = asset.lower().strip()
#         print "MC:Listener:asset:", asset
#         value = site.set_asset_value(asset, "1")

#         print "Sending asset", params[0], value
#         self.writeline(value)

#     @command('turnon')
#     def command_turnon(self, params):
#         '''<Turn On Asset>
#         Turn on the named asset.
#         '''
#         asset = ""

#         for param in params:
#             asset = asset + " " + param.encode('utf-8').strip()

#         asset = asset.lower().strip()
#         print "MC:Listener:asset:", asset
#         value = site.set_asset_value(asset, "0")

#         print "Sending asset", params[0], value
#         self.writeline(value)

def main():
    #max_log_size = 1000000

    # Setup Logging
    logger_level = logging.DEBUG
    logger = logging.getLogger(sm_logger)
    logger.setLevel(logger_level)

    # create logging file handler
    file_handler = logging.FileHandler('hapi_sm.log', 'a')
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
        smart_module = SmartModule()
        smart_module.discover()
        smart_module.load_site_data()

        #ACCOUNT_SID = <your twilio account SID here>
        #AUTH_TOKEN = <your twilio account token here>
        #client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        #client.messages.create(to=<+receiving number>, from_=<+sending number>, body="HAPI Master Controller is online.", )

        # problem_rtus = validate_pin_modes(rtus)
    except Exception, excpt:
        logger.exception("Error loading site information. %s", excpt)

    # try:
    #     listener = HAPIListener()

    # except Exception, excpt:
    #     logger.exception("Error loading Listener. %s", excpt)

    # try:
    #     logger.info("Initializing Listener...")
    #     listener_parent_conn, listener_child_conn = Pipe()
    #     p = Process(target=run_listener, args=(listener_child_conn,))
    #     p.start()
    #     logger.info("Listener is online.")
    # except Exception, excpt:
    #     logger.exception("Error loading initializing listener. %s", excpt)
    #smart_module.comm.client.loop(timeout=1.0, max_packets=1)
    #smart_module.comm.client.loop_start()
    while 1:
        #print listener_parent_conn.recv()
        try:
            
            time.sleep(0.5)
            # if count % 60 == 0:
            #     print ".",
            # time.sleep(5)
            # count = count + 5

            # schedule.run_pending()

            # if os.path.isfile("ipc.txt"):
            #     f = open("ipc.txt", "rb")
            #     data = f.read()
            #     f.close()
            #     open("ipc.txt", 'w').close()
            #     if data != "":
            #         if data == "run":
            #             scheduler.running = True
            #             logger.info("The scheduler is running.")
            #         elif data == "pause":
            #             logger.info("The scheduler has been paused.")
            #             scheduler.running = False
            #         else:
            #             logger.info("Received from Listener: " + data)
        except Exception, excpt:
            logger.exception("Error in Smart Module main loop. %s", excpt)
            break

if __name__ == "__main__":
    #main(sys.argv[1:])
    main()
