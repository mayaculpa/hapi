#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
HAPI Asset Interface for the DS18B20 Temperature Sensor
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
import os
import glob
import time
import log

class AssetImpl(object):
    def __init__(self):
        try:
            # Let's put it as a config/dep on the image and modprobe'd on boot
            #os.system('modprobe w1-gpio')
            #os.system('modprobe w1-therm')
            base_dir = '/sys/bus/w1/devices'
            device_dir = glob.glob(os.path.join(base_dir, '28*'))[0]
            self.device_path = os.path.join(device_dir, 'w1_slave')
            self.log = log.Log("asset.log")
            print('Device file:', self.device_path)
        except Exception as excpt:
            self.log.exception("Error initializing sensor interface: %s.", excpt)

    def read_temp_raw(self):
        try:
            with open(self.device_path, "r") as f:
                return f.read().decode('utf-8').split('\n')
        except Exception as excpt:
            self.log.exception("Error reading raw temperature data: %s.", excpt)

    def read_value(self):
        temp_c = -50
        try:
            lines = self.read_temp_raw()
            while not lines[0].strip().endswith('YES'):
                time.sleep(0.2)
                lines = self.read_temp_raw()

            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0

        except Exception as excpt:
            self.log.exception("Error getting converted sensor data: %s.", excpt)

        return temp_c
