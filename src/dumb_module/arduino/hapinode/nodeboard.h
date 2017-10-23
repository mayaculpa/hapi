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

HAPI Remote Terminal Unit Firmware Code V3.1.1
Authors: Tyler Reed, Mark Miller
ESP Modification: John Archbold

Sketch Date: June 29th, 2017
Sketch Version: V3.1.1
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

enum pin_control_enum {
    UNUSED_PIN, // or reserved
    DIGITAL_INPUT_PIN,
    DIGITAL_INPUT_PULLUP_PIN,
    DIGITAL_OUTPUT_PIN,
    ANALOG_OUTPUT_PIN,
    ANALOG_INPUT_PIN
};


#ifdef HN_ENET             // Mega256
#define NUM_DIGITAL 54    // Number of digital I/O pins
#define NUM_ANALOG  16    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value
// Default pin allocation
#define DHT_PIN 12        // Reserved pin for DHT-22 sensor
#define WIRE_PIN  13      // Reserved pin for 1-Wire bus
#define LED_PIN 2         // Use the built-in led for visual feedback
#define TDS_DRIVE1 33     // Reserved pin for TDS probe
#define TDS_INPUT1 25     // Reserved pin for TDS probe
#define TDS_INPUT2 26     // Reserved pin for TDS probe
#define TDS_DRIVE2 27     // Reserved pin for TDS probe

#define cWatr_PIN 4       // Water pump control pin
#define sFlow_PIN 36      // Water flow sensor pin
#define cFill_PIN 2       // Fill pump control pin
#define sFloat_PIN 39      // Fill float sensor pin
#define cNutr_PIN 15      // Nutrient pump control pin
#define sTDS_PIN 25       // TDS sensor pin
#define cpHUp_PIN 17      // pHUp pump control pin
#define spH_PIN   35      // pH sensor pin
#define cpHDn_PIN 16      // pHDown pump control pin
#define cLamp_PIN 14      // Lamp control pin
#define sLux_PIN  4       // Light sensor pin

// Default pin modes
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  // digital
  UNUSED_PIN,               //  0
  UNUSED_PIN,               //  1
  DIGITAL_OUTPUT_PIN,       //  2
  DIGITAL_OUTPUT_PIN,       //  3
  UNUSED_PIN,               //  4
  DIGITAL_OUTPUT_PIN,       //  5
  DIGITAL_OUTPUT_PIN,       //  6
  DIGITAL_OUTPUT_PIN,       //  7
  DIGITAL_OUTPUT_PIN,       //  8
  DIGITAL_OUTPUT_PIN,       //  9
  UNUSED_PIN,               // 10
  DIGITAL_INPUT_PULLUP_PIN, // 11
  DIGITAL_INPUT_PIN,        // 12
  DIGITAL_OUTPUT_PIN,       // 13
  UNUSED_PIN,               // 14
  UNUSED_PIN,               // 15
  UNUSED_PIN,               // 16
  UNUSED_PIN,               // 17
  UNUSED_PIN,               // 18
  UNUSED_PIN,               // 19
  UNUSED_PIN,               // 20
  UNUSED_PIN,               // 21
  DIGITAL_OUTPUT_PIN,       // 22
  DIGITAL_OUTPUT_PIN,       // 23
  DIGITAL_OUTPUT_PIN,       // 24
  DIGITAL_OUTPUT_PIN,       // 25
  DIGITAL_OUTPUT_PIN,       // 26
  DIGITAL_OUTPUT_PIN,       // 27
  DIGITAL_INPUT_PIN,        // 28
  DIGITAL_INPUT_PIN,        // 29
  DIGITAL_INPUT_PIN,        // 30
  DIGITAL_INPUT_PIN,        // 31
  DIGITAL_INPUT_PIN,        // 32
  DIGITAL_INPUT_PIN,        // 33
  DIGITAL_INPUT_PIN,        // 34
  DIGITAL_INPUT_PIN,        // 35
  DIGITAL_INPUT_PIN,        // 36
  DIGITAL_INPUT_PIN,        // 37
  DIGITAL_INPUT_PIN,        // 38
  DIGITAL_INPUT_PIN,        // 39
  DIGITAL_INPUT_PIN,        // 40
  DIGITAL_INPUT_PIN,        // 41
  DIGITAL_INPUT_PIN,        // 42
  DIGITAL_INPUT_PIN,        // 43
  DIGITAL_INPUT_PIN,        // 44
  DIGITAL_INPUT_PIN,        // 45
  DIGITAL_INPUT_PIN,        // 46
  DIGITAL_INPUT_PIN,        // 47
  DIGITAL_INPUT_PULLUP_PIN, // 48
  DIGITAL_INPUT_PULLUP_PIN, // 49
  UNUSED_PIN,               // 50
  UNUSED_PIN,               // 51
  UNUSED_PIN,               // 52
  UNUSED_PIN,               // 53
  // analog
  ANALOG_INPUT_PIN,         // 54
  ANALOG_INPUT_PIN,         // 55
  ANALOG_INPUT_PIN,         // 56
  ANALOG_INPUT_PIN,         // 57
  ANALOG_INPUT_PIN,         // 58
  ANALOG_INPUT_PIN,         // 59
  ANALOG_INPUT_PIN,         // 60
  ANALOG_INPUT_PIN,         // 61
  ANALOG_INPUT_PIN,         // 62
  ANALOG_INPUT_PIN,         // 63
  ANALOG_INPUT_PIN,         // 64
  ANALOG_INPUT_PIN,         // 65
  UNUSED_PIN,               // 66
  UNUSED_PIN,               // 67
  UNUSED_PIN,               // 68
  UNUSED_PIN                // 69
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
#define DHT_PIN 2        // Reserved pin for DHT-22 sensor
#define WIRE_PIN  13      // Reserved pin for 1-Wire bus
#define PH_SENSORPIN 14   // Reserved pin for pH probe
#define TDS_SENSORPIN 15  // Reserved pin for TDS probe
#define LED_PIN 5         // Use the built-in led for visual feedback

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
#define sLamp_PIN A0      // Analog Lamp sensor pin
#define sLux_PIN  32      // Light sensor pin
#define spH_PIN   35      // pH sensor pin

#define sTDS_PIN 34       // Analog TDS sensor pin
#define sWtrFlow_PIN 36   // Water flow sensor pin
#define cWtrPump_PIN 4    // Water pump control pin
#define cWtrFill_PIN 5    // Fill pump control pin
#define sWtrFloat_PIN 39  // Fill float sensor pin

#define SDA_PIN 21        // Default pin for I2C
#define SCL_PIN 22        // Default pin for I2C


// Default pin modes
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  // digital
  DIGITAL_OUTPUT_PIN, //  0
  DIGITAL_OUTPUT_PIN, //  1
  DIGITAL_OUTPUT_PIN, //  2
  DIGITAL_INPUT_PIN,  //  3
  DIGITAL_OUTPUT_PIN, //  4
  DIGITAL_OUTPUT_PIN, //  5
  UNUSED_PIN,         //  6
  UNUSED_PIN,         //  7
  UNUSED_PIN,         //  8
  UNUSED_PIN,         //  9
  UNUSED_PIN,         // 10
  UNUSED_PIN,         // 11
  DIGITAL_OUTPUT_PIN, // 12
  DIGITAL_OUTPUT_PIN, // 13
  DIGITAL_OUTPUT_PIN, // 14
  DIGITAL_OUTPUT_PIN, // 15
  DIGITAL_OUTPUT_PIN, // 16
  ANALOG_INPUT_PIN    // 17
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
#define LED_PIN 2         // Use the built-in led for visual feedback

#define DHT_PIN 13        // Reserved pin for DHT-22 sensor
#define WIRE_PIN 14       // Reserved pin for 1-Wire bus
#define SCL_PIN 22        // Default pin for I2C
#define SDA_PIN 21        // Default pin for I2C

#define cWtrPump_PIN 4    // Water pump control pin
#define sWtrFlow_PIN 36   // Water flow sensor pin
#define cWtrFill_PIN 5    // Fill pump control pin
#define sWtrFloat_PIN 39  // Fill float sensor pin

#define cNutr_PIN 15      // Nutrient pump control pin
#define sTDS_PIN 34       // Analog TDS sensor pin
#define cTDSO1_PIN 33     // Drive1 pin for TDS probe
#define sTDSI1_PIN 25     // Input1 pin for TDS probe
#define sTDSI2_PIN 26     // Input2 pin for TDS probe
#define cTDSO2_PIN 27     // Drive2 pin for TDS probe

#define cpHUp_PIN 17      // pHUp pump control pin
#define cpHDn_PIN 16      // pHDown pump control pin
#define spH_PIN   35      // pH sensor pin

#define cLamp_PIN 12      // Lamp control pin
#define sLux_PIN  32      // Light sensor pin

// Default pin modes
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  // digital
  UNUSED_PIN,         //  0
  UNUSED_PIN,         //  1
  DIGITAL_OUTPUT_PIN, //  2
  UNUSED_PIN,         //  3
  DIGITAL_OUTPUT_PIN, //  4
  DIGITAL_OUTPUT_PIN, //  5
  UNUSED_PIN,         //  6
  UNUSED_PIN,         //  7
  UNUSED_PIN,         //  8
  UNUSED_PIN,         //  9
  UNUSED_PIN,         // 10
  UNUSED_PIN,         // 11
  DIGITAL_OUTPUT_PIN, // 12
  DIGITAL_OUTPUT_PIN, // 13
  DIGITAL_OUTPUT_PIN, // 14
  DIGITAL_OUTPUT_PIN, // 15
  UNUSED_PIN,         // 16
  UNUSED_PIN,         // 17
  DIGITAL_OUTPUT_PIN, // 18
  DIGITAL_OUTPUT_PIN, // 19
  UNUSED_PIN,         // 20
  DIGITAL_OUTPUT_PIN, // 21
  DIGITAL_OUTPUT_PIN, // 22
  DIGITAL_OUTPUT_PIN, // 23
  UNUSED_PIN,         // 24
  DIGITAL_OUTPUT_PIN, // 25
  DIGITAL_OUTPUT_PIN, // 26
  DIGITAL_OUTPUT_PIN, // 27
  UNUSED_PIN,         // 28
  UNUSED_PIN,         // 29
  UNUSED_PIN,         // 30
  UNUSED_PIN,         // 31
  DIGITAL_OUTPUT_PIN, // 32
  DIGITAL_OUTPUT_PIN, // 33
  DIGITAL_OUTPUT_PIN, // 34
  DIGITAL_OUTPUT_PIN, // 35
  UNUSED_PIN,         // 36
  UNUSED_PIN,         // 37
  UNUSED_PIN,         // 38
  UNUSED_PIN,         // 39
  UNUSED_PIN,         // 40
  UNUSED_PIN,         // 41
  UNUSED_PIN,         // 42
  UNUSED_PIN,         // 43
  UNUSED_PIN,         // 44
  UNUSED_PIN,         // 45
  UNUSED_PIN,         // 46
  UNUSED_PIN,         // 47
  UNUSED_PIN,         // 48
  UNUSED_PIN,         // 49
  UNUSED_PIN,         // 50
  UNUSED_PIN,         // 51
  UNUSED_PIN,         // 52
  UNUSED_PIN,         // 53
  // analog
  ANALOG_INPUT_PIN,   // 54
  ANALOG_INPUT_PIN,   // 55
  ANALOG_INPUT_PIN,   // 56
  ANALOG_INPUT_PIN,   // 57
  ANALOG_INPUT_PIN,   // 58
  ANALOG_INPUT_PIN,   // 59
  ANALOG_INPUT_PIN,   // 60
  ANALOG_INPUT_PIN,   // 61
  ANALOG_INPUT_PIN,   // 62
  ANALOG_INPUT_PIN,   // 63
  ANALOG_INPUT_PIN,   // 64
  ANALOG_INPUT_PIN,   // 65
  UNUSED_PIN,         // 66
  UNUSED_PIN,         // 67
  UNUSED_PIN,         // 68
  UNUSED_PIN          // 69
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
