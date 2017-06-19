MQTT Topics
============

In the HAPI system devices are either **modules** or **nodes**. Both types of devices can have sensors and controls attached to them. Modules are based on Raspberry Pis, while nodes are based on arduinos.
The communication of sensor data or control commands uses the **MQTT protocol**. This protocol has two important operations called publishing and subscribing. In the HAPI system, a **local broker** is responsible for these operations.

The HAPI philosophy is that any module can assume the role of local broker. It then has the role of publishing controls based on a schedule, on sensor values or on exceptions, as well as co-ordinating the collection and storage of the sensor data.

A HAPI device can publish its sensor data and subscribe to controls for actions. A HAPI device could also subscribe to sensor data for processing and generate controls based on schedules or on these data values.

A HAPImodule can both publish and subscribe to data as well as publish and subscribe to controls.
A HAPImodule can also assume the role of the MQTT local broker.
A HAPInode can only publish data and subscribe to controls.

Device Naming
-------------

Each device has a unique ID, called the deviceID, derived from its type and the unique mac address that is hardcoded into the device at the time of manufacture. Each sensor or control is called an asset and has an assetID that is unique to the function of the asset. The deviceID and the assetID are used to uniquely identify the topic that sensor data is published to or that control information is received from.

HAPImodule
----------

HAPImodules have a deviceID of the form HN1xxxxxx, where HN1 identifies that this is a module (Raspberry Pi Zero) and xxxxxx is the low three bytes of the mac address of its WiFi module. (The high three bytes identify the manufacturer of the WiFi integrated circuit).
In python, the mac address is found using:
`from uuid import getnode as get_mac`
`mac = get_mac()`

HAPInode
--------
Each node has a unique ID derived from its type (a node and its arduino type) and the unique mac address that is hardcoded into the device at the time of manufacture.
HAPInodes have a name of the form HNnxxxxxx, where HNn identifies that this is a node (ESP32(HN5), ESP8266(HN4), or mega2560(HN3)) and xxxxxx is the low three bytes of the mac address of its WiFi module. (The high three bytes identify the manufacturer of the WiFi integrated circuit).
In arduino with a WiFi module, the mac address is found using:
`mac = WiFi(mac); `

MQTT topics
-----------
Each topic is built from the nature of the topic, the activity to be undertaken, and optionally, the deviceID and the assetID.
The first part is the nature of the topic, e.g. STATUS, ASSET, EXCEPTION, CONFIG
The next part is the activity associated with that topic, e.g. QUERY, RESPONSE, SET, CLEAR

Sample topics
-------------
Status Query
~~~~~~~~~~~~
Query the status of ALL devices
topic: STATUS/QUERY/
message: {"device": "*"}

Status Response
~~~~~~~~~~~~~~~
topic: STATUS/RESPONSE/HN1123456
Message contains JSON encoded fields identifying the device, name, and assets.
message: {"device": "HN1123456", "name": "TomatoBay1", "Asset": "[hum, tmp, wtm, lux]"}
Note that multiple messages may be generated to identify all the assets associated with a device, as the maximum MQTT payload length is limited to approximately 96 bytes, or 128 byte message length.

Asset Query
~~~~~~~~~~~
Query the value of the hum (humidity) asset of all devices with humidity assets
topic: ASSET/QUERY/+/hum
message: {"device": "*"}

Asset Response
~~~~~~~~~~~~~~
topic: ASSET/RESPONSE/HN1123456/hum
Message contains JSON encoded fields identifying the device, time, asset value, and units.
message: {"device": "HN1123456", "time": 123456, "hum": 67, "units": "%"}
