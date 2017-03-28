# -*- coding: utf-8 -*-
#!/usr/bin/env python

'''
HAPI Master Controller v2.1.1
Author: Tyler Reed
Release: December 2016 Beta
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

import sys
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("test")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def main(args):
    ID = ''
    #if len(args) < 2:
    if len(args) > 0:
        #ID = str(args[1])
        ID = str(args[0])

    # Members of the paho.mqtt.client package need to be prefixed with their package name
    client = mqtt.Client(client_id=ID, clean_session=True, userdata=None, protocol=mqtt.MQTTv31)
    print "Client created."

    # Setup callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    print "Callbacks set."

    # Dedicated host name over Avahi
    client.connect("sitecontroller.local", 1883, 5)
    print "Connected!"
    client.loop_forever()


if __name__ == '__main__':
    main(sys.argv)
