#!/bin/python

# HAPI Project
# Smart Module Status is responsible for fetching information from the system
# Author: Pedro Freitas
# Release: 0.1-alpha
# Copyright 2017 Maya Culpa, LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Done
# 1. Memory:
#   1.1. Memory used;
#   1.2. Memory available;
# 2. Disk:
#   2.1. Disk used;
#   2.2. Disk available.
# 3. Networking
#   3.2. Network sent packets; and
#   3.3. Network received packets.
# 4. Boot:
#   4.1. Boot time.
# 5. CPU:
#   5.1. CPU Process time
# TODO:
#   3.1. Network active connections;
#   1.3. Memory Process time.

import psutil
"""
This is a wrapper on psutil to provide system information
in a simple JSON way. If run stand-alone, print all information.
"""

class SystemStatus:
    """ Small class to handle system information """

    def __init__(self):
        self.cpu = { "percentage": 0 }
        self.boot = { "time": 0 }
        self.memory = { "used": 0, "free": 0 }
        self.network = { "packet_sent": 0, "packet_recv": 0 }
        self.disk = { "total": 0, "used": 0, "free": 0 }

    def __str__(self):
        json_string = str('"memory": {}, "cpu": {}, "boot": {}, "network": {}, "disk": {}')
        json_info = '{' + json_string.format(self.memory, self.cpu, self.boot, self.network, self.disk) + '}'
        return json_info

    def update(self):
        """ Function to update the entire class information """
        self.cpu["percentage"] = psutil.cpu_percent(interval=0.7)
        self.boot["time"] = psutil.boot_time()
        # Fetch all information about Memory in a temp variable
        # then assign each value to a specific key (psutil usually returns
        # a named tuple
        tempmemoryinfo = psutil.virtual_memory()
        self.memory["used"] = tempmemoryinfo[3]
        self.memory["free"] = tempmemoryinfo[4]
        tempnetworkinfo = psutil.net_io_counters()
        self.network["packet_sent"] = tempnetworkinfo[2]
        self.network["packet_recv"] = tempnetworkinfo[3]
        tempdiskinfo = psutil.disk_usage('/')
        self.disk["total"] = tempdiskinfo[0]
        self.disk["used"] = tempdiskinfo[1]
        self.disk["free"] = tempdiskinfo[2]

if __name__ == "__main__":
    """ If run as main, print in JSON system information """
    ss = SystemStatus()
    ss.update()
    print(ss)
