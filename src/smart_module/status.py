#!/bin/python
# or #!/bin/env python3

# HAPI Project
# Smart Module Status is responsible to fetch information from the system
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

# We should get:
# 1. Memory:
# 	1.1. Memory used;
# 	1.2. Memory available; and
# 	1.3. Memory Process time.
# 2. Disk:
# 	2.1. Disk used; and
# 	2.2. Disk available.
# 3. Networking
# 	3.1. Network active connections;
# 	3.2. Network sent packets; and
# 	3.3. Network received packets.
# 4. Boot:
# 	4.1. Boot time.
# 5. CPU:
# 	5.1. CPU Process time

import psutil
import json

class SystemStatus:
	""" Small class to handle system information """

	def __init__(self):
		self.memory = { "used": 0, "free": 0 }
		self.cpu = { "percentage": 0 }
		self.boot = { "time": 0 }
		self.network = { "Packet sent": 0, "Packet recvd": 0 }
		self.update()

	def __str__(self):
		json_string = '{"memory": {}, "cpu": {}, "boot": {}, \
						"network": {}}'.format(self.memory, self.cpu, self.boot, self.network)
		return json_string

	def update(self):
		self.cpu["percentage"] = psutil.cpu_percent(interval=0.7)
		self.memory["used"] = psutil.virtual_memory()

if __name__ == "__main__":
	testingclass = SystemStatus()
	print (testingclass)
