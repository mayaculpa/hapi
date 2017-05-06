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

import sys
import datetime
import logging
import time

some_import_failed = False
try:
    import SDL_DS3231
except ImportError:
    some_import_failed = True

try:
    import RPi.GPIO as GPIO
except ImportError:
    some_import_failed = True

SM_LOGGER = "smart_module"

TYPE_ADDRESS = 0
TYPE_LEN = 2
ID_ADDRESS = TYPE_ADDRESS + TYPE_LEN
ID_LEN = 16
CONTEXT_ADDRESS = ID_ADDRESS + ID_LEN
CONTEXT_LEN = 16

RTC_VCC_GPIO_PIN = 15

class RTCInterface(object):
    '''Interface for DS3231 Real-time Clock with internal temp sensor and AT24C32 EEPROM
    In order to minimize energy consumption, the RTC is kept powered off until it is needed.
    Powering the unit on and off is the responsiblility of the calling code.
    The RTC is powered from a digital pin that is toggled via GPIO output commands.
    '''

    def __init__(self):
        '''
        '''
        self.mock = some_import_failed

        self.logger = logging.getLogger(SM_LOGGER)

        if self.mock:
            return

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(RTC_VCC_GPIO_PIN, GPIO.OUT)
        try:
            self.ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68, 0x57)
        except Exception, excpt:
            self.logger.exception("Error initializing RTC. %s", excpt)

    def power_on_rtc(self):
        if self.mock:
            return

        GPIO.output(RTC_VCC_GPIO_PIN, GPIO.HIGH)
        time.sleep(0.5)

    def power_off_rtc(self):
        if self.mock:
            return

        GPIO.output(RTC_VCC_GPIO_PIN, GPIO.LOW)

    def get_datetime(self):
        '''Gets the current date/time from the attached RTC
        Returns:
            datetime: Current date/time from RTC if mock is False. Current Python datetime if mock is True
        '''
        if self.mock:
            return datetime.datetime.now()

        try:
            return self.ds3231.read_datetime()
        except Exception, excpt:
            self.logger.exception("Error getting RTC date/time. %s", excpt)

    def set_datetime(self):
        '''Writes the system datetime to the attached RTC (mock is False)
        '''

        if self.mock:
            return

        try:
            self.ds3231.write_now()
        except Exception, excpt:
            self.logger.exception("Error writing date/time to RTC. %s", excpt)

    def get_temp(self):
        '''Gets the internal temperature from the RTC component
        Returns:
            float: Current RTC internal temperature sensor value if mock is False. 20.0 if mock is True
        '''

        if self.mock:
            return float(random.randrange(8, 34, 1))

        try:
            return self.ds3231.getTemp()
        except Exception, excpt:
            self.logger.exception("Error getting the temperature from the RTC. %s", excpt)

    def read_eeprom(self, address, n, name, mock_value):
        '''Return string of n bytes from EEPROM starting at address.
        Strips leading and trailing spaces.
        If self.mock, return mock value instead.
        '''

        if self.mock:
            return mock_value

        try:
            bytes_ = (
                self.ds3231.read_AT24C32_byte(address + i)
                for i in range(n)
            )
        except Exception, excpt:
            self.logger.exception("Error reading %s from EEPROM. %s", name, excpt)

        s = ''.join(chr(c) for c in bytes_)
        return s.strip()

    def write_eeprom(self, s, address, n, name):
        '''Write n bytes of s to EEPROM
        starting at EEPROM address.
        s is padded with spaces if shorter than n.
        If exception, cites name.
        '''

        if self.mock:
            return

        s = s[:n]  # Trim to maximum length.
        s = s.ljust(n)  # Pad to correct length.
        for i, c in enumerate(s):
            try:
                self.ds3231.write_AT24C32_byte(address + i, ord(c))
            except Exception, excpt:
                self.logger.exception("Error writing %s to EEPROM. %s", name, excpt)
                return

    def get_type(self):
        '''Gets the modules sensor type from the EEPROM
        Returns:
            str: 2-byte Type data as String if mock is False. "wt" if mock is True
        '''

        return self.read_eeprom(self, TYPE_ADDRESS, TYPE_LEN, 'type', 'wt')

    def set_type(self, type_):
        '''Writes the modules %s-byte sensor type to EEPROM
        Args:
            type_ (str): Sensor Type to write to EEPROM
        ''' % TYPE_LEN

        self.write_eeprom(type_, TYPE_ADDRESS, TYPE_LEN, 'Sensor Type')

    def get_id(self):
        '''Gets the Smart Module ID from the attached EEPROM
        Returns:
            str: %s-byte module ID if mock is False. "HSM-WT123-MOCK" if mock is True
        ''' % ID_LEN

        return self.read_eeprom(
            self, ID_ADDRESS, ID_LEN, 'Module ID', 'HSM-WT123-MOCK')

    def set_id(self, id_):
        '''Writes the module id to EEPROM
        Args:
            id_ (str): The ID of the Smart Module to write to EEPROM      
        Returns:
            None
        '''

        self.write_eeprom(id_, ID_ADDRESS, ID_LEN, 'Module ID')

    def get_context(self):
        '''Gets the module context from the attached EEPROM
        Returns:
            str: %s-byte sensor context if mock is False. "Environment" if mock is True
        ''' % CONTEXT_LEN

        return self.read_eeprom(
            self,
            CONTEXT_ADDRESS, CONTEXT_LEN, 'Module context', 'Environment')

    def set_context(self, context):
        '''Writes the modules sensor context to the attached EEPROM
        Args:
            context (str): The context of the Smart Modules sensor (Water, Light, etc)
        Returns:
            None
        '''

        self.write_eeprom(context, CONTEXT_ADDRESS, CONTEXT_LEN, 'Module context')
