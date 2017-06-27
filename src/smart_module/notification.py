#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Smart Module v2.1.2
Release: April 2017 Beta Milestone

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
"""

from __future__ import print_function
from abc import abstractmethod
import smtplib
import sqlite3
import log
from utilities import DB_CORE

class Notification(object):
    """Hold information about nofication that can be sent via SMS or email."""

    def __init__(self):
        self.logging = log.Log("notification.log")
        self.sender = ""
        self.receiver = ""

    @abstractmethod
    def send(self, subject, message):
        """Send notification."""

    @abstractmethod
    def load_settings(self):
        """Load mail settings."""

class Email(Notification):
    """Email notification."""

    def __init__(self):
        Notification.__init__(self)
        self.serveraddr = ""
        self.serverport = ""
        self.username = ""
        self.password = ""
        self.tls = False

    def load_settings(self):
        """Load mail settings from the core database."""
        try:
            field_names = '''
                serveraddr
                serverport
                username
                password
                sender
                receiver
                tls
            '''.split()
            sql = 'SELECT {fields} FROM mail_settings LIMIT 1;'.format(
                fields=', '.join(field_names))
            database = sqlite3.connect(DB_CORE)
            db_elements = database.cursor().execute(sql).fetchone()
            for field, value in zip(field_names, db_elements):
                setattr(self, field, value)
            self.logging.info("Mail settings loaded.")
        except Exception as excpt:
            self.logging.exception("Trying to load mail settings: %s.", excpt)
        finally:
            database.close()


    def build_message(self, subject, message):
        """Build message body for e-mail."""
        message = "\r\n".join([
            "From: " + self.sender,
            "To: " + self.receiver,
            "Subject: " + subject,
            "",
            message])

        return message

    def send(self, subject, message):
        """Send email notification using paremeters from the database."""
        try:
            self.logging.info("Sending email notification.")
            self.load_settings()
            server = smtplib.SMTP(self.serveraddr, str(self.serverport))
            server.ehlo()
            if self.tls:
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.sender, self.receiver, self.build_message(subject, message))
            self.logging.info("Email notification sent.")
        except Exception as excpt:
            self.logging.exception("Trying to send notificaton via e-mail: %s.", excpt)
        finally:
            server.quit()

class SMS(Notification):
    """SMS notification."""

    def __init__(self):
        Notification.__init__(self)

    def send(self, subject, message):
        pass

    def load_settings(self):
        pass
