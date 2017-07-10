#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Master Controller v1.0
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
import sys
import json
import datetime
from log import Log
import paho.mqtt.client as mqtt
import notification
from alert import Alert

class Communicator(object):
    def __init__(self, sm):
        self.rtuid = ""
        self.name = ""
        self.broker_name = None
        self.broker_ip = None
        self.client = mqtt.Client(clean_session=True, userdata=None, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.smart_module = sm
        self.is_connected = False
        self.scheduler_found = False
        self.broker_connections = -1
        Log.info("Communicator initialized")

    def connect(self):
        """Connect to the broker."""
        try:
            Log.info("Connecting to %s at %s.", self.broker_name, self.broker_ip)
            self.client.connect(host=self.broker_ip, port=1883, keepalive=60)
            self.client.loop_start()
        except Exception as excpt:
            Log.exception("[Exiting] Error connecting to broker: %s", excpt)
            self.client.loop_stop()
            sys.exit(-1)

    def send(self, topic, message):
        try:
            if self.client:
                self.client.publish(topic, message)
        except Exception as excpt:
            Log.info("Error publishing message: %s.", excpt)

    def subscribe(self, topic):
        """Subscribe to a topic (QoS = 0)."""
        self.client.subscribe(topic, qos=0)

    def unsubscribe(self, topic):
        """Unsubscribe to a topic."""
        self.client.unsubscribe(topic)

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        Log.info("[Exiting] Disconnected: %s", mqtt.error_string(rc))
        self.client.loop_stop()
        sys.exit(-1)

    # The callback for when the client receives a CONNACK response from the server.
    #@staticmethod
    def on_connect(self, client, userdata, flags, rc):
        Log.info("Connected with result code %s", rc)
        # Subscribing in on_connect() means if we lose connection and reconnect, subscriptions will
        # be renewed.
        #self.client.subscribe("SCHEDULER/LOCATE")
        self.is_connected = True
        self.subscribe("COMMAND" + "/#")
        self.subscribe("SCHEDULER/IDENT")
        self.subscribe("$SYS/broker/clients/total")
        self.subscribe("SYNCHRONIZE/DATA" + "/#")
        self.subscribe("SYNCHRONIZE/VERSION")
        self.subscribe("SYNCHRONIZE/CORE")
        self.subscribe("SYNCHRONIZE/GET")
        self.subscribe("ASSET/QUERY" + "/#")
        self.subscribe("STATUS/QUERY")
        self.subscribe("ENV/#")

    def on_message(self, client, userdata, msg):
        print(msg.topic, msg.payload)
        if "ENV/QUERY" in msg.topic:
            self.smart_module.get_env()

        elif "ASSET/QUERY" in msg.topic:
            asset_value = self.smart_module.get_asset_data()
            json_asset = str(self.smart_module.asset).replace("u'", "'").replace("'", "\"")
            self.send("ASSET/RESPONSE/" + self.smart_module.asset.id, json_asset)

        elif "ASSET/RESPONSE" in msg.topic:
            asset_id = msg.topic.split("/")[2]
            asset_info = json.loads(msg.payload)
            self.smart_module.push_data(asset_info["name"], asset_info["context"],
                asset_info["value_current"], asset_info["unit"])
            alert = Alert()
            alert.update_alert(asset_id)
            if alert.check_alert(asset_info["value_current"]):
                json_alert = str(alert).replace("u'", "'").replace("'", "\"")
                self.send("ALERT/" + asset_id, json_alert)

        elif "STATUS/QUERY" in msg.topic:
            self.smart_module.last_status = self.smart_module.get_status()
            json_payload = str(self.smart_module.last_status).replace("'", "\"")
            self.send("STATUS/RESPONSE/" + self.smart_module.hostname, json_payload)

        elif "STATUS/RESPONSE" in msg.topic:
            status_payload = json.loads(msg.payload.replace("'", "\""))
            self.smart_module.push_sysinfo("system", status_payload)

        elif "SCHEDULER/RESPONSE" in msg.topic:
            self.scheduler_found = True
            Log.info(msg.payload + " has identified itself as the Scheduler.")

        elif "SCHEDULER/QUERY" in msg.topic:
            if self.smart_module.scheduler:
                self.send("SCHEDULER/RESPONSE", self.smart_module.hostname)
                Log.info("Sent SCHEDULER/RESPONSE")

        elif "SYNCHRONIZE/VERSION" in msg.topic:
            self.send("SYNCHRONIZE/RESPONSE", self.smart_module.data_sync.read_db_version())

        elif "SYNCHRONIZE/GET" in msg.topic:
            if msg.payload == self.smart_module.hostname:
                self.smart_module.data_sync.publish_core_db(self)

        elif "SYNCHRONIZE/DATA" in msg.topic:
            self.smart_module.data_sync.synchronize_core_db(msg.payload)

        elif "$SYS/broker/clients/total" in msg.topic:
            if self.smart_module.scheduler:
                self.broker_connections = int(msg.payload)

        elif "ALERT" in msg.topic:
            asset_payload = json.loads(msg.payload)
            if not asset_payload["notify_enabled"]:
                return
            asset_id = msg.topic.split("/")[1]
            site_name = self.smart_module.name
            time_now = datetime.datetime.now()
            value_now = asset_payload["value_current"]
            try:
                if "email" in asset_payload["response"]:
                    notify = notification.Email()
                    notify.send(
                        notify.subject.format(site=site_name, asset=asset_id),
                        notify.message.format(
                            time=time_now, site=site_name, asset=asset_id, value=value_now)
                    )
                if "sms" in asset_payload["response"]:
                    notify = notification.SMS()
                    notify.send(
                        "from",
                        "to",
                        notify.message.format(
                            time=time_now, site=site_name, asset=asset_id, value=value_now)
                    )
            except Exception as excpt:
                Log.exception("Trying to send notification: %s.", excpt)
