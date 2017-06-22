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
import log

class Notification(object):
    """Hold information about nofication that can be sent via SMS or email."""

    def __init__(self, **kwargs):
        self.logging = log.Log("notification.log")
        self.sender = ""
        self.receiver = ""
        self.message = ""

        if kwargs is not None:
            try:
                for key, value in kwargs.iteritems():
                    setattr(self, key, value)
            except Exception as excpt:
                self.logging.exception("Error setting parameters to Notification: %s", excpt)

    @abstractmethod
    def send(self, notification_msg):
        """Send notification."""

class Email(Notification):
    """Email notification."""

    def __init__(self, **kwargs):
        Notification.__init__(self, **kwargs)
        try:
            self.username = kwargs["username"]
            self.password = kwargs["password"]
            self.serveraddr = kwargs["server"]
            self.subject = kwargs["subject"]
        except Exception as excpt:
            self.logging.exception("Trying to set username and password: %s.", excpt)

    def build_message(self, alert):
        """Build message body for e-mail."""

        message = "\r\n".join([
            "From: " + self.sender,
            "To: " + self.receiver,
            "Subject: " + self.subject,
            "",
            alert + " : " + self.message])

        return message

    def send(self, notification_msg):
        try:
            self.logging.info("Sending email notification.")
            server = smtplib.SMTP(self.serveraddr)
            server.ehlo()
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.sender, self.receiver, self.build_message(notification_msg))
        except Exception as excpt:
            self.logging.exception("Trying to send notificaton via e-mail: %s.", excpt)
        finally:
            server.quit()

class SMS(Notification):
    """SMS notification."""

    def __init__(self, **kwargs):
        Notification.__init__(self, **kwargs)

    def send(self, notification_msg):
        pass
