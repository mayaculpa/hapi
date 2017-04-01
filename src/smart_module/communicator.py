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

import time
import logging
import paho.mqtt.client as mqtt
import datetime

class Communicator(object):
    def __init__(self):
        self.rtuid = ""
        self.name = ""
        self.broker_name = "localhost"
        self.TSL = False
        self.fallback_broker = ""
        self.influx_address = ""
        self.start_uptime = datetime.datetime.now()
        self.client = mqtt.Client(clean_session=True, userdata=None, protocol=mqtt.MQTTv31)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.ctl_function = None
        self.site = None
        self.is_connected = False
        self.scheduler_found = False
        self.logger = logging.getLogger("smart_module")
        self.logger.info("Communicator initialized")

    def connect(self):
        if self.TSL is True:
            self.logger.info("Connecting over TSL.")
            self.client.connect(self.broker_name, 8883, 5)
        else:
            self.logger.info("Connecting to " + self.broker_name + " over standard WiFi.")
            self.client.connect(self.broker_name)
            self.client.loop_start()

    def on_disconnect(self, client, userdata, rc):
        print mqtt.error_string(rc)
        self.logger.info("Disconnected")

    # The callback for when the client receives a CONNACK response from the server.
    #@staticmethod
    def on_connect(self, client, userdata, flags, rc):
        # self.logger.info("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#")
        self.is_connected = True
        client.subscribe(self.name.replace(" ", "") + "/#", qos=2)
        client.subscribe("ANNOUNCE" + "/#", qos=0)

        # Commented subscribes are the topics that the RTUs will be listening to
        client.subscribe("COMMAND" + "/#")

        # Time synchronization topic
        client.subscribe("SYNCHRONIZE/TIME" + "/#", qos=0)

        # Database synchronization topic
        client.subscribe("SYNCHRONIZE/DATA" + "/#", qos=0)

        client.subscribe("QUERY" + "/#")
        #client.subscribe("RESPONSE/#")

        #client.subscribe("REPORT/#")

        client.subscribe("SCHEDULER/#")

        client.subscribe("STATUS/#")

    # The callback when a message is received
    def on_message(self, client, userdata, msg):
        #if self.ctl_routine is not None:
        print(msg.topic+" "+str(msg.payload))
        if msg.topic == "COMMAND":
            self.site.execute_command(msg.payload)

        if "QUERY/ASSET/" in msg.topic:
            asset_name = msg.topic.split("/")[2]
            if asset_name in self.site.assets:
                self.comm.send("QUERY/ASSET/" + asset_name.lower().strip(), "QUERY")
            print "Asset = ", asset, msg.payload
            self.site.asset_data.update({asset:msg.payload})
        elif "STATUS" in msg.topic:
            print "Got", msg.topic, msg.payload
            self.send("REPORT", self.site.get_status())
        elif "SCHEDULE/IDENT" in msg.topic:
            self.scheduler_found = True
            self.site.scheduler_id = msg.payload
        elif "SCHEDULER/LOCATE" in msg.topic:
            if self.site.scheduler is not None:
                self.send("SCHEDULER/IDENT", self.site.hostname)
                self.logger.info("Sent SCHEDULER/IDENT")
            #self.site.asset_data.update({asset:msg.payload})

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def send(self, topic, message):
        if self.client is not None:
            self.client.publish(topic, message)

