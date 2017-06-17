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

HAPI Remote Terminal Unit Firmware Code V3.1.0
Authors: Tyler Reed, Mark Miller
ESP Modification: John Archbold

Sketch Date: June 13th, 2017
Sketch Version: V3.1.0
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
// Initialize Digital Pins for Input or Output - From the arrays pinControl and pinDefaults
  for (int i = 0; i < ArrayLength(pinControl); i++) {
    switch (pinControl[i]) {
      case DIGITAL_INPUT_PIN:
        pinMode(i, INPUT);
        break;
      case DIGITAL_INPUT_PULLUP_PIN:
        pinMode(i, INPUT_PULLUP);
        break;
      case DIGITAL_OUTPUT_PIN:
        pinMode(i, OUTPUT);
        digitalWrite(i, (pinDefaults[i] ? HIGH : LOW));
        break;
      case ANALOG_OUTPUT_PIN:
        pinMode(i, OUTPUT);
        break;
      default:
        break;
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
  pinMode(sWtrFlow_PIN, INPUT);
  flowrate.attach(sWtrFlow_PIN);
  flowrate.interval(5);

// Start the I2C
  Wire.begin(SDA_PIN,SCL_PIN);      // Default
  Wire.setClock(400000);  // choose 400 kHz I2C rate
  Alarm.delay(100);
}

String getPinArray() {
  // Returns all pin configuration information
  String response = "";
  for (int i = 0; i < NUM_DIGITAL+NUM_ANALOG; i++) {
    if (i < NUM_DIGITAL) {
      response += String(i) + String(pinControl[i]);
    }
    else {
      response += "A" + String(i - NUM_DIGITAL) + String(pinControl[i]);
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
//  Serial.print(F("DHT Humidity: "));
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
//  Serial.print(F("DHT Temperature: "));
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
//  Serial.print(F("18B20 Temperature: "));
//  Serial.println(returnValue);
  return returnValue;
}

float readpH(int Device) {
  // readpH - Reads pH from an analog pH sensor (Robot Mesh SKU: SEN0161, Module version 1.0)
  unsigned long int avgValue;  //Store the average value of the sensor feedback
  float b;
  int buf[10], temp;
  ControlData d;
  d = HapicData[Device];

  for (int i = 0; i < 10; i++) // Get 10 sample values from the sensor
  {
    buf[i] = analogRead(d.hcs_sensepin);  // Get the correct pin from the ControlData structure
    delay(10);
  }
  for (int i = 0; i < 9; i++) // Sort the analog from small to large
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
  for (int i = 2; i < 8; i++)               // Take the average value of 6 center samples
    avgValue += buf[i];
  float phValue = ((((float)avgValue * 5.0) / 1024) / 6); // Convert the analog into millivolt

  phValue = 3.5 * phValue;                  //convert the millivolt into pH value
//  Serial.print(F("pH: "));
//  Serial.println(phValue);
  return phValue;
}

float readTDS(int Device) {
  // readTDS - Reads pH from an analog TDS sensor
  unsigned long int avgValue;  //Store the average value of the sensor feedback
  float b;
  int buf[10], temp;
  ControlData d;
  d = HapicData[Device];

  for (int i = 0; i < 10; i++) // Get 10 sample values from the sensor
  {
    buf[i] = analogRead(d.hcs_sensepin);  // Get the correct pin from the ControlData structure
    delay(10);
  }
  for (int i = 0; i < 9; i++) // Sort the analog from small to large
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
  for (int i = 2; i < 8; i++)               // Take the average value of 6 center samples
    avgValue += buf[i];
  float TDSValue = ((((float)avgValue * 5.0) / 1024) / 6); // Convert the analog into millivolt

//TODO Need temperature compensation for TDS
  TDSValue = 1.0 * TDSValue;                  // Convert the millivolt into TDS value
//  Serial.print(F("TDS: "));
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

float readLightSensor(int Device) {
  // Simple code to read a Light value from a CDS sensor, with 10k to ground
  float Lux;
  ControlData d;
  d = HapicData[Device];

  int RawADC = analogRead(d.hcs_sensepin);
  //TODO
  Lux = (float)RawADC; // Need to do some processing to get lux from CDS reading
  return Lux;
}

float readFlow(int Device) {
  // readWaterFlowRate  - Uses an input pulse that creates an average flow rate
  //                      The averaging is done in software and stores a 30second rolling count
  ControlData d;
  d = HapicData[Device];

  //TODO
  return (float)WaterFlowRate;
}

float readSensorPin(int Device) {
  float pinData;
  //TODO
  return pinData;
}

void hapiSensors(void) {
  for (int device = 0; device < ArrayLength(HapisFunctions); device++) {
    currentTime = now();                  // Set the time
    sendMQTTAsset(SENSORID_FN, device);   // Read the sensor value
  }
}

