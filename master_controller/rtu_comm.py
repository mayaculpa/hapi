# -*- coding: utf-8 -*-
#!/usr/bin/env python

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

import telnetlib

class RTUCommunicator(object):
    def __init__(self):
        self.rtuid = ""

    def send_to_rtu(self, address, port, timeout, command):
        # address is a string with an ip address
        # port is an integer containing the port number
        # timeout an integer containing the timeout parameter in seconds
        tn = telnetlib.Telnet()
        tn.open(address, port, timeout)
        tn.write(command + "\n")
        response = tn.read_all()
        tn.close()
        return response

