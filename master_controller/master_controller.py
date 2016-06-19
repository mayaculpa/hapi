import sqlite3
import telnetlib
import sys
import operator
from time import sleep
import schedule


rtus = []

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
    pinmode_list = []
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

def load_interval_schedule():
    job_list = []
    try:
        conn = sqlite3.connect('hapi.db')
        c=conn.cursor()

        db_jobs = c.execute("SELECT job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled FROM schedule;")
        for row in db_jobs:
            job = Job()
            job.job_id = row[0]
            job.job_name = row[1]
            job.rtuid = row[2]
            job.command = row[3]
            job.time_unit = row[4]
            job.interval = row[5]
            job.at_time = row[6]
            job.enabled = row[7]
            job_list.append(job)

        conn.close()
    except Exception, excpt:
        print "Error loading rtu table. %s", excpt

    return job_list

def validate_environment():
    rtus = get_rtu_list()
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
            print "Pin mode from rtu:", pmode_from_rtu

            pmode_from_db = ""
            for db_pin_mode in sorted(rtu.pin_modes.values(), key=operator.attrgetter('pos')):
                pmode_from_db += db_pin_mode.pin
                pmode_from_db += str(db_pin_mode.mode)

            print "Pin mode from ref:", pmode_from_db

            pin_mode_ok = True
            for i in range(0, len(pmode_from_rtu) - 2):
                if pmode_from_rtu[i] != pmode_from_db[i]:
                    pin_mode_ok = False
                    print "Pin mode mismatch (rtu:db:pos)", pmode_from_rtu[i], ":", pmode_from_db[i], ":", i/2
                #print pmode_from_rtu[i], pmode_from_db[i]
            if pin_mode_ok == False:
                print "RTU", rtu.rtuid, "has a non-congruent pin mode."
                problem_rtus.append(rtu)
            else:
                print "Pin mode congruence between", rtu.rtuid, "and the database."

    return problem_rtus

def run_job(job):
    for rtu_el in rtus:
        if rtu_el.rtuid == job.rtuid:
            job_rtu = rtu_el

    if job_rtu != None:
        try:
            print "Connecting to", job_rtu.rtuid, "at", job_rtu.address
            tn = telnetlib.Telnet()
            tn.open(job_rtu.address, 80, 5)
            print "Connected."
            print "Executing command", job.command
            tn.write(job.command + '\n')
            response = tn.read_all()
            print response
            tn.close()
        except Exception, excpt:
            print "Error communicating with rtu", job_rtu.rtuid, excpt

def prepare_jobs(jobs):
    for job in jobs:
        if job.time_unit.lower() == "month":
            if job.interval > -1:
                schedule.every(job.interval).months.do(run_job, job)
        elif job.time_unit.lower() == "week":
            if job.interval > -1:
                schedule.every(job.interval).weeks.do(run_job, job)
        elif job.time_unit.lower() == "day":
            if job.interval > -1:
                schedule.every(job.interval).days.do(run_job, job)
            else:
                schedule.every().day.at(job.at_time).do(run_job, job)
        elif job.time_unit.lower() == "hour":
            if job.interval > -1:
                schedule.every(job.interval).hours.do(run_job, job)
        elif job.time_unit.lower() == "minute":
            if job.interval > -1:
                schedule.every(job.interval).minutes.do(run_job, job)
            else:
                schedule.every().minute.do(run_job, job)

def main(argv):
    problem_rtus = validate_environment()
    for rtu in problem_rtus:
        print "RTU", rtu.rtuid, "could not be found or has incongruent pin modes."

    jobs = load_interval_schedule()
    prepare_jobs(jobs)

    print len(jobs)

     # try:
     #      opts, args = getopt.getopt(argv,"hm:")
     # except getopt.GetoptError:
     #      print("command_broker.py -m <mode>")
     #      sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
