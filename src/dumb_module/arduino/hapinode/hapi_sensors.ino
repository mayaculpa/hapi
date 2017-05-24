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

void setupSensors(void){
  int i;
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

// Start the DHT-22
  dht1.begin();
  /*for (int x = 0; x < NUM_DHTS; x++) {
    dhts[x].begin();
  }*/

// Start the DS18B20
  wp_sensors.begin();

// Start the flow sensor
  pinMode(sFlow_PIN, INPUT);
  flowrate.attach(sFlow_PIN);
  flowrate.interval(5);
}

String getPinArray() {
  // Returns all pin configuration information
  String response = "";
  for (int i = 0; i < NUM_DIGITAL+NUM_ANALOG; i++) {
    if (i <= (NUM_DIGITAL-1)) {
      response = response + String(i) + String(pinControl[i]);
    }
    else {
      response = response + "A" + String(i - NUM_DIGITAL) + String(pinControl[i]);
    }
  }
  return response;
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
//  Serial.print("DHT Humidity: ");
//  Serial.println(returnValue);
  return returnValue;
}

float readTemperatured(int iDevice) {
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
//  Serial.print("DHT Temperature: ");
//  Serial.println(returnValue);
  return returnValue;
}

float read1WireTemperature(int iDevice) {
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
//  Serial.print("18B20 Temperature: ");
//  Serial.println(returnValue);
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
//  Serial.print("pH: ");
//  Serial.println(phValue);
  return phValue;
}

float readTDS(int iDevice) {
  // readTDS - Reads pH from an analog TDS sensor
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
  float TDSValue = (float)avgValue * 5.0 / 1024 / 6; //convert the analog into millivolt

//TODO Need temperature compensation for TDS
  TDSValue = 1.0 * TDSValue;                  //convert the millivolt into TDS value
//  Serial.print("TDS: ");
//  Serial.println(TDSValue);
  return TDSValue;
}

//  Type                Ambient light (lux)  Photocell resistance (Ω)
//
//  Dim hallway         0.1 lux               600KΩ
//  Moonlit night       1 lux                 70 KΩ
//  Dark room           10 lux                10 KΩ
//  Dark overcast day   Bright room 100 lux   1.5 KΩ
//  Overcast day        1000 lux              300 Ω

float readLightSensor(int iDevice) {
  // Simple code to read a Light value from a CDS sensor, with 10k to ground
  float Lux;
  int RawADC = analogRead(iDevice);
//TODO
  Lux = (float)RawADC; // Need to do some processing to get lux from CDS reading
  return Lux;
}

float readFlow(int iDevice) {
  // readWaterFlowRAte  - Uses an input pulse that creates an average flow rate
  //                      The averaging is done in software and stores a 30second rolling count
//TODO
return (float)WaterFlowRate;
}

float readSensorPin(int iDevice) {
   float pinData;
//TODO
return pinData;
}

boolean hapiSensors(void) {
  for (int i = 0; i < ArrayLength(HapisFunctions); i++) {
    sendMQTTAsset(SENSORID_FN, i);         // Sensor values
  }
}

