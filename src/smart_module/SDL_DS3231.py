#!/usr/bin/env python

# SDL_DS3231.py Python Driver Code
# SwitchDoc Labs 12/19/2014
# V 1.2
# only works in 24 hour mode
# now includes reading and writing the AT24C32 included on the SwitchDoc Labs
# DS3231 / AT24C32 Module (www.switchdoc.com)


#encoding: utf-8

# Copyright (C) 2013 @XiErCh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime
import time

import smbus


def _bcd_to_int(bcd, n=2):
    """Decode n least significant packed binary coded decimal digits to binary.
    Return binary result.
    n defaults to 2 (BCD digits).
    n=0 decodes all digits."""
    return int(('%x' % bcd)[-n:])


def _bcd_to_int(bcd, n=2):
    """Decode n least significant packed binary coded decimal digits to binary.
    Return binary result.
    n defaults to 2 (BCD digits)."""
    x = 0
    m = 1
    for _ in range(n):
        bcd, digit = divmod(bcd, 1<<4)
        x += m * digit
        m *= 10
    return x


def _int_to_bcd(x, n=2):
    """
    Encode the n least significant decimal digits of x
    to packed binary coded decimal (BCD).
    Return BCD value.
    n defaults to 2 (digits).
    n=0 encodes all digits.
    """

    return int(('%d' % x)[-n:], 0x10)


def _int_to_bcd(x, n=2):
    """
    Encode the n least significant decimal digits of x
    to packed binary coded decimal (BCD).
    Return BCD value.
    n defaults to 2 (digits).
    n=0 encodes all digits.
    """

    return int(str(x)[-n:], 0x10)


def _int_to_bcd(x, n=2):
    """
    Encode the n least significant decimal digits of x
    to packed binary coded decimal (BCD).
    Return BCD value.
    n defaults to 2 (digits).
    """

    bcd = 0
    m = 1
    for _ in range(n):
        x, digit = divmod(x, 10)
        bcd += m * digit
        m *= 0x10
    return bcd


class SDL_DS3231():
    _REG_SECONDS = 0x00
    _REG_MINUTES = 0x01
    _REG_HOURS = 0x02
    _REG_DAY = 0x03
    _REG_DATE = 0x04
    _REG_MONTH = 0x05
    _REG_YEAR = 0x06
    _REG_CONTROL = 0x07

    ###########################
    # DS3231 Code
    ###########################
    def __init__(self, twi=1, addr=0x68, at24c32_addr=0x56):
        self._bus = smbus.SMBus(twi)
        self._addr = addr
        self._at24c32_addr = at24c32_addr

    def _write(self, register, data):
        #print "addr =0x%x register = 0x%x data = 0x%x %i " % (self._addr, register, data,_bcd_to_int(data))
        self._bus.write_byte_data(self._addr, register, data)

    def _read(self, data):

        returndata = self._bus.read_byte_data(self._addr, data)
        #print "addr = 0x%x data = 0x%x %i returndata = 0x%x %i " % (self._addr, data, data, returndata, _bcd_to_int(returndata))
        return returndata

    def _read_seconds(self):
        return _bcd_to_int(self._read(self._REG_SECONDS)& 0x7F)   # wipe out the oscillator on bit

    def _read_minutes(self):
        return _bcd_to_int(self._read(self._REG_MINUTES))

    def _read_hours(self):
        d = self._read(self._REG_HOURS)
        if (d == 0x64):
            d = 0x40
        return _bcd_to_int(d & 0x3F)

    def _read_day(self):
        return _bcd_to_int(self._read(self._REG_DAY))

    def _read_date(self):
        return _bcd_to_int(self._read(self._REG_DATE))

    def _read_month(self):
        return _bcd_to_int(self._read(self._REG_MONTH))

    def _read_year(self):
        return _bcd_to_int(self._read(self._REG_YEAR))

    def read_all(self):
        """Return a tuple such as (year, month, date, day, hours, minutes,
        seconds).
        """
        return (self._read_year(), self._read_month(), self._read_date(),
                self._read_day(), self._read_hours(), self._read_minutes(),
                self._read_seconds())

    def read_str(self):
        """Return a string such as 'YY-DD-MMTHH-MM-SS'.
        """
        return '%02d-%02d-%02dT%02d:%02d:%02d' % (self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds())

    def read_datetime(self, century=21, tzinfo=None):
        """Return the datetime.datetime object.
        """
        return datetime((century - 1) * 100 + self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds(), 0, tzinfo=tzinfo)

    def write_all(self, seconds=None, minutes=None, hours=None, day=None,
            date=None, month=None, year=None, save_as_24h=True):
        """Direct write un-none value.
        Range: seconds [0,59], minutes [0,59], hours [0,23],
               day [0,7], date [1-31], month [1-12], year [0-99].
        """
        if seconds is not None:
            if seconds < 0 or seconds > 59:
                raise ValueError('Seconds is out of range [0,59].')
            seconds_reg = _int_to_bcd(seconds)
            self._write(self._REG_SECONDS, seconds_reg)

        if minutes is not None:
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes is out of range [0,59].')
            self._write(self._REG_MINUTES, _int_to_bcd(minutes))

        if hours is not None:
            if hours < 0 or hours > 23:
                raise ValueError('Hours is out of range [0,23].')
            self._write(self._REG_HOURS, _int_to_bcd(hours) ) # not  | 0x40 according to datasheet

        if year is not None:
            if year < 0 or year > 99:
                raise ValueError('Years is out of range [0,99].')
            self._write(self._REG_YEAR, _int_to_bcd(year))

        if month is not None:
            if month < 1 or month > 12:
                raise ValueError('Month is out of range [1,12].')
            self._write(self._REG_MONTH, _int_to_bcd(month))

        if date is not None:
            if date < 1 or date > 31:
                raise ValueError('Date is out of range [1,31].')
            self._write(self._REG_DATE, _int_to_bcd(date))

        if day is not None:
            if day < 1 or day > 7:
                raise ValueError('Day is out of range [1,7].')
            self._write(self._REG_DAY, _int_to_bcd(day))

    def write_datetime(self, dt):
        """Write from a datetime.datetime object.
        """
        self.write_all(dt.second, dt.minute, dt.hour,
                dt.isoweekday(), dt.day, dt.month, dt.year % 100)

    def write_now(self):
        """Equal to DS3231.write_datetime(datetime.datetime.now()).
        """
        self.write_datetime(datetime.now())

    def getTemp(self):
        byte_tmsb = self._bus.read_byte_data(self._addr,0x11)
        byte_tlsb = bin(self._bus.read_byte_data(self._addr,0x12))[2:].zfill(8)
        return byte_tmsb+int(byte_tlsb[0])*2**(-1)+int(byte_tlsb[1])*2**(-2)

    ###########################
    # AT24C32 Code
    ###########################

    def set_current_AT24C32_address(self,address):
        a1=address/256;
        a0=address%256;
        self._bus.write_i2c_block_data(self._at24c32_addr,a1,[a0])

    def read_AT24C32_byte(self, address):
        #print "i2c_address =0x%x eepromaddress = 0x%x  " % (self._at24c32_addr, address)

        self.set_current_AT24C32_address(address)
        return self._bus.read_byte(self._at24c32_addr)

    def write_AT24C32_byte(self, address, value):
        #print "i2c_address =0x%x eepromaddress = 0x%x value = 0x%x %i " % (self._at24c32_addr, address, value, value)
        a1=address/256;
        a0=address%256;
        self._bus.write_i2c_block_data(self._at24c32_addr,a1,[a0, value])
        time.sleep(0.20)
