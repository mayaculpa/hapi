#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
HAPI Asset Interface - v1.0
Authors: Tyler Reed
Release: April 2017, Beta Milestone
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
#https://github.com/switchdoclabs/RTC_SDL_DS3231/blob/master/SDL_DS3231.py

import SDL_DS3231
import sys
import datetime

sm_logger = "smart_module"

class RTCInterface(object):
    '''Interface for DS3231 Real-time Clock with AT24C32 EEPROM and internal temp sensor
    '''

    ID_ADDRESS = 2
    ID_LEN = 16

    def __init__(self, mock):
        '''
        Args:
            mock (bool): Set to True is a hardware RTC is not connected
        '''
        self.mock = mock
        if not self.mock:
            self.ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68, 0x57)

    def get_datetime(self):
        '''
        Returns:
            datetime: Current date/time from RTC if mock is False. Current Python datetime if mock is True
        '''
        if self.mock:
            return datatime.datetime.now()
        else:
            return self.ds3231.read_datetime()

    def set_datetime(self):
        '''
        Sets the RTC date/time to Python date/time if mock is False
        '''
        if not self.mock:
            self.ds3231.write_now()

    def get_temp(self):
        '''
        Returns:
            float: Current RTC internal temperature sensor value if mock is False. 20.0 if mock is True
        '''

        if self.mock:
            return float(random.randrange(8, 34, 1))
        else:
            return self.ds3231.getTemp()

    def get_type(self):
        '''
        Returns:
            str: 2-byte Type data as String if mock is False. "WT" if mock is True
        '''
        if self.mock:
            return "WT"
        else:
            byte0 = self.ds3231.read_AT24C32_byte(0)
            byte1 = self.ds3231.read_AT24C32_byte(1)
            return str(byte0) + str(byte1)

    def set_type(self, type_data):
        '''
        Args:
            type_data (str): Sensor Type to write to EEPROM
        '''
        if not self.mock:
            self.ds3231.write_AT24C32_byte(0, ord(type_data[0]))
            self.ds3231.write_AT24C32_byte(1, ord(type_data[1]))

    def get_id(self):
        '''
        Returns:
            str: 16-byte Smart Module ID if mock is False. "HSM-WT123-MOCK" if mock is True
        '''

        if self.mock:
            return "HSM-WT123-MOCK"
        else:
            #Concatenate the 16 byte unique sensor address
            id = ""
            for x in range(2,18):
                id = id + str(self.ds3231.read_AT24C32_byte(x))
            return id

    def set_id(self, id):
        '''
        Write id to EEPROM.
        Returns:
            None
        '''
        if self.mock:
            return

        id = id.ljust(ID_LEN)  # Pad with spaces.
	id = id[:ID_LEN]  # Limit to correct length.
        for i, c in enumerate(id):
            self.ds3231.write_AT24C32_byte(ID_ADDRESS + i, ord(c))

    def get_context(self):
        '''
        Returns:
            str: 16-byte sensor context if mock is False. "Environment" if mock is True
        '''

        if self.mock == True:
            return "Environment"
        else:
            #Read the 16 byte asset context
            context = ""
            for x in range(18, 34):
                context = context + str(self.ds3231.read_AT24C32_byte(x))
            return id

    def set_context(self, context):
        '''
        Returns:
            None
        '''
        if self.mock is False:
            #Write the 16 byte asset context
            for x in range(0,16):
                if len(context) < x:
                    ch = ""
                else:
                    ch = id[x]

                self.ds3231.write_AT24C32_byte(x + 18, ord(ch))

