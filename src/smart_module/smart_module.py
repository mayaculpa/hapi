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

import sqlite3                                      # https://www.sqlite.org/index.html
import sys
import time
import schedule                                     # sudo pip install schedule
import datetime
#import dateutil.parser
import urllib2
import json
import subprocess
import communicator
import socket
import psutil
import importlib
import codecs
from multiprocessing import Process
import logging
#from twilio.rest import TwilioRestClient            # sudo pip install twilio
from influxdb import InfluxDBClient
from status import SystemStatus
import asset_interface
from alert import Alert
from utilities import *

reload(sys)

class Asset(object):
    def __init__(self):
        self.id = "1"
        self.name = "Indoor Temperature"
        self.unit = "C"
        self.type = "wt"
        self.virtual = 0
        self.context = "Environment"
        self.system = "Test"
        self.enabled = True
        self.value = None

class AssetInterface(object):
    def __init__(self, asset_type):
        # determine the correct asset library and import it
        self.asset_lib = importlib.import_module("asset_" + str(asset_type))

    def read_value():
        return AssetImpl().read_value()

class SmartModule(object):
    """Represents a HAPI Smart Module (Implementation).

    Attributes:
        id: ID of the site
        name: Name of the site
        wunder_key: Weather Underground key to be used
        operator: Name of the primary site operator
        email: Email address of the primary site operator
        phone: Phone number of the primary site operator
        location: Location or Address of the site
    """

    def __init__(self):
        #logging.getLogger(SM_LOGGER).info("Smart Module Initializing.")
        self.comm = communicator.Communicator()
        self.data_sync = DataSync()
        self.comm.smart_module = self
        self.id = ""
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
        self.asset = Asset()
        self.scheduler = None
        self.hostname = ""
        self.lastStatus = ""
        self.influxhost = {"host": "138.197.74.74", "port": 8086, "user": "early",
                           "pass": "adopter"}
        self.dbconn = DatabaseConn(connect=True)
        self.log = logging.getLogger(SM_LOGGER)
        #logging.getLogger(SM_LOGGER).info("Smart Module initialization complete.")

    def discover(self):
        self.log.info("Performing Discovery...")
        subprocess.call("sudo ./host-hapi.sh", shell=True)
        self.comm.smart_module = self
        self.comm.client.loop_start()
        self.comm.connect()
        t_end = time.time() + 10
        while (time.time() < t_end) and not self.comm.is_connected:
            time.sleep(1)

        self.comm.subscribe("SCHEDULER/RESPONSE")
        self.comm.send("SCHEDULER/QUERY", "Where are you?")

        self.hostname = socket.gethostname()
        self.comm.send("ANNOUNCE", self.hostname + " is online.")

        t_end = time.time() + 2
        while (time.time() < t_end) and not self.comm.is_connected:
            time.sleep(1)

        if not self.comm.scheduler_found:
            # Loading scheduled jobs
            try:
                self.log.info("No Scheduler found. Becoming the Scheduler.")
                self.scheduler = Scheduler()
                self.scheduler.smart_module = self
                # running is always True after object creation. Should we remove it?
                # self.scheduler.running = True
                self.scheduler.prepare_jobs(self.scheduler.load_schedule())
                self.comm.scheduler_found = True
                self.comm.subscribe("SCHEDULER/QUERY")
                self.comm.unsubscribe("SCHEDULER/RESPONSE")
                self.comm.subscribe("STATUS/RESPONSE")
                self.comm.send("SCHEDULER/RESPONSE", socket.gethostname() + ".local")
                self.comm.send("ANNOUNCE", socket.gethostname() + ".local is running the Scheduler.")
                self.log.info("Scheduler program loaded.")
            except Exception, excpt:
                self.log.exception("Error initializing scheduler. %s", excpt)

    def load_site_data(self):
        field_names = '''
            id
            name
            wunder_key
            operator
            email
            phone
            location
            longitude
            latitude
            twilio_acct_sid
            twilio_auth_token
        '''.split()
        try:
            #conn = sqlite3.connect('hapi_core.db')
            #c = conn.cursor()
            sql = 'SELECT {field_names} FROM site LIMIT 1;'.format(
                field_names=', '.join(field_names))
            db_elements = self.dbconn.cursor.execute(sql)
            for row in db_elements:
                for field_name, field_value in zip(field_names, row):
                    setattr(self, field_name, field_value)
            self.log.info("Site data loaded.")
        except Exception, excpt:
            self.log.exception("Error loading site data: %s", excpt)

    def connect_influx(self, asset_context):
        """Connect to InfluxDB server and searches for the database in 'asset_context'.
           Return the connection to the database or create it if necessary."""

        influxcon = InfluxDBClient(self.influxhost["host"], self.influxhost["port"],
                                   self.influxhost["user"], self.influxhost["pass"])
        databases = influxcon.get_list_database()
        found = False
        for db in databases:
            if asset_context in db:
                found = True

        if found is False:
            influxcon.query("CREATE DATABASE {0}".format('"' + asset_context + '"'))

        influxcon = InfluxDBClient(self.influxhost["host"], self.influxhost["port"],
                                   self.influxhost["user"], self.influxhost["pass"], asset_context)
        return influxcon

    def push_sysinfo(self, asset_context, information):
        """Push System Status (stats) information to InfluxDB server."""
        # We should consider, somehow, a better approach
        timestamp = datetime.datetime.now()
        conn = self.connect_influx(asset_context)
        cpuinfo = [{"measurement": "cpu",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "percentage",
                        "load": information.cpu["percentage"]
                    }
                  }]
        meminfo = [{"measurement": "memory",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "bytes",
                        "free": information.memory["free"],
                        "used": information.memory["used"],
                        "cached": information.memory["cached"]
                    }
                  }]
        netinfo = [{"measurement": "network",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "packets",
                        "packet_recv": information.network["packet_recv"],
                        "packet_sent": information.network["packet_sent"]
                    }
                  }]
        botinfo = [{"measurement": "boot",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "timestamp",
                        "date": information.boot
                    }
                  }]
        diskinf = [{"measurement": "disk",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "bytes",
                        "total": information.disk["total"],
                        "free": information.disk["free"],
                        "used": information.disk["used"]
                    }
                  }]
        ctsinfo = [{"measurement": "clients",
                    "tags": {
                        "asset": self.name
                    },
                    "time": timestamp,
                    "fields": {
                        "unit": "integer",
                        "clients": information.clients
                    }
                  }]
        json = cpuinfo + meminfo + netinfo + botinfo + diskinf + ctsinfo
        conn.write_points(json)

    def get_status(self, brokerconnections):
        """Fetch system information (stats) and return a list with a single dictionary (JSON)."""
        try:
            sysinfo = SystemStatus(update=True)
            sysinfo.clients = brokerconnections
            return sysinfo
        except Exception, excpt:
            self.log.exception("Error getting System Status: %s", excpt)

    def on_query_status(self):
        """It'll be called by the Scheduler to ask for System Status information."""
        self.comm.send("STATUS/QUERY", "I might need to know how you are!")

    def get_asset_data(self):
        value = ""
        try:
            #ai = asset_interface.AssetInterface(self.asset.type)
            # Is this line correct? It needs a parameter
            ai = asset_interface.AssetInterface()
            value = str(ai.read_value())
            self.push_data(self.asset.name, self.asset.context, value, self.asset.unit)
            self.comm.send("RESPONSE/ASSET/" + self.asset.name, value)
        except Exception, excpt:
            self.log.exception("Error getting asset data: %s", excpt)

        return value

    def log_sensor_data(self, data, virtual):
        if not virtual:
            try:
                self.push_data(self.asset.name, self.asset.context, value, asset.unit)
            except Exception, excpt:
                self.log.exception("Error logging sensor data: %s", excpt)
        else:
            # For virtual assets, assume that the data is already parsed JSON
            unit_symbol = {
                'temp_c': 'C',
                'relative_humidity': '%',
                'pressure_mb': 'mb',
            }
            try:
                for factor in ('temp_c', 'relative_humidity', 'pressure_mb'):
                    value = str(data[factor]).replace("%", "")
                    self.push_data(factor, "Environment", value, unit_symbol[factor])

            except Exception, excpt:
                self.log.exception("Error logging sensor data: %s", excpt)

    def push_data(self, asset_name, asset_context, value, unit):
        try:
           #conn = self.connect_influx("138.197.74.74", 8086, "early", "adopter", asset_context)
            conn = self.connect_influx(asset_context)
            json_body = [
                {
                    "measurement": asset_context,
                    "tags": {
                        "site": self.name,
                        "asset": asset_name
                    },
                    "time": str(datetime.datetime.now()),
                    "fields": {
                        "value": value,
                        "unit": unit
                    }
                }
            ]
            conn.write_points(json_body)
            print(json_body)
            self.log.info("Wrote to analytic database: %s", json_body)
        except Exception, excpt:
            self.log.exception('Error writing to analytic database: %s', excpt)

    def get_weather(self):
        response = ""
        url = (
            'http://api.wunderground.com/'
            'api/{key}/conditions/q/{lat},{lon}.json'
        ).format(
            key=self.wunder_key,
            lat=self.latitude,
            lon=self.longitude,
        )
        print(url)
        try:
            f = urllib2.urlopen(url)
            json_string = f.read()
            parsed_json = json.loads(json_string)
            response = parsed_json['current_observation']
            f.close()
        except Exception, excpt:
            print('Error getting weather data.', excpt)
            self.log.exception('Error getting weather data: %s', excpt)
        return response

    def log_command(self, job, result):
        try:
            now = str(datetime.datetime.now())
            command = '''
                INSERT INTO command_log (timestamp, command, result)
                VALUES (?, ?, ?)
            ''', (now, job.name, result)
            self.log.info("Executed %s", job.name)
            conn = sqlite3.connect('hapi_history.db')
            c = conn.cursor()
            c.execute(*command)
            conn.commit()
            conn.close()
        except Exception, excpt:
            self.log.exception("Error logging command: %s", excpt)

    def get_env(self):
        now = datetime.datetime.now()
        uptime = now - self.launch_time
        days = uptime.days
        minutes, seconds = divmod(uptime.seconds, SECONDS_PER_MINUTE)
        hours, minutes = divmod(minutes, MINUTES_PER_HOUR)
        s = ('''
            Master Controller Status
              Software Version v{version}
              Running on: {platform}
              Encoding: {encoding}
              Python Information
               - Executable: {executable}
               - v{sys_version}
               - location: {executable}
              Timestamp: {timestamp}
              Uptime: This Smart Module has been online for '''
                  '''{days} days, {hours} hours and {minutes} minutes.
            ###
        ''').format(
            version=version,
            platform=sys.platform,
            encoding=sys.getdefaultencoding(),
            executable=sys.executable,
            sys_version=sys.version.split()[0],
            timestamp=now.strftime('%Y-%m-%d %H:%M:%S'),
            days=days,
            hours=hours,
            minutes=minutes,
        )
        s = trim(s) + '\n'
        try:
            self.comm.send("ENV/RESPONSE", s)
        except Exception, excpt:
            self.log.exception("Error getting environment data: %s", excpt)

class Scheduler(object):
    def __init__(self):
        self.running = True
        self.smart_module = None
        self.processes = []
        self.dbconn = DatabaseConn(connect=True)
        self.log = logging.getLogger(SM_LOGGER)

    class Job(object):
        def __init__(self):
            self.id = -1
            self.name = ""
            self.asset_id = ""
            self.command = ""
            self.time_unit = ""
            self.interval = -1
            self.at_time = ""
            self.enabled = False
            self.sequence = ""
            self.timeout = 0.0
            self.virtual = False

    def process_sequence(self, seq_jobs, job, job_rtu, seq_result):
        for row in seq_jobs:
            name, command, step_name, timeout = row
            seq_result.put(
                'Running {name}:{step_name}({command}) on {id} at {address}.'.
                format(
                    name=name,
                    step_name=step_name,
                    command=job.command,
                    id=job.rtuid,
                    address=job_rtu.address,
                )
            )
            command = command.encode("ascii")
            timeout = int(timeout)
            self.site.comm.send("COMMAND/" + job.rtuid, command)
            time.sleep(timeout)

    def load_schedule(self):
        jobs = []
        self.log.info("Loading Schedule Data...")
        field_names = '''
            id
            name
            asset_id
            command
            time_unit
            interval
            at_time
            enabled
            sequence
            virtual
        '''.split()
        try:
            #conn = sqlite3.connect('hapi_core.db')
            #c = conn.cursor()
            sql = 'SELECT {field_names} FROM schedule;'.format(
                field_names=', '.join(field_names))
            db_jobs = self.dbconn.cursor.execute(sql)
            for row in db_jobs:
                job = Scheduler.Job()
                for field_name, field_value in zip(field_names, row):
                    setattr(job, field_name, field_value)
                jobs.append(job)
            self.log.info("Schedule Data Loaded.")
        except Exception, excpt:
            self.log.exception("Error loading schedule. %s", excpt)

        return jobs

    def prepare_jobs(self, jobs):
        for job in jobs:
            if job.time_unit.lower() == "month":
                if job.interval > -1:
                    #schedule.every(job.interval).months.do(self.run_job, job)
                    self.log.info("  Loading monthly job: " + job.name)
            elif job.time_unit.lower() == "week":
                if job.interval > -1:
                    schedule.every(job.interval).weeks.do(self.run_job, job)
                    self.log.info("  Loading weekly job: " + job.name)
            elif job.time_unit.lower() == "day":
                if job.interval > -1:
                    schedule.every(job.interval).days.do(self.run_job, job)
                    self.log.info("  Loading daily job: " + job.name)
                else:
                    schedule.every().day.at(job.at_time).do(self.run_job, job)
                    self.log.info("  Loading time-based job: " + job.name)
            elif job.time_unit.lower() == "hour":
                if job.interval > -1:
                    schedule.every(job.interval).hours.do(self.run_job, job)
                    self.log.info("  Loading hourly job: " + job.name)
            elif job.time_unit.lower() == "minute":
                if job.interval > -1:
                    schedule.every(job.interval).minutes.do(self.run_job, job)
                    self.log.info("  Loading minutes job: " + job.name)
                else:
                    schedule.every().minute.do(self.run_job, job)
                    self.log.info("  Loading minute job: " + job.name)
            elif job.time_unit.lower() == "second":
                if job.interval > -1:
                    schedule.every(job.interval).seconds.do(self.run_job, job)
                    self.log.info("  Loading seconds job: " + job.name)
                else:
                    schedule.every().second.do(self.run_job, job)
                    self.log.info("  Loading second job: " + job.name)

    def run_job(self, job):
        if not self.running or not job.enabled:
            return

        response = ""
        job_rtu = None

        if job.sequence is None:
            job.sequence = ""

        if job.virtual:
            print('Running virtual job:', job.name, job.command)
            try:
                response = eval(job.command)
                self.smart_module.log_sensor_data(response, True)
            except Exception, excpt:
                self.log.exception("Error running job. %s", excpt)
        else:
            try:
                if job.sequence != "":
                    print('Running sequence', job.sequence)
                    #conn = sqlite3.connect('hapi_core.db')
                    #c = conn.cursor()
                    command = '''
                        SELECT name, command, step_name, timeout
                        FROM sequence
                        WHERE name=?
                        ORDER BY step ;
                    ''', (job.sequence,)
                    seq_jobs = self.dbconn.cursor.execute(*command)
                    #print('len(seq_jobs) =', len(seq_jobs))
                    p = Process(target=self.process_sequence, args=(seq_jobs, job, job_rtu, seq_result,))
                    p.start()
                else:
                    print('Running command', job.command)
                    # Check pre-defined jobs
                    if job.name == "Log Data":
                        self.site.comm.send("QUERY/#", "query")
                        # self.site.log_sensor_data(response, False, self.logger)

                    elif job.name == "Log Status":
                        self.site.comm.send("REPORT/#", "report")

                    else:
                        eval(job.command)
                        # if job_rtu is not None:  #??? job_rtu is always None. Bug?
                        #     self.site.comm.send("COMMAND/" + job.rtuid, job.command)

                    #self.log_command(job, "")

            except Exception, excpt:
                self.log.exception('Error running job: %s', excpt)

class DataSync(object):
    @staticmethod
    def read_db_version():
        version = ""
        try:
            conn = sqlite3.connect('hapi_core.db')
            c = conn.cursor()
            sql = "SELECT data_version FROM db_info;"
            data = c.execute(sql)
            for element in data:
                version = element[0]
            conn.close()
            logging.getLogger(SM_LOGGER).info("Read database version: %s", version)
            return version
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).info("Error reading database version: %s", excpt)

    @staticmethod
    def write_db_version():
        try:
            version = datetime.datetime.now().isoformat()
            command = 'UPDATE db_info SET data_version = ?;', (version,)
            conn = sqlite3.connect('hapi_core.db')
            c = conn.cursor()
            c.execute(*command)
            conn.commit()
            conn.close()
            logging.getLogger(SM_LOGGER).info("Wrote database version: %s", version)
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).info("Error writing database version: %s", excpt)

    @staticmethod
    def publish_core_db(comm):
        try:
            subprocess.call("sqlite3 hapi_core.db .dump > output.sql", shell=True)
            f = codecs.open('output.sql', 'r', encoding='ISO-8859-1')
            data = f.read()
            byteArray = bytearray(data.encode('utf-8'))
            comm.unsubscribe("SYNCHRONIZE/DATA")
            comm.send("SYNCHRONIZE/DATA", byteArray)
            #comm.subscribe("SYNCHRONIZE/DATA")
            logging.getLogger(SM_LOGGER).info("Published database.")
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).info("Error publishing database: %s", excpt)

    def synchronize_core_db(self, data):
        try:
            with codecs.open("incoming.sql", "w") as fd:
                fd.write(data)

            subprocess.call('sqlite3 -init incoming.sql hapi_new.db ""', shell=True)

            logging.getLogger(SM_LOGGER).info("Synchronized database.")
        except Exception, excpt:
            logging.getLogger(SM_LOGGER).info("Error synchronizing database: %s", excpt)

def main():
    #max_log_size = 1000000

    # Setup Logging
    logger_level = logging.DEBUG
    logger = logging.getLogger(SM_LOGGER)
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

    except Exception, excpt:
        logger.exception("Error initializing Smart Module. %s", excpt)

    while 1:
        try:
            time.sleep(0.5)
            schedule.run_pending()

        except Exception, excpt:
            logger.exception("Error in Smart Module main loop. %s", excpt)
            break

if __name__ == "__main__":
    main()

# class HAPIListener(TelnetHandler):
#     @command('abc')
#     def command_abc(self, params):
#         '''<context of assets for data>
#         Gets Asset data By Context.
#         '''
#         if params:
#             context = params[0]
#             self.writeresponse("Gathering asset data by context: " + context)
#             data = site.assets_by_context(context)
#             result = ''.join(
#                 '"{a.name}":"{a.value}",'.format(a=asset)
#                 for asset in data
#             )
#             result = '{%s}' % result
#         else:
#             result = 'No context provided.'
#         self.writeresponse(result)

#     @command('cmd')
#     def command_cmd(self, params):
#         '''<command to be run on connected RTU>
#         Sends a command to the connected RTU

#         '''
#         if the_rtu is None:
#             self.writeresponse("You are not connected to an RTU.")
#         else:
#             command = params[0]

#             self.writeresponse("Executing " + command + " on " + the_rtu.rtuid + "...")
#             target_rtu = rtu_comm.RTUCommunicator()
#             response = target_rtu.send_to_rtu(the_rtu.address, 80, 1, command)
#             self.writeresponse(response)
#             job = IntervalJob()
#             job.name = command
#             job.rtuid = the_rtu.rtuid
#             log_command(job)

#     @command('continue')
#     def command_continue(self, params):
#         '''
#         Starts the Master Controller's Scheduler

#         '''
#         with open('ipc.txt', 'wb') as f:
#             f.write('run')

#     @command('pause')
#     def command_pause(self, params):
#         '''
#         Pauses the Master Controller's Scheduler

#         '''
#         with open('ipc.txt', 'wb') as f:
#             f.write('pause')

#     @command('run')
#     def command_run(self, params):
#         '''
#         Starts the Master Controller's Scheduler

#         '''
#         if the_rtu is None:
#             self.writeresponse("You are not connected to an RTU.")
#         else:
#             command, value = params[:2]

#             scheduler = Scheduler()
#             scheduler.site = site
#             scheduler.logger = self.logger

#             print('Running', command, value, 'on', the_rtu.rtuid)
#             job = IntervalJob()
#             job.name = "User-defined"
#             job.enabled = True
#             job.rtuid = the_rtu.rtuid

#             if command in ('command', 'sequence'):
#                 setattr(job, command, value)

#             print('Passing job to the scheduler.')
#             scheduler.run_job(job)

#     @command('stop')
#     def command_stop(self, params):
#         '''
#         Kills the HAPI listener service

#         '''
#         with open('ipc.txt', 'wb') as f:
#             f.write('stop')

#     @command('turnoff')
#     def command_turnoff(self, params):
#         '''<Turn Off Asset>
#         Turn off the named asset.
#         '''
#         asset = ' '.join(param.encode('utf-8').strip() for param in params)
#         asset = asset.lower()

#         print('MC:Listener:asset:', asset)
#         value = site.set_asset_value(asset, "1")

#         print('Sending asset', params[0], value)
#         self.writeline(value)

#     @command('turnon')
#     def command_turnon(self, params):
#         '''<Turn On Asset>
#         Turn on the named asset.
#         '''
#         asset = ' '.join(param.encode('utf-8').strip() for param in params)
#         asset = asset.lower()

#         print('MC:Listener:asset:', asset)
#         value = site.set_asset_value(asset, "0")

#         print('Sending asset', params[0], value)
#         self.writeline(value)

