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

#define MILLISECONDS_PER_SECOND (1000)

//**** Begin Board Configuration Section ****

// Board Type
// ==========
//#define HN_2560         // Must have ethernet shield

//**ESP Based
// Board Type
//#define HN_ESP8266
#define HN_ESP32

// Connection Type
// ===============
//#define HN_ENET          // Define for Ethernet shield
#define HN_WiFi           // Define for WiFi support

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

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Bounce2.h> // Used for "debouncing" inputs

// =====================================================================
// Make sure to update these files for your own WiFi and/or MQTT Broker!
// =====================================================================
#include "nodecomms.h"      // WiFi, UDP, NTP and MQTT setup
#include "nodeboard.h"      // Node default pin allocations

//**** Begin Main Variable Definition Section ****
int loopcount;                      // Count of times through main loop (for LED etc)
unsigned long old_millis; // Unit is one millisecond.
signed long millis_accumulator; // Unit is one millisecond.
unsigned long epoch;                // UTC seconds

String HAPI_FW_VERSION = F("v3.0");    // The version of the firmware the HN is running
#ifdef HN_ENET
String HN_base = F("HN2");             // Prefix for mac address
#endif
#ifdef HN_ESP8266
String HN_base = F("HN3");             // Prefix for mac address
#endif
#ifdef HN_ESP32
String HN_base = F("HN4");             // Prefix for mac address
#endif

String HN_Id = F("HNx");              // HN address
String HN_status = F("Online");

boolean idle_mode = false;         // a boolean representing the idle mode of the HN
boolean metric = true;             // should values be returned in metric or US customary units
String inputString = F("");           // A string to hold incoming data
String inputCommand = F("");          // A string to hold the command
String inputPort = F("");             // A string to hold the port number of the command
String inputControl = F("");          // A string to hold the requested action of the command
String inputTimer = F("0");           // A string to hold the length of time to activate a control
boolean stringComplete = false;    // A boolean indicating when received string is complete (a \n was received)
//**** End Main Variable Definition Section ****

//**** Begin Communications Section ****
// the media access control (ethernet hardware) address for the shield
// Need to manually change this for USB, Ethernet
byte mac[] = { 0x55, 0x55, 0x55, 0x55, 0x55, 0x55 };
char mac_str[16] = F("555555555555");
char hostString[32] = {0};              // for mDNS Hostname

// ntp config
IPAddress timeServerIP;               // Place to store IP address of mqttbroker.local
const char* ntpServerName = F("mqttbroker"); // Assume mqttbroker is also the time server
const int NTP_PACKET_SIZE = 48;       // NTP time stamp is in the first 48 bytes of the message
byte packetBuffer[ NTP_PACKET_SIZE];  //buffer to hold incoming and outgoing packets
unsigned int localPort = UDP_port;    // local port to listen for UDP packets

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
const char* clientID = F("HAPInode");
const char* mqtt_topic_status = F("STATUS/RESPONSE/");     // General Status topic
const char* mqtt_topic_asset = F("ASSET/RESPONSE/");       // Genral Asset topic
char mqtt_topic[256] = F("COMMAND/");                      // Topic for this HN
const char* mqtt_topic_exception = F("EXCEPTION/");        // General Exception topic

#define MAXTOPICS 5
#define STATUSSTART 0
#define ASSETSTART 1
#define CONFIGSTART 4
char* mqtt_topic_array[MAXTOPICS] = {
  F("STATUS/QUERY"),
  F("ASSET/QUERY"),
  F("ASSET/QUERY/"),
  F("ASSET/QUERY/*"),
  F("CONFIG/QUERY/")
};
#define MAXLISTEN 11
char* mqtt_listen_array[MAXLISTEN] = {
  F("COMMAND/"),
  F("EXCEPTION/"),
  F("STATUS/QUERY"),
  F("STATUS/QUERY/"),
  F("STATUS/QUERY/#"),
  F("ASSET/QUERY"),
  F("ASSET/QUERY/"),
  F("ASSET/QUERY/#"),
  F("CONFIG/QUERY"),
  F("CONFIG/QUERY/"),
  F("CONFIG/QUERY/#")
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

const int ledPin = 2; // Use the built-in led for visual feedback
boolean ledState = false;

// Flow meter devices
Bounce flowrate = Bounce();   // Use bouncer object to measure flow rate
int WaterFlowRate = 0;

//LIGHT Devices

//oneWire Devices
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature wp_sensors(&oneWire);

//Define DHT devices and allocate resources
#define NUM_DHTS 1        //total number of DHTs on this device
#define DHTTYPE DHT22     // Sets DHT type

DHT dht1(DHT_SENSORPIN, DHT22);   //For each DHT, create a new variable given the pin and Type
DHT dhts[1] = {dht1};             //add the DHT device to the array of DHTs

// Custom function devices
//Custom functions are special functions for reading sensors or controlling devices. They are
//used when setting or a reading a pin isn't enough, as in the instance of library calls.
typedef float (* GenericFP)(int); //generic pointer to a function that takes an int and returns a float
struct FuncDef {   //define a structure to associate a Name to generic function pointer.
  char* fName;
  const char* fType;
  const char* fUnit;
  int fPin;
  GenericFP fPtr;
};

#define ArrayLength(x) (sizeof(x)/sizeof(*(x)))
// Create a FuncDef for each custom function
// Format: abbreviation, context, pin, data function
FuncDef sfunc1 = {F("tmp"), F("Env"), F("C"), -1, &readTemperatured};
FuncDef sfunc2 = {F("hum"), F("Env"), F("%"), -1, &readHumidity};
FuncDef sfunc3 = {F("lux"), F("Env"), F("lux"), sLux_PIN, &readLightSensor};
FuncDef sfunc4 = {F("tmw"), F("Water"), F("C"), ONE_WIRE_BUS, &read1WireTemperature};
FuncDef sfunc5 = {F("phv"), F("Water"), F("pH"), spH_PIN, &readpH};
FuncDef sfunc6 = {F("tds"), F("Water"), F("ppm"), sTDS_PIN, &readTDS};
FuncDef sfunc7 = {F("flo"), F("Water"), F("lpm"), sFlow_PIN, &readFlow};
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
CFuncDef cfunc1 = {F("ppw"), F("Pump"), F("lpm"), 1, &controlPumps, &readSensorPin};
CFuncDef cfunc2 = {F("ppf"), F("Pump"), F("lpm"), 2, &controlPumps, &readSensorPin};
CFuncDef cfunc3 = {F("ppn"), F("Pump"), F("lpm"), 3, &controlPumps, &readTDS};
CFuncDef cfunc4 = {F("pHU"), F("Pump"), F("lpm"), 4, &controlPumps, &readpH};
CFuncDef cfunc5 = {F("pHD"), F("Pump"), F("lpm"), 5, &controlPumps, &readpH};
CFuncDef cfunc6 = {F("lmp"), F("Lamp"), F("lpm"), 6, &controlLamps, &readLightSensor};
CFuncDef HapicFunctions[] = {cfunc1, cfunc2, cfunc3, cfunc4, cfunc5, cfunc6};

struct ControlData {
  const char* hc_name;              // abbreviation
  int hc_controlpin;
  boolean hc_polarity;              // Active low control output
  unsigned long hc_start;           // Start time (unix time)
  unsigned long hc_end;             // End time (unix time)
  unsigned long hc_repeat;          // Repeat interval (seconds)
  boolean hc_active;               // Pump running or not, Lamp on or off
  int hcs_sensepin;                 // Pin used for iPtr function control
  int hcs_onValue;                  // Sensor value at which control turns On
  int hcs_offValue;                 // Sensor value at which control turns Off
};

ControlData ccontrol1 = {F("ppw"), cWatr_PIN, true, 0, 0, 0, false, sFlow_PIN, 0, 0};        // Water
ControlData ccontrol2 = {F("ppf"), cFill_PIN, true, 0, 0, 0, false, sFloat_PIN, 0, 0};       // Fill
ControlData ccontrol3 = {F("ppn"), cNutr_PIN, true, 0, 0, 0, false, sTDS_PIN, 0, 0};         // Nutrient
ControlData ccontrol4 = {F("pHU"), cpHUp_PIN, true, 0, 0, 0, false, spH_PIN, 0, 0};          // pHUp
ControlData ccontrol5 = {F("pHD"), cpHDn_PIN, true, 0, 0, 0, false, spH_PIN, 0, 0};          // pHDown
ControlData ccontrol6 = {F("lmp"), cLamp_PIN, true, 0, 0, 0, false, sLux_PIN, 0, 0};         // Lamp
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
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH);

// Start Debug port and sensors
// ============================
  setupSensors();             // Initialize I/O and start devices
  inputString.reserve(200);   // reserve 200 bytes for the inputString
  Serial.begin(115200);       // Debug port

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
  Serial.println();
  Serial.print(F("IP  address: "));
  Serial.println(WiFi.localIP());
  Serial.print(F("Hostname   : "));
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
  Serial.println(F(" mDNS responder started"));

  Serial.println(F("Sending mDNS query"));
  int n = MDNS.queryService(F("workstation"), F("tcp")); // Send out query for workstation tcp services
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
    }
  }
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
  //TODO get timeServerIP
#endif
#ifdef HN_WiFi
  WiFi.hostByName(ntpServerName, timeServerIP);   // Get mqttbroker's IP address
#endif
  Serial.print(F("Local IP:   "));
  Serial.println(timeServerIP);
  getNTPTime();
  initialize_epoch_timekeeping(void);

// Start MQTT support
// ==================
  MQTTClient.setServer(MQTT_broker_address, MQTT_port);
  MQTTClient.setCallback(MQTTcallback);

  exception_topic[F("Node")] = HN_Id;

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

  Serial.println(F("Setup Complete. Listening for topics .."));
}

void initialize_epoch_timekeeping(void)
{
  old_millis = millis();
  millis_accumulator = -MILLISECONDS_PER_SECOND;
}

void poll_epoch_timekeeping(void)
{
  /* call this at least once per second, preferably many times per second */
  unsigned long new_millis;

  new_millis = millis();
  millis_accumulator += new_millis - old_millis;
  if (millis_accumulator >= 0) {
    millis_accumulator -= MILLISECONDS_PER_SECOND;
    epoch++;
  }
  old_millis = new_millis;
}

void loop() {
  poll_epoch_timekeeping();

  // Wait for a new event, publish topic
  if ((loopcount++ % 3600) == 0) {
    getNTPTime();
    loopcount = 0;
  }

  checkControls();              // Check all the timers on the controls
  MQTTClient.loop();            // Check for MQTT topics
  flashLED();                   // Flash LED - slow blink

  delay(100);
}

void flashLED(void) {
  if ((loopcount++ % 100) == 0) {
    ledState = !ledState;
    digitalWrite(ledPin, ledState ? HIGH : LOW);
    hapiSensors();
  }
}

