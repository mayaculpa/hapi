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
"""
This is a wrapper on psutil to provide system information
in a simple JSON way. If run stand-alone, print all information.
"""

# Todo:
#   3.1. Network active connections;
#   1.3. Memory Process time.

import time
import psutil

class SystemStatus:
    """ Small class to handle system information """

    def __init__(self, update=False):
        """ If update == True, create the object and fetch all data """
        self.cpu = {"percentage": 0}
        self.bootdate = 0
        self.memory = {"used": 0, "free": 0}
        self.network = {"packet_sent": 0, "packet_recv": 0}
        self.disk = {"total": 0, "used": 0, "free": 0}
        self.timestamp = 0
        if update is True:
            self.update()

    def __str__(self):
        return str([{"time": self.timestamp, "memory": self.memory, "cpu": self.cpu,
                     "boot": self.boot, "network": self.network, "disk": self.disk}])

    def update(self):
        """ Function to update the entire class information """
        self.cpu["percentage"] = psutil.cpu_percent(interval=0.7)
        self.boot = psutil.boot_time()
        # Fetch all information about Memory in a temp variable
        # then assign each value to a specific key (psutil usually returns
        # a named tuple)
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
        self.timestamp = time.time()

if __name__ == "__main__":
    SYSINFO = SystemStatus(update=True)
    print(SYSINFO)
