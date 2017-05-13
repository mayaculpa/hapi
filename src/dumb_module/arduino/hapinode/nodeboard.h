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

#ifndef HAPIBOARD_H
#define HAPIBOARD_H

#ifdef HN_2560
#define NUM_DIGITAL 54    // Number of digital I/O pins
#define NUM_ANALOG  16    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value
// Default pin allocation
#define LIGHT_SENSORPIN 2 // Reserved pin for a Light sensor
#define FLOW_SENSORPIN 4  // Reserved pin for a flow sensor
#define DHT_SENSORPIN 12  // Reserved pin for DHT-22 sensor
#define ONE_WIRE_BUS 8   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN A1   // Reserved pin for pH probe
#define TDS_SENSORPIN 15  // Reserved pin for TDS probe

#define cWatr_PIN 12      // Water pump control pin
#define sWatr_PIN A1      // Water pump sensor pin
#define cFill_PIN 12      // Fill pump control pin
#define sFill_PIN A1      // Fill pump sensor pin
#define cNutr_PIN 12      // Nutrient pump control pin
#define sNutr_PIN A1      // Nutrient pump sensor pin
#define cpHUp_PIN 12      // pHUp pump control pin
#define spHUp_PIN A1      // pHUp pump sensor pin
#define cpHDn_PIN 12      // pHDown pump control pin
#define spHDn_PIN A1      // pHDown pump sensor pin
#define cLamp_PIN 12      // Lamp control pin
#define sLamp_PIN A1      // Lamp sensor pin

// Default pin modes
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 3, 3, 0, 3, 3, 3, 3, 3,   //  0 -  9
  0, 2, 1, 3, 0, 0, 0, 0, 0, 0,   // 10 - 19
  0, 0, 3, 3, 3, 3, 3, 3, 1, 1,   // 20 - 29
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1,   // 30 - 39
  1, 1, 1, 1, 1, 1, 1, 1, 2, 2,   // 40 - 49
  0, 0, 0, 0,                     // 50 - 53
                                  // ANALOG
  5, 5, 5, 5, 5, 5, 5, 5, 5, 5,   // 54 - 63
  5, 5, 0, 0, 0, 0                // 64 - 69
};

// Default pin states
// Defaults determine the value of output pins with the HN initializes
// 0 = LOW, 1 = HIGH
int pinDefaults[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 1, 1, 0, 1, 1, 1, 1, 1,   //  0 -  9
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 10 - 19
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 20 - 29
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 30 - 39
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 40 - 49
  0, 0, 0, 0,                     // 50 - 53
                                  // ANALOG
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 54 - 63
  0, 0, 0, 0, 0, 0                // 64 - 69
};

#endif

#ifdef HN_ESP8266
#define NUM_DIGITAL 17    // Number of digital I/O pins
#define NUM_ANALOG  1     // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value

// Default pin allocation
#define LIGHT_SENSORPIN 2 // Reserved pin for a Light sensor
#define FLOW_SENSORPIN 4  // Reserved pin for a flow sensor
#define DHT_SENSORPIN 12  // Reserved pin for DHT-22 sensor
#define ONE_WIRE_BUS 13   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN 14   // Reserved pin for pH probe
#define TDS_SENSORPIN 15  // Reserved pin for TDS probe

#define cWatr_PIN 12      // Water pump control pin
#define sWatr_PIN A0      // Water pump sensor pin
#define cFill_PIN 12      // Fill pump control pin
#define sFill_PIN A0      // Fill pump sensor pin
#define cNutr_PIN 12      // Nutrient pump control pin
#define sNutr_PIN A0      // Nutrient pump sensor pin
#define cpHUp_PIN 12      // pHUp pump control pin
#define spHUp_PIN A0      // pHUp pump sensor pin
#define cpHDn_PIN 12      // pHDown pump control pin
#define spHDn_PIN A0      // pHDown pump sensor pin
#define cLamp_PIN 12      // Lamp control pin
#define sLamp_PIN A0      // Lamp sensor pin

// Default pin modes
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  3, 3, 3, 1, 3, 3, 0, 0,   //  0 -  7  // Digital i/o
  0, 0, 0, 0, 3, 3, 3, 3,   //  8 - 15
  3,                        // 16
  5                         // A0       //Analog Input
};

// Default pin states
// Defaults determine the value of output pins with the HN initializes
// 0 = LOW, 1 = HIGH
int pinDefaults[NUM_DIGITAL+NUM_ANALOG] = {
  1, 1, 1, 1, 1, 1, 0, 0,   //  0 -  7  // Digital i/o
  0, 0, 0, 0, 1, 1, 1, 1,   //  8 - 15
  1,                        // 16
  5                         // A0       //Analog Input
};
#endif

#ifdef HN_ESP32
#define NUM_DIGITAL 54    // Number of digital I/O pins
#define NUM_ANALOG  16    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value
// Default pin allocation
#define LIGHT_SENSORPIN 2 // Reserved pin for a Light sensor
#define FLOW_SENSORPIN 4  // Reserved pin for a flow sensor
#define DHT_SENSORPIN 12  // Reserved pin for DHT-22 sensor
#define ONE_WIRE_BUS 13   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN 14   // Reserved pin for pH probe
#define TDS_SENSORPIN 15  // Reserved pin for TDS probe

#define cWatr_PIN 12      // Water pump control pin
#define sWatr_PIN A1      // Water pump sensor pin
#define cFill_PIN 12      // Fill pump control pin
#define sFill_PIN A1      // Fill pump sensor pin
#define cNutr_PIN 12      // Nutrient pump control pin
#define sNutr_PIN A1      // Nutrient pump sensor pin
#define cpHUp_PIN 12      // pHUp pump control pin
#define spHUp_PIN A1      // pHUp pump sensor pin
#define cpHDn_PIN 12      // pHDown pump control pin
#define spHDn_PIN A1      // pHDown pump sensor pin
#define cLamp_PIN 12      // Lamp control pin
#define sLamp_PIN A1      // Lamp sensor pin

// Default pin modes
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 3, 0, 3, 3, 0, 0, 0, 0,   //  0 -  9
  0, 0, 3, 3, 3, 3, 0, 0, 3, 3,   // 10 - 19
  0, 3, 3, 3, 0, 3, 3, 3, 0, 0,   // 20 - 29
  0, 0, 3, 3, 3, 3, 0, 0, 0, 0,   // 30 - 39
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 40 - 49
  0, 0, 0, 0,                     // 50 - 53
                                  // ANALOG
  5, 5, 5, 5, 5, 5, 5, 5, 5, 5,   // 54 - 63
  5, 5, 0, 0, 0, 0                // 64 - 69
};

// Default pin states
// Defaults determine the value of output pins with the HN initializes
// 0 = LOW, 1 = HIGH
int pinDefaults[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 1, 1, 0, 1, 1, 1, 1, 1,   //  0 -  9
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 10 - 19
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 20 - 29
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 30 - 39
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 40 - 49
  0, 0, 0, 0,                     // 50 - 53
                                  // ANALOG
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   // 54 - 63
  0, 0, 0, 0, 0, 0                // 64 - 69
};
#endif

#endif //HAPIBOARD_H
