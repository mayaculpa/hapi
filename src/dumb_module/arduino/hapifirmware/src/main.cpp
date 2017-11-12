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

HAPI Remote Terminal Unit Firmware Code v2.2.0
Authors: Tyler Reed, Mark Miller
ESP Modification: John Archbold
Release: September 2016 v2.2.0 Debug
Sketch Date: April 22nd 2017
Sketch Version: v2.2.0
Implements of Remote Terminal Unit (RTU) for use in Monitoring and Control
Implements HAPI Command Language Interpreter (CLI) for the Arduino Mega
Implements definitions for Mega2560-ethernet, Mega2560-usb, ESP-NodeMCU
Listens for Telnet connections on Port 80
Target Board: NodeMCU
Communications Protocol: Ethernet, USB
*/


//**** Begin Board Selection Section ****
//#define RTU_ENET          // Define for Arduino 2560 via Ethernet shield
//#define RTU_USB           // Define for Arduino 2560 via USB
//#define RTU_UNO           // Define for Arduino UNO via USB
#define RTU_ESP           // Define for NodeMCU, or ESP8266-based device

// Required for ESP (WiFi) connection
#ifndef HAPI_SSID
#define HAPI_SSID "your_ssid"
#define HAPI_PWD  "your_ssid"
#endif

//**** Begin Board Selection Section ****


#include <DHT.h>
#include <SPI.h>
#ifdef RTU_ESP
#include <ESP8266WiFi.h>
#endif
#ifdef RTU_ENET
#include <Ethernet.h>
#endif
#include <stdlib.h>
#include <math.h>
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Pin type description used for all boards
enum pin_control_enum {
    UNUSED_PIN, // or reserved
    DIGITAL_INPUT_PIN,
    DIGITAL_INPUT_PULLUP_PIN,
    DIGITAL_OUTPUT_PIN,
    ANALOG_OUTPUT_PIN,
    ANALOG_INPUT_PIN
};

#ifdef RTU_ENET
#define NUM_DIGITAL 54    // Number of digital I/O pins
#define NUM_ANALOG  16    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value

// Default pin allocation
#define ONE_WIRE_BUS 8   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN A1  // Reserved pin for pH probe
#define DHTTYPE DHT22    // Sets DHT type
#define DHTPIN 12        // Reserved pin for DHT-22 sensor

// Default pin modes
// Analog input pins are assumed to be used as analog input pins
enum pin_control_enum pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  // DIGITAL
  UNUSED_PIN,                //  0
  UNUSED_PIN,                //  1
  DIGITAL_OUTPUT_PIN,        //  2
  DIGITAL_OUTPUT_PIN,        //  3
  UNUSED_PIN,                //  4
  DIGITAL_OUTPUT_PIN,        //  5
  DIGITAL_OUTPUT_PIN,        //  6
  DIGITAL_OUTPUT_PIN,        //  7
  DIGITAL_OUTPUT_PIN,        //  8
  DIGITAL_OUTPUT_PIN,        //  9
  UNUSED_PIN,                // 10
  DIGITAL_INPUT_PULLUP_PIN,  // 11
  DIGITAL_INPUT_PIN,         // 12
  DIGITAL_OUTPUT_PIN,        // 13
  UNUSED_PIN,                // 14
  UNUSED_PIN,                // 15
  UNUSED_PIN,                // 16
  UNUSED_PIN,                // 17
  UNUSED_PIN,                // 18
  UNUSED_PIN,                // 19
  UNUSED_PIN,                // 20
  UNUSED_PIN,                // 21
  DIGITAL_OUTPUT_PIN,        // 22
  DIGITAL_OUTPUT_PIN,        // 23
  DIGITAL_OUTPUT_PIN,        // 24
  DIGITAL_OUTPUT_PIN,        // 25
  DIGITAL_OUTPUT_PIN,        // 26
  DIGITAL_OUTPUT_PIN,        // 27
  DIGITAL_INPUT_PIN,         // 28
  DIGITAL_INPUT_PIN,         // 29
  DIGITAL_INPUT_PIN,         // 30
  DIGITAL_INPUT_PIN,         // 31
  DIGITAL_INPUT_PIN,         // 32
  DIGITAL_INPUT_PIN,         // 33
  DIGITAL_INPUT_PIN,         // 34
  DIGITAL_INPUT_PIN,         // 35
  DIGITAL_INPUT_PIN,         // 36
  DIGITAL_INPUT_PIN,         // 37
  DIGITAL_INPUT_PIN,         // 38
  DIGITAL_INPUT_PIN,         // 39
  DIGITAL_INPUT_PIN,         // 40
  DIGITAL_INPUT_PIN,         // 41
  DIGITAL_INPUT_PIN,         // 42
  DIGITAL_INPUT_PIN,         // 43
  DIGITAL_INPUT_PIN,         // 44
  DIGITAL_INPUT_PIN,         // 45
  DIGITAL_INPUT_PIN,         // 46
  DIGITAL_INPUT_PIN,         // 47
  DIGITAL_INPUT_PULLUP_PIN,  // 48
  DIGITAL_INPUT_PULLUP_PIN,  // 49
  UNUSED_PIN,                // 50
  UNUSED_PIN,                // 51
  UNUSED_PIN,                // 52
  UNUSED_PIN,                // 53
  // ANALOG
  ANALOG_INPUT_PIN,          // 54
  ANALOG_INPUT_PIN,          // 55
  ANALOG_INPUT_PIN,          // 56
  ANALOG_INPUT_PIN,          // 57
  ANALOG_INPUT_PIN,          // 58
  ANALOG_INPUT_PIN,          // 59
  ANALOG_INPUT_PIN,          // 60
  ANALOG_INPUT_PIN,          // 61
  ANALOG_INPUT_PIN,          // 62
  ANALOG_INPUT_PIN,          // 63
  ANALOG_INPUT_PIN,          // 64
  ANALOG_INPUT_PIN,          // 65
  UNUSED_PIN,                // 66
  UNUSED_PIN,                // 67
  UNUSED_PIN,                // 68
  UNUSED_PIN                 // 69
};

// Default pin states
// Defaults determine the value of output pins with the RTU initializes
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


#ifdef RTU_USB
#define NUM_DIGITAL 54    // Number of digital I/O pins
#define NUM_ANALOG  16    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value

// Default pin allocation
#define ONE_WIRE_BUS 8   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN A1  // Reserved pin for pH probe
#define DHTTYPE DHT22    // Sets DHT type
#define DHTPIN 12        // Reserved pin for DHT-22 sensor


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
// Defaults determine the value of output pins with the RTU initializes
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


#ifdef RTU_UNO
#define NUM_DIGITAL 14    // Number of digital I/O pins
#define NUM_ANALOG   6    // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default digital state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value

// Default pin allocation
#define ONE_WIRE_BUS 8   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN A1  // Reserved pin for pH probe
#define DHTTYPE DHT22    // Sets DHT type
#define DHTPIN 12        // Reserved pin for DHT-22 sensor
#define THERMISTOR 2     // Analog Read Temperature

// Default pin modes
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 3, 3, 3, 3, 3, 0, 2, 1, 	//  0 -  9

  1, 1, 2, 3,                     // 10 - 13
                                  // ANALOG
  5, 5, 5, 5, 5, 5                // 14 - 20
};

// Default pin states
// Defaults determine the value of output pins with the RTU initializes
// 0 = LOW, 1 = HIGH
int pinDefaults[NUM_DIGITAL+NUM_ANALOG] = {
                                  // DIGITAL
  0, 0, 1, 1, 0, 1, 1, 1, 1, 1,   //  0 -  9
  0, 0, 0, 0,                     // 10 - 13
                                  // ANALOG
  0, 0, 0, 0, 0, 0                // 14 - 20
};
#endif

#ifdef RTU_ESP
#define NUM_DIGITAL 17    // Number of digital I/O pins
#define NUM_ANALOG  1     // Number of analog I/O pins
#define PIN_MAP_SIZE NUM_DIGITAL*2   // Array size for default state data
                                     // 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value

// Default pin allocation
#define ONE_WIRE_BUS 13   // Reserved pin for 1-Wire bus
#define PH_SENSORPIN 14   // Reserved pin for pH probe
#define DHTTYPE DHT22     // Sets DHT type
#define DHTPIN 12         // Reserved pin for DHT-22 sensor

// Default pin modes
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins
int pinControl[NUM_DIGITAL+NUM_ANALOG] = {
  3, 3, 3, 1, 3, 3, 0, 0,   //  0 -  8  // Digital i/o
  0, 0, 0, 0, 3, 3, 3, 3,   //  9 - 15
  3,                        // 16
  5                         // A0       //Analog Input
};

// Default pin states
// Defaults determine the value of output pins with the RTU initializes
// 0 = LOW, 1 = HIGH
int pinDefaults[NUM_DIGITAL+NUM_ANALOG] = {
  1, 1, 1, 1, 1, 1, 0, 0,   //  0 -  8  // Digital i/o
  0, 0, 0, 0, 1, 1, 1, 1,   //  9 - 15
  1,                        // 16
  5                         // A0       //Analog Input
};

#endif


OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature wp_sensors(&oneWire);

//**** Begin Main Variable Definition Section ****
String HAPI_CLI_VERSION = "v2.2";  // The version of the firmware the RTU is running
#ifdef RTU_ENET
String RTUID = "RTU001";             // This RTUs Unique ID Number - unique across site
#endif
#ifdef RTU_USB
String RTUID = "RTU101";             // This RTUs Unique ID Number - unique across site
#endif
#ifdef RTU_ESP
String RTUID = "RTU301";             // This RTUs Unique ID Number - unique across site
#endif
#ifdef RTU_UNO
String RTUID = "RTU201";             // This RTUs Unique ID Number - unique across site
#endif
boolean idle_mode = false;         // a boolean representing the idle mode of the RTU
boolean metric = true;             // should values be returned in metric or US customary units
String inputString = "";           // A string to hold incoming data
String inputCommand = "";          // A string to hold the command
String inputPort = "";             // A string to hold the port number of the command
String inputControl = "";          // A string to hold the requested action of the command
String inputTimer = "0";           // A string to hold the length of time to activate a control
boolean stringComplete = false;    // A boolean indicating when received string is complete (a \n was received)
//**** End Main Variable Definition Section ****

//**** Begin Communications Section ****
// the media access control (ethernet hardware) address for the shield:
byte mac[] = { 0x55, 0x55, 0x55, 0x55, 0x55, 0x55 };
#ifdef RTU_ENET
EthernetServer rtuServer = EthernetServer(80);
EthernetClient client;
#endif
#ifdef RTU_ESP
const char* ssid = HAPI_SSID;
const char* password = HAPI_PWD;
int WiFiStatus = 0;
WiFiServer rtuServer = WiFiServer(80);
WiFiClient client;
#endif
//**** End Communications Section ****


//Define the Reset function
void(* resetFunc) (void) = 0; //declare reset function @ address 0

//**** Begin DHT Device Section ****
//Define DHT devices and allocate resources
#define NUM_DHTS 1 //total number of DHTs on this device
DHT dht1(DHTPIN, DHT22); //For each DHT, create a new variable given the pin and Type
DHT dhts[1] = {dht1}; //add the DHT device to the array of DHTs

//**** Begin Custom Functions Section ****
//Custom functions are special functions for reading sensors or controlling devices. They are
//used when setting or a reading a pin isn't enough, as in the instance of library calls.
#define CUSTOM_FUNCTIONS 5 //The number of custom functions supported on this RTU

typedef float (* GenericFP)(int); //generic pointer to a function that takes an int and returns a float

struct FuncDef {   //define a structure to associate a Name to generic function pointer.
  String fName;
  String fType;
  int fPort;
  GenericFP fPtr;
};

float readTemperature(int iDevice);
float readHumidity(int iDevice);
float readThermistorTemp(int iDevice);
float readWaterTemperature(int iDevice);
float readpH(int iDevice);

//Create a FuncDef for each custom function
//Format: abbreviation, context, pin, function
FuncDef func1 = {"tmp", "dht", -1, &readTemperature};
FuncDef func2 = {"hmd", "dht", -1, &readHumidity};
FuncDef func3 = {"trm", "thermistor", 2, &readThermistorTemp};
FuncDef func4 = {"res1tmp", "DS18B20", ONE_WIRE_BUS, &readWaterTemperature};
FuncDef func5 = {"phl", "pH Sensor", PH_SENSORPIN, &readpH};

FuncDef HapiFunctions[CUSTOM_FUNCTIONS] = {func1, func2, func3, func4, func5};
//**** End Custom Functions Section ****

String getPinArray() {
  // Returns all pin configuration information
  String response = "";
  for (int i = 0; i < NUM_DIGITAL+NUM_ANALOG; i++) {
    if (i <= (NUM_DIGITAL-1)) {
      response += String(i) + String(pinControl[i]);
    }
    else {
      response += "A" + String(i - NUM_DIGITAL) + String(pinControl[i]);
    }
  }
  return response;
}

void assembleResponse(String &responseString, String varName, String value) {
  // Helper function for building response strings
  if (responseString.equals("")) {
    responseString = "{";
  }

  if (!varName.equals("")) {
    responseString += "\"" + varName + "\"" + ":" + "\"" + value + "\"" + ",";
  }
  else {
    if (responseString.endsWith(",")) {
      responseString = responseString.substring(0, responseString.length() - 1);
    }
    responseString += "}";
  }
}

void writeLine(String response, boolean EOL) {
  // Writes a response line to the network connection

  char inChar;

  for (int i = 0; i < response.length(); i++)
    {
    inChar = (char)response.charAt(i);
#ifdef RTU_ENET
    rtuServer.write(inChar);
#endif
    #ifdef RTU_ESP
    rtuServer.write(inChar);
#endif
#ifdef RTU_USB
    Serial.write(inChar);
#endif
    #ifdef RTU_UNO
    Serial.write(inChar);
#endif
    }
  if ((String)inChar != "\n") {
    if (EOL) {
#ifdef RTU_ENET
    rtuServer.write(inChar);
#endif
    #ifdef RTU_ESP
    rtuServer.write(inChar);
#endif
#ifdef RTU_USB
    Serial.write(inChar);
#endif
    #ifdef RTU_UNO
    Serial.write(inChar);
#endif
    }
  }
}


float readHumidity(int iDevice) {
  // readHumidity  - Uses the DHT Library to read the current humidity
  float returnValue;
  float h;
  //h = dhts[iDevice].readHumidity();
  h = dht1.readHumidity();

  if (isnan(h)) {
    returnValue = -1;
  }
  else {
    returnValue = h;
  }
  return returnValue;
}

float readTemperature(int iDevice) {
  // readTemperature  - Uses the DHT Library to read the current temperature
  float returnValue;
  float h;
  //h = dhts[iDevice].readTemperature();
  h = dht1.readTemperature();

  if (isnan(h)) {
    returnValue = -1;
  }
  else {
    returnValue = h;
    if (!metric) {
      returnValue = (returnValue * 9.0)/ 5.0 + 32.0; // Convert Celsius to Fahrenheit
    }
  }
  return returnValue;
}

float readWaterTemperature(int iDevice) {
  // readWaterTemperature  - Uses the Dallas Temperature library to read the waterproof temp sensor
  float returnValue;
  wp_sensors.requestTemperatures();
  returnValue = wp_sensors.getTempCByIndex(0);
  if (isnan(returnValue)) {
    returnValue = -1;
  }
  else
  {
    if (!metric) {
      returnValue = (returnValue * 9.0)/ 5.0 + 32.0; // Convert Celsius to Fahrenheit
    }
  }
  return returnValue;
}

float readpH(int iDevice) {
  // readpH - Reads pH from an analog pH sensor (Robot Mesh SKU: SEN0161, Module version 1.0)
  unsigned long int avgValue;  //Store the average value of the sensor feedback
  float b;
  int buf[10], temp;

  for (int i = 0; i < 10; i++) //Get 10 sample value from the sensor for smooth the value
  {
    buf[i] = analogRead(iDevice);
    delay(10);
  }
  for (int i = 0; i < 9; i++) //sort the analog from small to large
  {
    for (int j = i + 1; j < 10; j++)
    {
      if (buf[i] > buf[j])
      {
        temp = buf[i];
        buf[i] = buf[j];
        buf[j] = temp;
      }
    }
  }
  avgValue = 0;
  for (int i = 2; i < 8; i++)               //take the average value of 6 center sample
    avgValue += buf[i];
  float phValue = (float)avgValue * 5.0 / 1024 / 6; //convert the analog into millivolt
  phValue = 3.5 * phValue;                  //convert the millivolt into pH value
  return phValue;
}

float readThermistorTemp(int iDevice) {
  // Simple code to read a temperature value from a 10k thermistor with a 10k pulldown resistor
  float Temp;
  int RawADC = analogRead(iDevice);

  Temp = log(10000.0*((1024.0/RawADC-1)));
  Temp = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * Temp * Temp ))* Temp );
  Temp -= 273.15;            // Convert Kelvin to Celsius
  if (!metric) {
     Temp = (Temp * 9.0)/ 5.0 + 32.0; // Convert Celsius to Fahrenheit
  }

  return Temp;
}

#ifdef RTU_USB
String getCommand() {
#endif
#ifdef RTU_UNO
String getCommand() {
#endif
#ifdef RTU_ENET
String getCommand(EthernetClient client) {
#endif
#ifdef RTU_ESP
String getCommand(WiFiClient client) {
#endif

// Retrieves a command from the cuurent serial or network connection
  stringComplete = false;
  char inChar;
  inputString = "";

#if defined(RTU_USB) || defined(RTU_UNO)
  while (Serial.available() > 0 && !stringComplete) {
    inChar = (char)Serial.read();  // read the bytes incoming from the client:
#elif defined(RTU_ENET) || defined(RTU_ESP)
  while (client.available() > 0 && !stringComplete) {
    inChar = (char)client.read();  // read the bytes incoming from the client:
#endif
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
    delay(2);                       // small delay to receive any further characters
  }

  Serial.println(inputString);
  return inputString;
}

String buildResponse() {
  // Assembles a response with values from pins and custom functions
  // Returns a JSON string  ("pinnumber":value,"custom function abbreviation":value}
  String response = "buildResponse\r\n";
  assembleResponse(response, "name", RTUID);
  assembleResponse(response, "version", HAPI_CLI_VERSION);
//  assembleResponse(response, "lastcmd", lastCommand);
  //Process digital pins
  for (int i = 0; i < NUM_DIGITAL; i++) {
    switch (pinControl[i]) {
    case DIGITAL_INPUT_PIN:
    case DIGITAL_INPUT_PULLUP_PIN:
    case DIGITAL_OUTPUT_PIN:
    case ANALOG_OUTPUT_PIN:
      assembleResponse(response, (String)i, (String)digitalRead(i));
      break;
    default:
      break;
    }
  }

  //Process analog pins
  for (int x = 0; x < NUM_ANALOG; x++) {
    assembleResponse(response, (String)(x + NUM_DIGITAL), (String)analogRead(x));
  }

  //Process custom functions
  FuncDef f;
  float funcVal = -1.0;
  String funcStr = "";
  String tempVal;
  char cFuncVal[10];
  String str;

  for (int x = 0; x < CUSTOM_FUNCTIONS; x++) {
    f = HapiFunctions[x];

    if (f.fType.equals("dht")) {
      for (int x = 0; x < NUM_DHTS; x++) {
        funcVal = f.fPtr(x);
        assembleResponse(response, f.fName, String((int)funcVal));
      }
    }
    else {
      funcVal = f.fPtr(f.fPort);
      dtostrf(funcVal, 4, 3, cFuncVal);
      str = cFuncVal;
      assembleResponse(response, f.fName, str);
    }
  }

  assembleResponse(response, "", ""); //closes up the response string
  return response;
}

int freeRam ();

String getStatus() {
  // Returns the current status of the RTU itself
  // Includes firmware version, MAC address, IP Address, Free RAM and Idle Mode
  String retval = "getStatus\r\n";
  String macstring = (char*)mac;

  retval = RTUID + "\r\n";
  retval += "Firmware " + HAPI_CLI_VERSION + "\r\n";
  Serial.println(retval);
#ifdef RTU_USB
  retval += "Connected on USB\r\n";
#endif
#ifdef RTU_UNO
  retval += "Connected on USB\r\n";
#endif
#ifdef RTU_ENET
  retval += "MAC=";
  retval += "0x" + String(mac[0], HEX) + ":";
  retval += "0x" + String(mac[1], HEX) + ":";
  retval += "0x" + String(mac[2], HEX) + ":";
  retval += "0x" + String(mac[3], HEX) + ":";
  retval += "0x" + String(mac[4], HEX) + ":";
  retval += "0x" + String(mac[5], HEX) + "\n";
  Serial.println(retval);
  retval += "IP=";
  retval += String(Ethernet.localIP()[0]) + ".";
  retval += String(Ethernet.localIP()[1]) + ".";
  retval += String(Ethernet.localIP()[2]) + ".";
  retval += String(Ethernet.localIP()[3]) + "\n";
  Serial.println(retval);
#endif
#ifdef RTU_ESP
  retval += "MAC=";
  retval += "0x" + String(mac[0], HEX) + ":";
  retval += "0x" + String(mac[1], HEX) + ":";
  retval += "0x" + String(mac[2], HEX) + ":";
  retval += "0x" + String(mac[3], HEX) + ":";
  retval += "0x" + String(mac[4], HEX) + ":";
  retval += "0x" + String(mac[5], HEX) + "\n";
  Serial.println(retval);
  retval += "IP=";
  retval += String(WiFi.localIP()[0]) + ".";
  retval += String(WiFi.localIP()[1]) + ".";
  retval += String(WiFi.localIP()[2]) + ".";
  retval += String(WiFi.localIP()[3]) + "\n";
  Serial.println(retval);
#endif

  retval += "Digital= " + String(NUM_DIGITAL) + "\n";
  retval += "Analog= " + String(NUM_ANALOG) + "\n";
  retval += "Free SRAM: " + String(freeRam()) + "k\n";

  retval += String("Idle Mode: ") + (idle_mode ? String("True") : String("False"));

  return retval;

}


int freeRam (){
#ifdef RTU_ESP
// Gets free ram on the ESP8266
  return ESP.getFreeHeap();
#else
// Gets free ram on the Arduino
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
#endif
}

void setup() {

  // Initialize Digital Pins for Input or Output - From the arrays pinControl and pinDefaults
  for (int x = 0; x < (NUM_DIGITAL+NUM_ANALOG); x++) {
    if (pinControl[x] == 1) {
      pinMode(x, INPUT); // Digital Input
    }
    if (pinControl[x] == 2) {
      pinMode(x, INPUT_PULLUP); // Digital Inputs w/ Pullup Resistors
    }
    if (pinControl[x] == 3) {
      pinMode(x, OUTPUT); // Digital Outputs
      if (pinDefaults[x] == 0) {
        digitalWrite(x, LOW);
      }
      else{
        digitalWrite(x, HIGH);
      }
    }
    if (pinControl[x] == 4) {
      pinMode(x, OUTPUT); // Analog Outputs
    }
  }

  dht1.begin(); // Start the DHT-22
  /*for (int x = 0; x < NUM_DHTS; x++) {
    dhts[x].begin();
  }*/

  wp_sensors.begin(); // Start the DS18B20

  inputString.reserve(200);  // reserve 200 bytes for the inputString:

  Serial.begin(115200);

#ifdef RTU_ENET
  Serial.println("Initializing network....");
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to obtain IP address  ...");
  } else
  {
    Serial.print("IP address: ");
    Serial.println(Ethernet.localIP());
  }
  rtuServer.begin();
#endif
#ifdef RTU_ESP
  Serial.println("Initializing WiFi network....");
  WiFiStatus = WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  WiFi.macAddress(mac);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  rtuServer.begin();
#endif

  Serial.println("Starting communications  ...");
  Serial.println(getStatus()); //Send Status (incl. IP Address) to the Serial Monitor
  Serial.println("Setup Complete. Listening for connections.");

}

void loop() {
#if defined(RTU_USB) || defined(RTU_UNO)
  if (Serial.available()) {
    inputString = getCommand();
#elif defined(RTU_ENET) || defined(RTU_ESP)
  // Wait for a new client to connect
  client = rtuServer.available();
  if (client) {
    inputString = getCommand(client);
#endif
    inputString.trim();
    inputString.toLowerCase();
    inputTimer = "0";

    if (inputString != "" && inputString != "\r\n") {
      inputCommand = inputString.substring(0, 3);
      boolean cmdFound = false;

      Serial.println(inputCommand);

      if ((inputCommand == "aoc") && !idle_mode) {
        cmdFound = true;
        inputPort = inputString.substring(3, 6);
        inputControl = inputString.substring(6, 9);
        if (pinControl[inputPort.toInt()] == 5) {
          analogWrite(inputPort.toInt(), inputControl.toInt());
        } // END OF if pinControl=5
      }  // END Of aoc

      // doc (Digital Output Control) Sets a single digital output
      if ((inputCommand == "doc") && !idle_mode) {
        cmdFound = true;
        inputPort = inputString.substring(4, 6);
        inputControl = inputString.substring(6, 7);
        inputTimer = inputString.substring(7, 10);
        if (pinControl[inputPort.toInt()] == 3) {
          if (inputTimer.toInt() > 0) {
            int currVal = digitalRead(inputPort.toInt());
            digitalWrite(inputPort.toInt(), inputControl.toInt());
            delay(inputTimer.toInt() * 1000);
            digitalWrite(inputPort.toInt(), currVal);
          }
          else {
            digitalWrite(inputPort.toInt(), inputControl.toInt());
          }

        } // END OF if pinControl=3
      }  // END Of doc

      // Get pin modes
      if (inputCommand == "gpm") {
        cmdFound = true;
        String response = getPinArray();
        writeLine(response, true); //Send pin mode information back to client
      }

      // Enable/Disable Idle Mode
      if (inputCommand == "idl") {
        cmdFound = true;
        if (inputString.substring(3, 4) == "0") {
          idle_mode = false;
        }
        else if (inputString.substring(3, 4) == "1") {
          idle_mode = true;
        }
      }

      // res  - resets the Arduino
      if ((inputCommand == "res") && !idle_mode) {
        cmdFound = true;
        for (int x = 0; x < NUM_DIGITAL+NUM_ANALOG; x++) {
          if (pinControl[x] == 3) {
            digitalWrite(x, LOW); // If this Pin is a Digital Output Turn it off
          }
          if (pinControl[inputPort.toInt()] == 4) {
            analogWrite(x, 0); // If this Pin is a Analog Output Set Value to 0
          }
        }
        delay(100);
        resetFunc();  //call reset
      }

      // Get the RTU Status
      if (inputCommand == "sta") {
        cmdFound = true;
        writeLine(getStatus(), true);
      }

      String response = buildResponse();
      writeLine(response, true);
#ifdef RTU_ENET
      client.stop();
#endif
#ifdef RTU_ESP
      client.stop();
#endif
    }
  }
}
