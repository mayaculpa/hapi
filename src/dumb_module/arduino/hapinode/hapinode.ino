#include <Arduino.h>

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

//**** Begin Board Configuration Section ****

// Board Type
// ==========
//#define HN_2560         // Must have ethernet shield

//**ESP Based
// Board Type
#define HN_ESP8266
//#define HN_ESP32

// Connection Type
// ===============
//#define HN_ENET           // Define for Ethernet shield
#define HN_WiFi             // Define for WiFi support

// Protocol Type
// =============
#define HN_MQTT

//**** End Board Configuration Section ****

#include <DHT.h>
#include <SPI.h>

#ifdef HN_ESP8266
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>        // for avahi
#endif

#ifdef HN_ESP32
#include <WiFi.h>
#include <ESPmDNS.h>            // for avahi
#endif

#ifdef HN_WiFi
#include <WiFiUdp.h>            // For ntp
#endif

#ifdef HN_ENET
#include <Ethernet.h>
#include <EthernetBonjour.h>
#include <EthernetUdp.h>
#endif

#include <PubSubClient.h> // Allows us to connect to, and publish to the MQTT brokerinclude <stdlib.h>
#include <ArduinoJson.h>  // JSON library for MQTT strings
#include <math.h>

#ifndef HN_ESP32
#include <EEPROM.h>
#endif
#ifdef HN_ESP32
#include <Preferences.h>
#endif

// Real Time Clock Libraries
// Time related libararies
#include <DS1307RTC.h>            //https://www.pjrc.com/teensy/td_libs_DS1307RTC.html
#include <TimeLord.h>             //https://github.com/probonopd/TimeLord
#include <TimeLib.h>              //https://github.com/PaulStoffregen/Time
#include <TimeAlarms.h>           //https://github.com/PaulStoffregen/TimeAlarms
//#include <Timezone.h>             //https://github.com/schizobovine/Timezone (https://github.com/JChristensen/Timezone)
//#include <EEPROM.h>               //http://playground.arduino.cc/Code/EEPROMWriteAnything
#include <Wire.h>
#include <DallasTemperature.h>
#include <Bounce2.h> // Used for "debouncing" inputs

// =====================================================================
// Make sure to update these files for your own WiFi and/or MQTT Broker!
// =====================================================================
#include "nodecomms.h"      // WiFi, UDP, NTP and MQTT setup
#include "nodeboard.h"      // Node default pin allocations

//**** Begin Main Variable Definition Section ****
int loopcount;              // Count of times through main loop (for LED etc)
unsigned long mscount;      // millisecond counter
time_t epoch;               // UTC seconds
time_t currentTime;         // Local value

String HAPI_FW_VERSION = "V3.1.1";    // The version of the firmware the HN is running
#ifdef HN_ENET
String HN_base = "HN2";             // Prefix for mac address
#endif
#ifdef HN_ESP8266
String HN_base = "HN3";             // Prefix for mac address
#endif
#ifdef HN_ESP32
String HN_base = "HN4";             // Prefix for mac address
#endif

String HN_Id = "HNx";              // HN address
String HN_status = "Online";

boolean idle_mode = false;         // a boolean representing the idle mode of the HN
boolean metric = true;             // should values be returned in metric or US customary units
String inputString = "";           // A string to hold incoming data
String inputCommand = "";          // A string to hold the command
String inputPort = "";             // A string to hold the port number of the command
String inputControl = "";          // A string to hold the requested action of the command
String inputTimer = "0";           // A string to hold the length of time to activate a control
boolean stringComplete = false;    // A boolean indicating when received string is complete (a \n was received)
//**** End Main Variable Definition Section ****

//**** Begin Communications Section ****
// the media access control (ethernet hardware) address for the shield
// Need to manually change this for USB, Ethernet
byte mac[] = { 0x55, 0x55, 0x55, 0x55, 0x55, 0x55 };
char mac_str[16] = "555555555555";  // Default mac id      
char hostString[64] = {0};          // mDNS Hostname for this HAPInode

// ntp config
IPAddress ntpServerIP;                // Place to store IP address of mqttbroker.local
char ntpServer_hostname[64] = MQTT_broker_default;    // Assume mqttbroker is also the time server
const int NTP_PACKET_SIZE = 48;       // NTP time stamp is in the first 48 bytes of the message
byte packetBuffer[ NTP_PACKET_SIZE];  //buffer to hold incoming and outgoing packets
const unsigned int localPort = UDP_port;    // local port to listen for UDP packets

int timeZone = +10; // Eastern Standard Time (Au)
//int timeZone = -5;  // Eastern Standard Time (USA)
//int timeZone = -4;  // Eastern Daylight Time (USA)
//int timeZone = -8;  // Pacific Standard Time (USA)
//int timeZone = -7;  // Pacific Daylight Time (USA)


#ifdef HN_WiFi
// Local wifi network parameters (set in nodewifi.h)
const char* ssid = HAPI_SSID;
const char* password = HAPI_PWD;
int WiFiStatus = 0;
WiFiClient HNClient;
WiFiUDP udp;                          // A UDP instance to let us send and receive packets over UDP
#endif // HN_WiFi

#ifdef HN_ENET
EthernetClient HNClient;
EthernetUDP udp;
#endif  // HN_ENET

//**** End Communications Section ****

//**** Begin MQTT Section ****
char MQTT_broker_hostname[64] = MQTT_broker_default;    // Space to hold mqtt broker hostname
const char* clientID = "HAPInode";
const char* mqtt_topic_command = "COMMAND/";            // General Command topic
const char* mqtt_topic_status = "STATUS/RESPONSE/";     // General Status topic
const char* mqtt_topic_asset = "ASSET/RESPONSE/";       // Genral Asset topic
const char* mqtt_topic_exception = "EXCEPTION/";        // General Exception topic
const char* mqtt_topic_config = "CONFIG/";              // General Configuration topic
char mqtt_topic[256] = "";                              // Topic for this HN

#define MAXTOPICS 5
#define STATUSSTART 0
#define ASSETSTART 1
#define CONFIGSTART 4
#define INVALID_VALUE 9999
const char* mqtt_topic_array[MAXTOPICS] = {
  "STATUS/QUERY",
  "ASSET/QUERY",
  "ASSET/QUERY/",
  "ASSET/QUERY/*",
  "CONFIG/QUERY/"
};
#define MAXLISTEN 12
const char* mqtt_listen_array[MAXLISTEN] = {
  "COMMAND/",
  "CONFIG/",
  "EXCEPTION/",
  "STATUS/QUERY",
  "STATUS/QUERY/",
  "STATUS/QUERY/#",
  "ASSET/QUERY",
  "ASSET/QUERY/",
  "ASSET/QUERY/#",
  "CONFIG/QUERY",
  "CONFIG/QUERY/",
  "CONFIG/QUERY/#"
};

StaticJsonBuffer<128> hn_topic_exception;               // Exception data for this HN
char MQTTOutput[256];                                   // String storage for the JSON data
char MQTTInput[256];                                    // String storage for the JSON data

// Callback function header
void MQTTcallback(char* topic, byte* payload, unsigned int length);
PubSubClient MQTTClient(HNClient);                      // 1883 is the listener port for the Broker

// Prepare JSON string objects

JsonObject& exception_topic = hn_topic_exception.createObject();
//**** End MQTT Section ****

//**** Begin Sensors Section ****
// Definitions related to sensor operations
#define SENSORID_DIO 0    // DIGITAL I/O
#define SENSORID_AIO 1    // ANALOG I/O
#define SENSORID_FN 2     // SENSOR FUNCTION I/O
#define CONTROLID_FN 3    // CONTROL FUNCTION I/O
#define CONTROLDATA1_FN 4  // CONTROL FUNCTION TIME DATA
#define CONTROLDATA2_FN 5  // CONTROL FUNCTION VALUE DATA

boolean ledState = false;

// Flow meter devices
Bounce flowrate = Bounce();   // Use bouncer object to measure flow rate
int WaterFlowRate = 0;

//LIGHT Devices

//oneWire Devices
OneWire oneWire(WIRE_PIN );
DallasTemperature wp_sensors(&oneWire);

//Define DHT devices and allocate resources
#define NUM_DHTS 1        //total number of DHTs on this device
#define DHTTYPE DHT22     // Sets DHT type

DHT dht1(DHT_PIN, DHT22);   //For each DHT, create a new variable given the pin and Type
DHT dhts[1] = {dht1};             //add the DHT device to the array of DHTs

// Custom function devices
//Custom functions are special functions for reading sensors or controlling devices. They are
//used when setting or a reading a pin isn't enough, as in the instance of library calls.
typedef float (* GenericFP)(int); //generic pointer to a function that takes an int and returns a float
struct FuncDef {   //define a structure to associate a Name to generic function pointer.
  const char* fName;
  const char* fType;
  const char* fUnit;
  int fPin;
  GenericFP fPtr;
};

#define ArrayLength(x) (sizeof(x)/sizeof(*(x)))
// Create a FuncDef for each custom function
// Format: abbreviation, context, pin, data function
FuncDef sfunc1 = {"tmp", "Env", "C", -1, &readTemperatured};
FuncDef sfunc2 = {"hum", "Env", "%", -1, &readHumidity};
FuncDef sfunc3 = {"lux", "Env", "lux", sLux_PIN, &readLightSensor};
FuncDef sfunc4 = {"tmw", "Water", "C", WIRE_PIN , &read1WireTemperature};
FuncDef sfunc5 = {"phv", "Water", "pH", spH_PIN, &readpH};
FuncDef sfunc6 = {"tds", "Water", "ppm", sTDS_PIN, &readTDS};
FuncDef sfunc7 = {"flo", "Water", "lpm", sWtrFlow_PIN, &readFlow};
FuncDef HapisFunctions[] = {sfunc1, sfunc2, sfunc3, sfunc4, sfunc5, sfunc6, sfunc7};

// Custom control devices
//Custom functions are special functions for reading sensors or controlling devices. They are
//used when setting or a reading a pin isn't enough, as in the instance of library calls.
typedef float (* GenericFP)(int); //generic pointer to a function that takes an int and returns a float
struct CFuncDef {   //define a structure to associate a Name to generic control pointer.
  const char* fName;
  const char* fType;
  const char* fUnit;
  int fPin;
  GenericFP oPtr;
  GenericFP iPtr;
};

// Create a FuncDef for each custom control function
// Format: abbreviation, context, Control data index, control function, data function
CFuncDef cfunc1 = {"ppw", "Pump", "lpm", 1, &controlPumps, &readSensorPin};
CFuncDef cfunc2 = {"ppf", "Pump", "lpm", 2, &controlPumps, &readSensorPin};
CFuncDef cfunc3 = {"ppn", "Pump", "lpm", 3, &controlPumps, &readTDS};
CFuncDef cfunc4 = {"pHU", "Pump", "lpm", 4, &controlPumps, &readpH};
CFuncDef cfunc5 = {"pHD", "Pump", "lpm", 5, &controlPumps, &readpH};
CFuncDef cfunc6 = {"lmp", "Lamp", "lpm", 6, &controlLamps, &readLightSensor};
CFuncDef HapicFunctions[] = {cfunc1, cfunc2, cfunc3, cfunc4, cfunc5, cfunc6};

struct ControlData {
  const char* hc_name;              // Sensor name abbreviation
  int hc_controlpin;
  boolean hc_polarity;              // Active low control output
  unsigned long hc_start;           // Start time (unix time)
  unsigned long hc_end;             // End time (unix time)
  unsigned long hc_repeat;          // Repeat interval (seconds)
  boolean hc_active;                // Pump running or not, Lamp on or off
  int hcs_sensepin;                 // Pin used for iPtr function control
  int hcs_onValue;                  // Sensor value at which control turns On
  int hcs_offValue;                 // Sensor value at which control turns Off
};

ControlData ccontrol1 = {"ppw", cWtrPump_PIN, true, 0, 0, 0, false, sWtrFlow_PIN, 0, 0};  // Water
ControlData ccontrol2 = {"ppf", cWtrFill_PIN, true, 0, 0, 0, false, sWtrFloat_PIN, 0, 0}; // Fill
ControlData ccontrol3 = {"ppn", cNutr_PIN, true, 0, 0, 0, false, sTDS_PIN, 0, 0};         // Nutrient
ControlData ccontrol4 = {"pHU", cpHUp_PIN, true, 0, 0, 0, false, spH_PIN, 0, 0};          // pHUp
ControlData ccontrol5 = {"pHD", cpHDn_PIN, true, 0, 0, 0, false, spH_PIN, 0, 0};          // pHDown
ControlData ccontrol6 = {"lmp", cLamp_PIN, true, 0, 0, 0, false, sLux_PIN, 0, 0};         // Lamp
ControlData HapicData[] = {ccontrol1, ccontrol2, ccontrol3, ccontrol4, ccontrol5, ccontrol6};

//**** End Sensors Section ****

void b2c(byte* bptr, char* cptr, int len) {
  int i;
  char c;
  for (i=0; i<len; i++) {
    c = (bptr[i] >> 4) & 0x0f;
    c += '0';
    if (c > '9') c += ('A' - '9' - 1);
    *cptr++ = c;
//    Serial.print(c, HEX);
    c = bptr[i] & 0x0f;
    c += '0';
    if (c > '9') c += ('A' - '9' - 1);
    *cptr++ = c;
//    Serial.print(c, HEX);
  }
  *cptr++ = '\0';
//  Serial.println(F(""));
}

int freeRam (){
#if defined(HN_ESP8266) || defined(HN_ESP32)
// Gets free ram on the ESP8266, ESP32
  return ESP.getFreeHeap();
#else
// Gets free ram on the Arduino
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
#endif
}

void setup() {
// Switch the on-board LED off to start with
//  pinMode(LED_PIN, OUTPUT);
//  digitalWrite(LED_PIN, HIGH);
  Serial.begin(115200);       // Debug port
  while (!Serial) ;           //  wait for Arduino Serial Monitor

// Start Debug port and sensors
// ============================
  setupSensors();             // Initialize I/O and start devices
  inputString.reserve(200);   // reserve 200 bytes for the inputString

#ifdef HN_WiFi
  Serial.println(F("Initializing WiFi network...."));
  WiFiStatus = WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(F("."));
  }
  WiFi.macAddress(mac);
#endif // HN_WiFi

  b2c(&mac[3], &mac_str[0], 3);         //convert mac to ASCII value for unique station ID
  HN_Id = HN_base + String(mac_str);
  HN_Id.toCharArray(hostString,(HN_Id.length()+1));

#ifdef HN_2560
  Serial.println(hostString);
#endif
#ifdef HN_ESP8266
  Serial.println(WiFi.hostname());
  Serial.println(WiFi.hostname(hostString));
  Serial.print(F("NewHostname: "));
  Serial.println(WiFi.hostname());
#endif
#ifdef HN_ESP32
  Serial.println(WiFi.getHostname());
  Serial.println(WiFi.setHostname(hostString));
  Serial.print(F("NewHostname: "));
  Serial.println(WiFi.getHostname());
#endif
#if defined(HN_ESP32) || defined(HN_ESP32)
  Serial.print(F("IP  address: "));
  Serial.println(WiFi.localIP());
#endif

// Start mDNS support
// ==================
  Serial.print(F("HN_Id:      "));
  Serial.println(HN_Id);
  Serial.print(F("hostString: "));
  Serial.println(hostString);

#if defined(HN_ESP8266) || defined(HN_ESP32)
 if (!MDNS.begin(hostString)) {
    Serial.println(F("Error setting up MDNS responder!"));
  }
  Serial.print(F("Hostname: "));
  Serial.print(hostString);
  Serial.println(F(" mDNS responder started for this HAPInode"));

  Serial.print(F("Sending mDNS query to find mqtt broker - "));
  int n = MDNS.queryService("mqtt", "tcp"); // Send out query for workstation tcp services
  Serial.println(F("mDNS query done"));
  if (n == 0) {
    Serial.println(F("no services found"));
  }
  else {
    Serial.print(n);
    Serial.println(F(" service(s) found"));
    for (int i = 0; i < n; ++i) {
      // Print details for each service found
      Serial.print(i + 1);
      Serial.print(F(": "));
      Serial.print(MDNS.hostname(i));
      Serial.print(F(" ("));
      Serial.print(MDNS.IP(i));
      Serial.print(F(":"));
      Serial.print(MDNS.port(i));
      Serial.println(F(")"));
      if (MDNS.port(i) == MQTT_port) {
        MDNS.hostname(i).toCharArray(MQTT_broker_hostname,(MDNS.hostname(i).length()+1));
// TODO check for separate ntp server
        MDNS.hostname(i).toCharArray(ntpServer_hostname,(MDNS.hostname(i).length()+1));
      }
    }
  }
  Serial.print(F("Hostname: "));
  Serial.print(MQTT_broker_hostname);
  Serial.println(F(" being used for MQTT_broker_hostname"));
  Serial.print(F("Hostname: "));
  Serial.print(ntpServer_hostname);
  Serial.println(F(" being used for ntpServer"));
  Serial.println();
#endif


// Start NTP support
// =================
  Serial.println(F("Starting UDP"));                 // Start UDP
  udp.begin(localPort);
  Serial.print(F("Local port: "));
#ifdef HN_ESP8266
  Serial.println(udp.localPort());
#endif
#ifdef HN_2560
  Serial.println(udp.remoteIP());
  //TODO get ntpServerIP
#endif
#ifdef HN_WiFi
  WiFi.hostByName(ntpServer_hostname, ntpServerIP);   // Get mqttbroker's IP address
#endif
  Serial.print(F("Local IP:   "));
  Serial.println(ntpServerIP);

  setupTime();          // initialize RTC using ntp, if available
  mscount = millis();   // initialize the millisecond counter

// Start MQTT support
// ==================
  MQTTClient.setServer(MQTT_broker_hostname, MQTT_port);
  MQTTClient.setCallback(MQTTcallback);

  exception_topic["Node"] = HN_Id;

  // Wait until connected to MQTT Broker
  // client.connect returns a boolean value
  Serial.println(F("Connecting to MQTT broker ..."));
  // Poll until connected.
  while (!sendMQTTStatus())
    ;

// Subscribe to the TOPICs

  Serial.println(F("Subscribing to MQTT topics ..."));
  for (int i = 0; i < MAXLISTEN; i++) {
    Serial.print(i+1);
    Serial.print(F(" - "));
    Serial.println(mqtt_listen_array[i]);
    do {
      MQTTClient.loop();
      Serial.print(F(" .. subscribing to "));
      Serial.println(mqtt_listen_array[i]);
      delay(100);
    } while (!MQTTClient.subscribe(mqtt_listen_array[i]));
  }
  currentTime = now();
  Serial.println(F("Setup Complete. Listening for topics .."));
// Create the recurring calls, to trigger at or after time
  Alarm.timerRepeat(1, flashLED);         // Every    second
  Alarm.timerRepeat(2, checkControls);    // Every  2 seconds
  Alarm.timerRepeat(5, hapiSensors);      // Every  5 seconds
  Alarm.alarmRepeat(3,30,0,updateRTC);    // 3:30am every day
}

void loop() {
  MQTTClient.loop();            // Check for MQTT topics
  Alarm.delay(0);
}

