/*
*********************************************************************
  Copyright 2013 Maya Culpa, LLC

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*********************************************************************

  Sketch Date: October 20th 2013 11:00:00 EDT
  Sketch Version: v1.0.0

  HAPI Command Language Interpreter (CLI) for the Arduino Mega
  Implements Arduino as a Remote Terminal Unit (RTU) for use in Monitoring and Control
  Arduino Listens on the Ethernet Port for Commands and then executes commands

  Target Board: Arduino Mega 2560
  Communications Protocol: Ethernet
*/

#include <DHT.h>
#include <SPI.h>
//#include <Adafruit_CC3000.h>
#include <Ethernet.h>
#include <stdlib.h>
#include <math.h>
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define PIN_MAP_SIZE 108 // Array size for default state data, 2 bytes per digital I/O pin, 1st byte = State, 2nd byte = Value
#define ONE_WIRE_BUS 8
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature wp_sensors(&oneWire);

//**** Begin Main Variable Definition Section ****
String HAPI_CLI_VERSION = "v2.1";  // The version of the firmware the RTU is running
boolean idle_mode = false;         // a boolean representing the idle mode of the RTU
String RTUID = "RTU1";             // This RTUs Unique ID Number - unique across site
String inputString = "";           // A string to hold incoming data
String inputCommand = "";          // A string to hold the command
String inputPort = "";             // A string to hold the port number of the command
String inputControl = "";          // A string to hold the requested action of the command
String inputTimer = "0";           // A string to hold the length of time to activate a control
boolean stringComplete = false;    // A boolean indicating when received string is complete (a \n was received)
//**** End Main Variable Definition Section ****

//**** Begin Communications Section ****
// the media access control (ethernet hardware) address for the shield:
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
//byte ip[] = { 192, 168, 0, 50 };
//byte gateway[] = { 192, 168, 0, 1 };
//byte subnet[] = { 255, 255, 255, 0 };
EthernetServer rtuServer(80);
//**** End Communications Section ****


//Define the Reset function
void(* resetFunc) (void) = 0; //declare reset function @ address 0

//**** Begin DHT Device Section ****
//Define DHT devices and allocate resources
#define NUM_DHTS 1 //total number of DHTs on this device
DHT dht1(40, DHT22); //For each DHT, create a new variable given the pin and Type
DHT dhts[1] = {dht1}; //add the DHT device to the array of DHTs


//**** Begin Default State Data Section ****
byte data[PIN_MAP_SIZE]; //Stores two bytes for every pin, 0 - 53 and A0 - A15
//First byte is the default state of the pin
//0=Ignored, 1=pinMode INPUT, 2=pinMode INPUT_PULLUP, 3=pinMode OUTPUT, 4=pinMode OUTPUT
//Second byte contains the default value
//1 and 0 = set the pin mode to INPUT, value is ignored
//Example: 31 in the 0,1 positions = set pin #1 to OUTPUT mode with a value is 1 (HIGH)

String defaultData = ""; //Stores the incoming string of default data
//**** End Default State Data Section ****


//**** Begin Custom Functions Section ****
//Custom functions are special functions for reading sensors or controlling devices. They are
//used when setting or a reading a pin isn't enough, as in the instance of library calls.

#define CUSTOM_FUNCTIONS 4 //The number of custom functions supported on this RTU

typedef float (* GenericFP)(int); //generic pointer to a function that takes an int and returns a float

struct FuncDef {   //define a structure to associate a Name to generic function pointer.
  String fName;
  String fType;
  int fPort;
  GenericFP fPtr;
};

//Create a FuncDef for each custom function
FuncDef func1 = {"tmp", "dht", -1, &readTemperature};
FuncDef func2 = {"hmd", "dht", -1, &readHumidity};
FuncDef func3 = {"trm", "thermistor", 56, &readThermistorTemp};
FuncDef func4 = {"res1tmp", "DS18B20", ONE_WIRE_BUS, &readWaterTemperature};
//FuncDef func5 = {"phl", "pH Sensor", PH_SENSORPIN, &readpH};

FuncDef HapiFunctions[CUSTOM_FUNCTIONS] = {func1, func2, func3, func4};
//**** End Custom Functions Section ****


// Setup digital pin use definitions
// 0 not used or reserved;  1 digital input; 2 digital input_pullup; 3 digital output; 4 analog output; 5 analog input;
// Analog input pins are assumed to be used as analog input pins

int pinControl[70] = {
  0, 0, 4, 4, 0, 0, 3, 3, 0, 0, //  0 -  9
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, // 10 - 19
  0, 0, 3, 3, 3, 3, 3, 3, 1, 1, // 20 - 29
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 30 - 39
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 40 - 49
  0, 0, 0, 0,             // 50 - 53
  5, 5, 5, 5, 5, 5, 5, 5, 5, 5, // 54 - 63 //Analog Inputs
  5, 5, 0, 0, 0, 0        // 64 - 69 //Analog Inputs
};
// End of Definitions

String getPinArray() {
  String response = "";
  for (int i = 0; i < 70; i++) {
    if (i <= 53) {
      response = response + String(i) + String(pinControl[i]);
    }
    else {
      response = response + "A" + String(i - 54) + String(pinControl[i]);
    }
  }
  return response;
}

void assembleResponse(String &responseString, String varName, String value) {
  if (responseString.equals("")) {
    responseString = "{";
  }

  if (!varName.equals("")) {
    responseString = responseString + "\"" + varName + "\"" + ":" + "\"" + value + "\"" + ",";
  }
  else {
    if (responseString.endsWith(",")) {
      responseString = responseString.substring(0, responseString.length() - 1);
    }
    responseString = responseString + "}";
  }
}

void writeLine(String response, boolean EOL) {
  char inChar;

  for (int i = 0; i < response.length(); i++)
  {
    inChar = (char)response.charAt(i);
    Serial.write(inChar);
    rtuServer.write(inChar);
  }
  if ((String)inChar != "\n") {
    if (EOL) {
      rtuServer.write("\r\n");
      Serial.write("\r\n");
    }
  }
}

//***** Default State Management Functions *****
void setDefaultState() {
  int pin;
  byte state;
  byte value;

  pin = 0;
  for (int i = 0; i < PIN_MAP_SIZE; i += 2) {
    state = EEPROM.read(i) - 48;
    value = EEPROM.read(i + 1) - 48;

    switch (state) {
      case 1:
        pinMode(pin, INPUT);
        break;
      case 2:
        pinMode(pin, INPUT_PULLUP);
        break;
      case 3:
        pinMode(pin, OUTPUT);
        digitalWrite(pin, value);
        break;
    }
    pin = pin + 1;
  }
}

void writeDefaultData(byte stateData[]) {
  for (int i = 0; i < PIN_MAP_SIZE; i++) {
    EEPROM.write(i, stateData[i]);
  }
}

//***** Default State Management Functions *****
float readHumidity(int iDevice) {
  // readHumidity  - Uses the DHT Library to read the current humidity
  float returnValue;
  float h;
  h = dhts[iDevice].readHumidity();

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
  h = dhts[iDevice].readTemperature();

  if (isnan(h)) {
    returnValue = -1;
  }
  else {
    returnValue = h;
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
  // resistance at 25 degrees C
  int THERMISTORNOMINAL = 10000;
  int TEMPERATURENOMINAL = 22;
  int NUMSAMPLES = 10;
  long BCOEFFICIENT = 4050000;
  int SERIESRESISTOR = 9710;
  int samples[NUMSAMPLES];

  float reading = 0;
  for (int i = 0; i < NUMSAMPLES; i++) {
    reading += analogRead(iDevice);
    delay(10);
  }
  reading /= NUMSAMPLES;
  reading = 1023 / reading - 1;
  reading = SERIESRESISTOR / reading;

  float steinhart;
  steinhart = reading / THERMISTORNOMINAL; // (R/Ro)
  steinhart = log(steinhart); // ln(R/Ro)
  steinhart /= BCOEFFICIENT; // 1/B * ln(R/Ro)
  steinhart += 1.0 / (TEMPERATURENOMINAL + 273.15); // + (1/To)
  steinhart = 1.0 / steinhart; // Invert
  steinhart -= 273.15; // convert to C

  return steinhart;
}

String getCommand(EthernetClient client) {
  stringComplete = false;
  char inChar;
  inputString = "";
  while ((client.available() > 0) && (stringComplete == false)) {
    inChar = (char)client.read();  // read the bytes incoming from the client:
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }

  if (inputString == "") {
    while ((Serial.available() > 0) && (stringComplete == false)) {
      inChar = (char)Serial.read();  // read the bytes incoming from the client:
      inputString += inChar;
      if (inChar == '\n') {
        stringComplete = true;
      }
    }
  }

  return inputString;
}

String buildResponse() {
  String response = "";
  assembleResponse(response, "name", RTUID);
  assembleResponse(response, "version", HAPI_CLI_VERSION);

  //Process digital pins
  for (int x = 0; x < 54; x++) {
    if (pinControl[x] > 0) {
      if (pinControl[x] < 5) {
        assembleResponse(response, (String)x, (String)digitalRead(x));
      }  // END of if pinControl<4
    } // END OF if pinControl>0 -  Returns a JSON Output String  ("pinnumber":status,"pinnumber":status} 0 or 1 for Pins declared Input, Input_PullUp, or Output
  }   // Next x

  //Process analog pins
  for (int x = 0; x < 16; x++) {
    assembleResponse(response, (String)(x + 54), (String)analogRead(x));
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

String getConnectionDetails() {
  String retval = "";
  String macstring = (char*)mac;

  retval = RTUID + "\r\n";
  retval = retval + "Firmware " + HAPI_CLI_VERSION + "\r\n";

  retval = retval + "MAC=";
  retval = retval + "0x" + String(mac[0], HEX) + ":";
  retval = retval + "0x" + String(mac[1], HEX) + ":";
  retval = retval + "0x" + String(mac[2], HEX) + ":";
  retval = retval + "0x" + String(mac[3], HEX) + "\n";

  retval = retval + "IP=";
  retval = retval + String(Ethernet.localIP()[0]) + ".";
  retval = retval + String(Ethernet.localIP()[1]) + ".";
  retval = retval + String(Ethernet.localIP()[2]) + ".";
  retval = retval + String(Ethernet.localIP()[3]) + "\n";

  //  retval = retval + "Gateway=";
  //  retval = retval + String(gateway[0]) + ".";
  //  retval = retval + String(gateway[1]) + ".";
  //  retval = retval + String(gateway[2]) + ".";
  //  retval = retval + String(gateway[3]) + "\n";
  //
  //  retval = retval + "Subnet=";
  //  retval = retval + String(subnet[0]) + ".";
  //  retval = retval + String(subnet[1]) + ".";
  //  retval = retval + String(subnet[2]) + ".";
  //  retval = retval + String(subnet[3]) + "\n";

  retval = retval + "Free SRAM: " + String(freeRam()) + "k\n";

  return retval;

}


int freeRam ()
{
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

void setup() {
  Serial.begin(115200);
  Serial.println("Initializing network....");
  //  Ethernet.begin(mac, ip, gateway, subnet);
  Ethernet.begin(mac);
  Serial.println("Starting communications server....");
  rtuServer.begin();
  Serial.println(getConnectionDetails());
  Serial.println("Listening for connections...");

  inputString.reserve(200);  // reserve 200 bytes for the inputString:
  // Initialize Digital Pins for Input or Output - From the Array pinControl

  for (int x = 0; x < 70; x++) {
    if (pinControl[x] == 1) {
      pinMode(x, INPUT); // Digital Input
    }
    if (pinControl[x] == 2) {
      pinMode(x, INPUT_PULLUP); // Digital Inputs w/ Pullup Resistors
    }
    if (pinControl[x] == 3) {
      pinMode(x, OUTPUT); // Digital Outputs
    }
    if (pinControl[x] == 4) {
      pinMode(x, OUTPUT); // Analog Outputs
    }
  }

  for (int x = 0; x < NUM_DHTS; x++) {
    dhts[x].begin();
  }

  wp_sensors.begin();
  Serial.println("Setup Complete");
}

void loop() {
  // wait for a new client:
  EthernetClient client = rtuServer.available();
  if (client) {
    inputString = getCommand(client);
    inputString.trim();
    inputString.toLowerCase();
    inputTimer = "0";

    if (inputString != "" && inputString != "\r\n") {
      inputCommand = inputString.substring(0, 3);
      boolean cmdFound = false;

      if (inputCommand == "aoc") {
        cmdFound = true;
        inputPort = inputString.substring(3, 6);
        inputControl = inputString.substring(6, 9);
        if (pinControl[inputPort.toInt()] == 5) {
          analogWrite(inputPort.toInt(), inputControl.toInt());
        } // END OF if pinControl=5 -  Returns OK
      }  // END Of aoc

      // doc (Digital Output Control) Sets a single digital output
      if (inputCommand == "doc") {
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

        } // END OF if pinControl=3 - just making sure this is an OUTPUT pin  - No ok<cr> sent if it is not
      }  // END Of doc

      // Get pin modes
      if (inputCommand == "gpm") {
        cmdFound = true;
        String response = getPinArray();
        writeLine(response, true); //Send a response back to client
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
      if (inputCommand == "res") {
        cmdFound = true;
        for (int x = 0; x < 54; x++) {
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

      // sds - Set RTU to the Default State stored in EEPROM
      if (inputCommand == "sds") {
        cmdFound = true;
        writeLine("setting state", true);
        setDefaultState();
      }

      // Get the RTU Status
      if (inputCommand == "sta") {
        cmdFound = true;
        writeLine(getConnectionDetails(), true);
        setDefaultState();
      }

      // wds - Write Default State data to EEPROM
      if (inputCommand == "wds") {
        cmdFound = true;
        defaultData = inputString.substring(3, inputString.length());

        for (int i = 0; i < PIN_MAP_SIZE; i++) {
          data[i] = (byte)defaultData.charAt(i);
        }
        writeDefaultData(data);
      }

      if (inputCommand != "gpm") {
        writeLine(buildResponse(), true); //Send a response back to client
      }
      client.stop();
    }
  }
}




