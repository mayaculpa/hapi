#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
HAPI Asset Interface - v1.0
Release: May 2017, Beta Milestone
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

import random
import datetime
import logging
import time
from utilities import SM_LOGGER
#import RPi.GPIO

LEN_ID = 16
LEN_CONTEXT = 16
LEN_TYPE = 2
RTC_VCC = 15
GPIO = None

class RTCInterface(object):
    '''Interface for DS3231 Real-time Clock with internal temp sensor and AT24C32 EEPROM
    In order to minimize energy consumption, the RTC is kept powered off until it is needed.
    Powering the unit on and off is the responsiblility of the calling code.
    The RTC is powered from a digital pin that is toggled via GPIO output commands.
    '''

    def __init__(self):
        self.mock = False

        try:
            global SDL_DS3231
            import SDL_DS3231
        except ImportError:
            self.mock = True

        try:
            global GPIO
            import RPi.GPIO as GPIO
        except ImportError:
            self.mock = True

        self.logger = logging.getLogger(SM_LOGGER)

        try:
            if not self.mock:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(RTC_VCC, GPIO.OUT)
                self.ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68, 0x57)
        except Exception, excpt:
            self.logger.exception("Error initializing RTC. %s", excpt)

    def power_on_rtc(self):
        if not self.mock:
            GPIO.output(RTC_VCC, GPIO.HIGH)
            time.sleep(0.5)

    def power_off_rtc(self):
        if not self.mock:
            GPIO.output(RTC_VCC, GPIO.LOW)

    def get_datetime(self):
        '''Gets the current date/time from the attached RTC
        Returns:
            datetime: Current date/time from RTC if mock is False. Current Python datetime if mock
            is True
        '''
        try:
            if self.mock:
                return datetime.datetime.now()

            return self.ds3231.read_datetime()
        except Exception, excpt:
            self.logger.exception("Error getting RTC date/time. %s", excpt)

    def set_datetime(self):
        '''Writes the system datetime to the attached RTC (mock is False)
        '''

        try:
            if not self.mock:
                self.ds3231.write_now()
        except Exception, excpt:
            self.logger.exception("Error writing date/time to RTC. %s", excpt)

    def get_temp(self):
        '''Gets the internal temperature from the RTC component
        Returns:
            float: Current RTC internal temperature sensor value if mock is False. 20.0 if mock
            is True
        '''

        try:
            if self.mock:
                return float(random.randrange(8, 34, 1))

            return self.ds3231.getTemp()
        except Exception, excpt:
            self.logger.exception("Error getting the temperature from the RTC. %s", excpt)

    def get_type(self):
        '''Gets the modules sensor type from the EEPROM
        Returns:
            str: 2-byte Type data as String if mock is False. "wt" if mock is True
        '''

        try:
            if self.mock:
                return "wt"

            byte0 = self.ds3231.read_AT24C32_byte(0)
            byte1 = self.ds3231.read_AT24C32_byte(1)
            return str(chr(byte0) + chr(byte1)).strip()
        except Exception, excpt:
            self.logger.exception("Error reading type from EEPROM. %s", excpt)

    def set_type(self, type_data):
        '''Writes the modules 2-byte sensor type to EEPROM
        Args:
            type_data (str): Sensor Type to write to EEPROM
        '''

        try:
            if not self.mock:
                self.ds3231.write_AT24C32_byte(0, ord(type_data[0]))
                self.ds3231.write_AT24C32_byte(1, ord(type_data[1]))
        except Exception, excpt:
            self.logger.exception("Error writing Sensor Type to EEPROM. %s", excpt)

    def get_id(self):
        '''Gets the Smart Module ID from the attached EEPROM
        Returns:
            str: 16-byte module ID if mock is False. "HSM-WT123-MOCK" if mock is True
        '''

        try:
            if self.mock:
                return "HSM-WT123-MOCK"

            #Concatenate the 16 byte module ID
            id_data = ""
            for x in range(LEN_TYPE, LEN_TYPE + LEN_ID):
                id_data = id_data + chr(self.ds3231.read_AT24C32_byte(x))
            return str(id_data).strip()
        except Exception, excpt:
            self.logger.exception("Error reading Module ID from EEPROM. %s", excpt)

    def set_id(self, id_data):
        '''Writes the module id to EEPROM
        Args:
            id_data (str): The ID of the Smart Module to write to EEPROM
        Returns:
            None
        '''

        try:
            if not self.mock:
                #Concatenate the 16 byte module ID
                for x in range(0, LEN_ID):
                    if len(id_data) < x + 1:
                        ch = " "
                    else:
                        ch = id_data[x]

                    self.ds3231.write_AT24C32_byte(x + LEN_TYPE, ord(ch))
        except Exception, excpt:
            self.logger.exception("Error writing Module ID to EEPROM. %s", excpt)


    def get_context(self):
        '''Gets the module context from the attached EEPROM
        Returns:
            str: 16-byte sensor context if mock is False. "Environment" if mock is True
        '''

        try:
            if self.mock:
                return "Environment"

            #Read the 16 byte asset context
            context = ""
            for x in range(LEN_ID + LEN_TYPE, LEN_ID + LEN_TYPE + LEN_CONTEXT):
                context = context + chr(self.ds3231.read_AT24C32_byte(x))
            return str(context).strip()
        except Exception, excpt:
            self.logger.exception("Error reading Module context from EEPROM. %s", excpt)

    def set_context(self, context):
        '''Writes the modules sensor context to the attached EEPROM
        Args:
            context (str): The context of the Smart Modules sensor (Water, Light, etc)
        Returns:
            None
        '''

        try:
            if not self.mock:
                #Write the 16 byte sensor context
                for x in range(0, LEN_CONTEXT):
                    if len(context) < x + 1:
                        ch = " "
                    else:
                        ch = context[x]

                    self.ds3231.write_AT24C32_byte(LEN_TYPE + LEN_ID + x, ord(ch))
        except Exception, excpt:
            self.logger.exception("Error writing Module context to EEPROM. %s", excpt)
