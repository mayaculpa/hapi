System Overview
===============

The HAPI system is based on low cost micro-controllers providing sufficient computing power to monitor and control all local production resources. These resources are comprised of the sensors that monitor the environment and growing conditions, and the controls that affect these conditions. The results of these activities are published using a standard messaging protocol called MQTT. The information that is published can then be used to analyze the conditions, monitor the controls, and change the operation of the system.

.. This document serves to give an overview of the system and its components.

Below is a draft of the HAPI system architecture. Please note it is not fully up to date

.. image:: img/system-overview.png

Components
-------

HAPImodule
~~~~~~~~~~~~
HAPImodules are devices with a high computational capability that run system, sensor and control code. Currently the supported hardware for Smart Modules is a Raspberry Pi Zero W or 3B. Multiple HAPImodules can exist within the system and collaborate to determine the tasks performed by each module. One HAPImodule is the MQTT Broker (Server) and is responsible for storing all the data being transmitted. If for some reason this Server is unreachable (configuration problems or hardware failure, for instance), any other HAPImodule within the system can step up and take its place.

**Features:**

* Focused on the needs of Urban and Controlled-Environment Agriculture
* Supports multiple sites for a single user
* Open source designs and code (user isn’t stuck with proprietary technology)
* Wide & growing range of sensor support
* User-definable Alerts
* User-definable Schedule
* Control equipment based on schedule, sensor values or manually.
* WiFi Capable (configured via FMS Application)
* Seamlessly integrate with other Smart Modules
* Integrated, battery-backed, real-time clock
* Simple, durable design and enclosure
* Waterproof, weather-resistant enclosures
* Optional data push to cloud visualization services
* Automatic fail-over of communications and scheduling functions (fault-tolerant mesh)
* Minimal User Configuration (Set WiFi info and you’re done)

.. todo: we should provide other resources on MQTT, including an explanation of its role in the system. Perhaps too we should move the technical details someplace else.

HAPInode
~~~~~~~~~~~
The hardware for the HAPInode is based on arduino.
Since the main focus of HAPI is a system wide automation, arduinos that can easily incorporate WiFi and Bluetooth Low Energy are preferred. Conditional defines in the arduino software allow for ESP32, ESP8266 and mega2560 w/Ethernet modules.
The preferred development module is (https://learn.sparkfun.com/tutorials/esp32-thing-hookup-guide), which includes the necessary WiFi, Bluetooth, external power and external battery interfaces.

**Features:**

* Run on Arduino, ESP8266 (e.g. NodeMCU) or ESP32 (e.g. WROOM32)
* Targeted to DIY/Makers, Technicians, Experimenters, Hobbyists
* User-configurable sensor and control configurations
* Seamlessly integrate with other HAPI Smart Modules and Nodes
* Open source designs and code

Facility Management System (FMS) Android App
------------------------------------------
The FMS is an Android application for managing and monitoring the HAPI system.

* Configure WiFi settings for Smart Modules
* See all sensor values at a touch
* Manage schedule for collecting sensor data, weather data, system health and checking alerts
* Set Alert parameters and notification preferences
* View data in Standard or Metric Units
* Open source designs and code
* Integration with Weather Underground (optional via free subscription)
* Access to Visualization Dashboards (optional via paid subscription)

System Features
---------------

Job scheduling
~~~~~~~~~~~~~~
The HAPI platform features an in-process scheduler for running periodic jobs. Jobs can be control functions, such as turning a light or pump on. Jobs can also serve monitoring purposes, such as gathering sensor data. Job information is stored in the database, in the table `schedule`. Any Smart Module can run the job scheduling code (i.e. "become the Scheduler"). HAPI Nodes cannot become the Scheduler.

Technical Description
^^^^^^^^^^^^^^^^^^^^^
When a Smart Module starts, it publishes on message on the MQTT topic SCHEDULER/QUERY, essentially asking for the Scheduler to respond. If another module on the network is running the job scheduling code, it responds to the to the message and no further action is taken. If there is no response to the message, the starting module runs the job scheduling code itself,  announces that it is now the Scheduler and listens on the SCHEDULER/QUERY topic for other Smart Modules that are discovering the scheduler.

The HAPI Scheduler uses [the schedule package](https://pypi.python.org/pypi/schedule) created by Daniel Badr. Documentation can be [found here](https://schedule.readthedocs.io/en/stable/).

Auto-Discovery
~~~~~~~~~~~~~~
All modules (Smart or Dumb) have the capability to automatically detect and connect to one another without user configuration or intervention. To accomplish this, the HAPI platform uses a zero-configuration networking implementation called `Avahi`_. Similar to Apple's Bonjour, Avahi allows modules to dynamically name themselves and discover neighboring modules.

Technical Description
^^^^^^^^^^^^^^^^^^^^^
For Smart Modules, the original Raspian images are modified to include the avahi daemon. When a module boots, it automatically runs this daemon. When a Smart Module starts, to attempts to contact the MQTT broker, "mqttbroker.local". This machine is acts as the communications hub for all HAPI-based facilities. If the Smart Module's search for the MQTT broker is not successful, it changes it's own name to "mqttbroker.local" and becomes the communications hub for the site.

.. _Avahi: https://en.wikipedia.org/wiki/Avahi_(software)
