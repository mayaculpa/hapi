#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
HAPI Asset Interface for the DS18B20 Temperature Sensor
Authors: Tyler Reed
Release: April 2017, Alpha Milestone
Version: 1.0
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

from __future__ import print_function

import asset_interface
import w1thermsensor    #pip install w1thermsensor
import os
import glob
import time
import logging
import subprocess

version = "3.0 Alpha"
sm_logger = "smart_module"

class AssetImpl(object):
    def __init__(self):
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            base_dir = '/sys/bus/w1/devices'
            device_dir = glob.glob(os.path.join(base_dir, '28*'))[0]
            self.device_path = os.path.join(device_dir, 'w1_slave')
            print('Device file:', self.device_path)
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error initializing sensor interface: %s", excpt)

    def read_temp_raw(self):
        try:
            catdata = subprocess.Popen(
                ['cat', self.device_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = catdata.communicate()
            out_decode = out.decode('utf-8')
            lines = out_decode.split('\n')
            return lines
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error reading raw temperature data: %s", excpt)

    def read_value(self):
        try:
            temp_c = -50
            lines = self.read_temp_raw()
            print(lines)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.read_temp_raw()
                print(lines)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0

            return temp_c
        except Exception, excpt:
            logging.getLogger(sm_logger).exception("Error getting converted sensor data: %s", excpt)

