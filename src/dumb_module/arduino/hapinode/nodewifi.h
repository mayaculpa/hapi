/*
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

HAPI Remote Terminal Unit Firmware Code v3.0.0
Authors: Tyler Reed, Mark Miller
ESP Modification: John Archbold

Sketch Date: May 2nd 2017
Sketch Version: v3.0.0
Implement of MQTT-based HAPInode (HN) for use in Monitoring and Control
Implements mDNS discovery of MQTT broker
Implements definitions for 
  ESP-NodeMCU
  ESP8266
  WROOM32
Communications Protocol
  WiFi
Communications Method
  MQTT        Listens for messages on Port 1883
*/

#ifndef HAPIWiFi_H
#define HAPIWiFi_H

// ==============================================================
// Make sure to update this for your own WiFi and/or MQTT Broker!
// ==============================================================

#define MQTT_broker_address F("mqttbroker")    // IP address of mqtt broker
#define MQTT_broker_username F("mqttuser")      // Required if broker security is enabled
#define MQTT_broker_password F("mqttpass")
#define MQTT_port 1883

#define UDP_port 2390

#ifdef HN_WiFi
#define HAPI_SSID F("HAPInet")
#define HAPI_PWD  F("HAPIconnect")
#endif

#endif //HAPIWiFi_H
