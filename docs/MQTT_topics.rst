MQTT Topics
============

In the HAPI system devices are either **modules** or **nodes**. Both types of devices can have sensors and controls attached to them. Modules are based on Raspberry Pis, while nodes are based on arduinos.
The communication of sensor data or control commands uses the **MQTT protocol**. This protocol has two important operations called publishing and subscribing. In the HAPI system, a **local broker** is responsible for these operations.

The HAPI philosophy is that any module can assume the role of local broker. It then has the role of publishing controls based on a schedule, on sensor values or on exceptions, as well as co-ordinating the collection and storage of the sensor data.

A HAPI device can publish its sensor data and subscribe to controls for actions. A HAPI device could also subscribe to sensor data for processing and generate controls based on schedules or on these sensor data values.

A HAPImodule can both publish and subscribe to data as well as publish and subscribe to controls.
A HAPImodule can also assume the role of the MQTT local broker.
A HAPInode can only publish data and subscribe to controls.

Device Naming
-------------

Each device has a unique ID, called the deviceID, derived from its node type and the unique mac address that is hardcoded into the device at the time of manufacture.

Each sensor or control is called an asset and has an assetID that is unique to the function of the asset.

The deviceID and the assetID are used to uniquely identify the topic that sensor data is published to or that control information is received from.

HAPImodule
----------

HAPImodules have a unique **deviceID** of the form HN1xxxxxx, where HN1 identifies that this is a module (Raspberry Pi Zero) and xxxxxx is the low three bytes of the mac address of its WiFi module. (The high three bytes identify the manufacturer of the WiFi integrated circuit).

In python, the mac address is found using:

  *from uuid import getnode as get_mac*
  
  *mac = get_mac()*

HAPInode
--------

HAPInodes have a unique **deviceID** of the form HNnxxxxxx, where HNn identifies the type of the node, (ESP32(HN5), ESP8266(HN4), or mega2560(HN3)) and xxxxxx is the low three bytes of the mac address of its WiFi module. (The high three bytes identify the manufacturer of the WiFi integrated circuit).

The HAPInode deviceID is also its hostname.


In arduino with a WiFi module, the mac address is found using:

  *mac = WiFi(mac);*


Module, Node types
------------------

Current module, node types include -
  
+------+----------------------------------+
| type |  Meaning                         | 
+------+----------------------------------+
| HN1  |  Raspberry pi zero               |
+------+----------------------------------+
| HN2  |  Raspberry pi 3                  |
+------+----------------------------------+
| HN3  |  Arduino mega2560                |
+------+----------------------------------+
| HN4  |  Arduino ESP8266                 |
+------+----------------------------------+
| HN5  |  Arduino ESP32 (WROOM)           |
+------+----------------------------------+


AssetID
----------
Each asset has a unique **assetID**. The assetId is derived from its asset type and its function.
The *asset type* is a two letter identification that groups the assets into their functional blocks.

Current asset type include -
  
+------+----------------------------------+
| Type |  Meaning                         | 
+------+----------------------------------+
|  wt  |  One-wire temperature device     |
+------+----------------------------------+
|  ht  |  DHT device                      |
+------+----------------------------------+
|  rt  |  RTC device                      |
+------+----------------------------------+
|  ph  |  ph device                       |
+------+----------------------------------+
|  ec  |  Electrical conductivity device  |
+------+----------------------------------+
|  ds  |  Total dissolved solids device   |
+------+----------------------------------+
|  lx  |  Light device                    |
+------+----------------------------------+
|  rl  |  Relay                           |
+------+----------------------------------+
  
  
The asset function relates to its use at the node. The asset function is a freeform, but unique, identifcation.

Examples are 'watertemp1', 'nutrienttemp'. 'waterprobe', 'lightrelay', 'waterfill', 'nutrientpump'. 

MQTT topics
-----------
Each topic is built from the nature of the topic, the activity to be undertaken, and optionally, the deviceID and optionally, the assetID.
The first part is the nature of the topic, e.g. STATUS, ASSET, EXCEPTION, CONFIG
The next part is the activity associated with that topic, e.g. QUERY, RESPONSE, SET, CLEAR
The next, optional, part is the scope associated with that topic which may idenitify a unique device and, optionally, asset for the topic.

-------------------

Sample topics
-------------
Status Query
~~~~~~~~~~~~
* Nature: STATUS  
* Activity: QUERY  
* Payload: JSON string *(content not used at this stage)*  

**Example: Query the status of ALL devices**  
* STATUS/QUERY/  
* *payload:* '{"device": "*"}'  

Status Response
~~~~~~~~~~~~~~~
* Nature: STATUS  
* Activity: RESPONSE  
* Payload: JSON string containing data  
* Payload contains JSON encoded fields identifying the time, the value, and the units.  
  
**Example: Response from HN1123456 (RPiz with mac ID 123456)**

* STATUS/RESPONSE/HN1123456/wt/watertemp1  
+ *payload:* {"data": "[1234567890, 17.44, "C"]"}  
* STATUS/RESPONSE/HN1123456/ht/airhumidity 
+ *payload:* {"data": "[1234567899, 53.55, "%"]"}  

*Note that multiple messages may be generated to identify all the assets associated with a device, as the maximum MQTT payload length is limited to approximately 96 bytes, or 128 byte mqtt message length.*
  
Asset Query
~~~~~~~~~~~
* Nature: STATUS  
* Activity: QUERY  
* Payload: JSON string *(content not used at this stage)*

**Example: Query the status of ALL humidity devices**  
* ASSET/QUERY/+/ht  
* *payload:* '{"device": "*"}' 

Asset Response
~~~~~~~~~~~~~~
* Nature: STATUS  
* Activity: RESPONSE  
* Payload: JSON string containing data  
* Payload contains JSON encoded fields identifying the time, the value, and the units.  

**Example: Response from HN1123456 (RPiz with mac ID 123456) and HN5678345 (ESP32 with macID 678345)**

+ STATUS/RESPONSE/HN1123456/ht/airhumidity 
* *payload:* {"data": "[1234567899, 53.55, "%"]"}  
+ STATUS/RESPONSE/HN5678345/ht/airhumidity 
* *payload:* {"data": "[1234567910, 78.23, "%"]"}
  
-------------------
