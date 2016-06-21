# -*- coding: utf-8 -*-

import sqlite3
import telnetlib
import sys
import operator
import time
import schedule
import datetime

rtus = []
reload(sys)
sys.setdefaultencoding('UTF-8')

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

def validate_environment(rtus):
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
                print "Pin mode congruence between", rtu.rtuid, "and the database."

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
    job_rtu = None
    for rtu_el in rtus:
        if rtu_el.rtuid == job.rtuid:
            job_rtu = rtu_el
        else:
            print rtu_el.rtuid != job.rtuid

    if job_rtu != None:
        try:
            print "Connecting to", job_rtu.rtuid, "at", job_rtu.address
            tn = telnetlib.Telnet()
            tn.open(job_rtu.address, 80, 5)
            print "Executing command", job.command
            command = job.command
            tn.write(command)
            response = tn.read_all()
            print response
            tn.close()
            if (job.job_name == "Log Data"):
                conn = sqlite3.connect('hapi.db')
                c=conn.cursor()
                response = response.replace('"', '')
                command = 'INSERT INTO log (rtuid, timestamp, data) VALUES (\"' + job.rtuid + '\",\"' + str(datetime.datetime.now()) + '\",\"' + response + '\")'
                print command
                c.execute(command)
                conn.commit()
                conn.close()

            print "RTU: ", job_rtu.rtuid, "ran", job.command
        except Exception, excpt:
            print "Error running job", job.job_name, "on", job_rtu.rtuid, excpt

def main(argv):
    global rtus
    rtus = get_rtu_list()
    problem_rtus = validate_environment(rtus)
    for rtu in problem_rtus:
        print "RTU", rtu.rtuid, "could not be found or has incongruent pin modes."

    print "There are", len(rtus), "RTUs."
    jobs = load_interval_schedule()
    prepare_jobs(jobs)

    #print len(jobs)
    while 1:
        schedule.run_pending()
        time.sleep(1)

     # try:
     #      opts, args = getopt.getopt(argv,"hm:")
     # except getopt.GetoptError:
     #      print("command_broker.py -m <mode>")
     #      sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
