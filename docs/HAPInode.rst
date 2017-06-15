HAPInode
========

Hardware Setup
--------------
The hardware for the HAPInode is based on arduino.
Since the main focus of HAPI is a system wide automation, arduinos that can easily incorporate WiFi and Bluetooth Low Energy are preferred. Conditional defines in the arduino software allow for ESP32, ESP8266 and mega2560 w/Ethernet modules.
The preferred development module is https://learn.sparkfun.com/tutorials/esp32-thing-hookup-guide, which includes the necessary WiFi, Bluetooth, external power and external battery interfaces.

Prototype Diagram
~~~~~~~~~~~~~~~~~
.. image:: img/HAPInode.png

Software Setup
--------------
Using the Arduino IDE download and flash the board with the `HAPInode code <https://github.com/mayaculpa/hapi/tree/dev/src/dumb_module/arduino/hapinode>`_.
