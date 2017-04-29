#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Master Controller v1.0
Author: Tyler Reed
Release: March 2017 Alpha

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

import time
import logging
import paho.mqtt.client as mqtt
import datetime

class Communicator(object):
    def __init__(self):
        self.rtuid = ""
        self.name = ""
        self.broker_name = "mqttbroker.local"
        self.fallback_broker = ""
        self.influx_address = ""
        self.start_uptime = datetime.datetime.now()
        self.client = mqtt.Client(clean_session=True, userdata=None, protocol=mqtt.MQTTv31)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.smart_module = None
        self.is_connected = False
        self.scheduler_found = False
        self.logger = logging.getLogger("smart_module")
        self.logger.info("Communicator initialized")
        self.broker_connections = -1

    def connect(self):
        try:
            self.logger.info("Connecting to " + self.broker_name + " over standard WiFi.")
            self.client.connect("mqttbroker.local", 1883, 5)
            # Probably testing code?
            self.send("ANNOUNCE", "neuromancer.local" + " is online.")
        except Exception, excpt:
            self.logger.exception("Error connecting to broker. %s", excpt)

    def on_disconnect(self, client, userdata, rc):
        print(mqtt.error_string(rc))
        self.logger.info("Disconnected")

    # The callback for when the client receives a CONNACK response from the server.
    #@staticmethod
    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Connected with result code " + str(rc))
        # Subscribing in on_connect() means if we lose connection and reconnect, subscriptions will be renewed.
        self.is_connected = True
        self.client.subscribe("COMMAND" + "/#")
        #self.client.subscribe("SCHEDULER/LOCATE")
        self.client.subscribe("SCHEDULER/IDENT")
        self.client.subscribe("$SYS/broker/clients/total")
        self.client.subscribe("SYNCHRONIZE/DATA" + "/#", qos=0)
        self.client.subscribe("SYNCHRONIZE/VERSION", qos=0)
        self.client.subscribe("SYNCHRONIZE/CORE", qos=0)
        self.client.subscribe("SYNCHRONIZE/GET", qos=0)
        self.client.subscribe("ASSET/QUERY" + "/#")
        self.client.subscribe("STATUS/QUERY")

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    # The callback when a message is received
    def on_message(self, client, userdata, msg):
        #if self.ctl_routine is not None:
        print(msg.topic, msg.payload)
        if "ENV/QUERY" in msg.topic:
            self.smart_module.get_env(msg.payload)

        elif "ASSET/QUERY" in msg.topic:
            asset_name = msg.topic.split("/")[2]
            if self.smart_module.asset.name.lower() == asset_name.lower():
                self.comm.send("ASSET/RESPONSE" + asset_name.lower().strip(), "QUERY")
            print('Asset = ', asset, msg.payload)
            self.smart_module.asset_data.update({asset:msg.payload})

        elif "ASSET/RESPONSE" in msg.topic:
            if self.smart_module.scheduler:
                asset_id = msg.topic.split("/")[2]
                self.smart_module.check_alert(asset_id, float(msg.payload))
                self.smart_module.check_alert(asset_id, float(msg.payload))
                print('Asset = ', asset_id, msg.payload)

        elif "STATUS/QUERY" in msg.topic:
            self.smart_module.lastStatus = self.smart_module.get_status(self.broker_connections)
            self.send("STATUS/RESPONSE", str(self.smart_module.lastStatus))

        # Not sure why System Status should be Scheduled, if we're listen for queries?
        elif "STATUS/RESPONSE" in msg.topic:
            # Pushing System Status to Influx Server
            self.smart_module.push_sysinfo("system", self.smart_module.lastStatus)

        # Scheduler messages
        elif "SCHEDULER/RESPONSE" in msg.topic:
            self.scheduler_found = True
            self.logger.info(msg.payload + " has identified itself as the Scheduler.")

        elif "SCHEDULER/QUERY" in msg.topic:
            if self.smart_module.scheduler:
                self.send("SCHEDULER/RESPONSE", self.smart_module.hostname)
                self.logger.info("Sent SCHEDULER/RESPONSE")
                #self.site.asset_data.update({asset:msg.payload})

        # Database synchronization messages
        elif "SYNCHRONIZE/VERSION" in msg.topic:
            self.send("SYNCHRONIZE/RESPONSE", self.smart_module.data_sync.read_db_version())

        elif "SYNCHRONIZE/GET" in msg.topic:
            if msg.payload == self.smart_module.hostname:
                self.smart_module.data_sync.publish_core_db(self)

        elif "SYNCHRONIZE/DATA" in msg.topic:
            self.smart_module.data_sync.synchronize_core_db(msg.payload)

        elif "$SYS/broker/clients/total" in msg.topic:
            self.broker_connections = int(msg.payload)

        # elif "SYNCHRONIZE/TEST" in msg.topic:
        #     self.send("SYNCHRONIZE/RESPONSE", self.smart_module.data_sync.read_db_version())

    def send(self, topic, message):
        try:
            if self.client:
                self.client.publish(topic, message)
        except Exception, excpt:
            self.logger.info("Error publishing message: %s", excpt)
