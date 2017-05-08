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

void(* resetFunc) (void) = 0; //declare reset function @ address

boolean sendMQTTStatus(void){

  StaticJsonBuffer<128> hn_topic_status;                   // Status data for this HN
  JsonObject& status_topic = hn_topic_status.createObject();

// Publish current status
  // Identify HAPInode 
  status_topic["AssetId"] = HN_id;
  // Returns the current status of the HN itself
  // Includes firmware version, MAC address, IP Address, Free RAM and Idle Mode
  status_topic["FW"] = HAPI_FW_VERSION;
  status_topic["DIO"] = String(NUM_DIGITAL);
  status_topic["AIO"] = String(NUM_ANALOG);
  status_topic["Free SRAM"] = String(freeRam()) + "k";
  if (idle_mode == false){
    status_topic["Idle"] = "False";
  }else{
    status_topic["Idle"] = "True";
  }
  status_topic.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  Serial.println(MQTTOutput);

    // PUBLISH to the MQTT Broker
  if (MQTTClient.publish(mqtt_topic_status, MQTTOutput)) {
    return true;
  }
  // If the message failed to send, try again, as the connection may have broken.
  else {
    Serial.println("Status Message failed to publish. Reconnecting to MQTT Broker and trying again .. ");
    if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
      Serial.println("reconnected to MQTT Broker!");
      delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
      if (MQTTClient.publish(mqtt_topic_status, MQTTOutput)) {
        return true;
      }
      else {
        Serial.println("Status Message failed to publish after one retry.");
        return false;
      }
    }
    else {
      Serial.println("Connection to MQTT Broker failed...");
      return false;
    }
  }
}

boolean sendAllMQTTAssets(void) {
//Process digital pins
  for (int x = 0; x < NUM_DIGITAL; x++) {
    if (pinControl[x] > 0) {
      if (pinControl[x] < 5) {
        while (!(sendMQTTAsset(SENSORID_D_PIN, x)));  // Until it is sent
      }
    }
  }
//Process analog pins
  for (int x = 0; x < NUM_ANALOG; x++) {
    while (!(sendMQTTAsset(SENSORID_A_PIN, x+NUM_DIGITAL)));  // Until it is sent
  }
// Process Custom Functions
  for (int x = 0; x < CUSTOM_FUNCTIONS; x++) {
    while (!(sendMQTTAsset(SENSORID_FN, x)));  // Until it is sent
  }
  return true;
}

boolean sendMQTTAsset(int SensorIdx, int Number) {
  //For custom functions
  FuncDef f;
  float funcVal = -1.0;
  StaticJsonBuffer<128> hn_topic_asset;                   // Sensor data for this HN
  JsonObject& asset_topic = hn_topic_asset.createObject();
  asset_topic["AssetId"] = HN_id;

  // Assembles a response with values from pins and custom functions
  // Returns a JSON string  ("pinnumber":value,"custom function abbreviation":value}

//  if ((SensorIdx == SENSORID_D_PIN) || (SensorIdx == SENSORID_A_PIN)) {
    asset_topic["SId"] = String(SensorIdx) + "." + String(Number);
//  }
//  else {
//    asset_topic["SId"] = String(SensorIdx);
//  }

  switch(SensorIdx) {
    case SENSORID_D_PIN:
      asset_topic["name"] =  "DIO";
      asset_topic["unit"] =  "";
//      asset_topic["virtual"] =  "0";
//      asset_topic["context"] =  "Sensor";
//      asset_topic["system"] =  "node";
//      asset_topic["enabled"] =  "1";
      asset_topic["data"] =  (String)digitalRead(Number);
      break;
    case SENSORID_A_PIN:
      asset_topic["name"] =  "AIO";
      asset_topic["unit"] =  "";
//      asset_topic["virtual"] =  "0";
//      asset_topic["context"] =  "Sensor";
//      asset_topic["system"] =  "node";
//      asset_topic["enabled"] =  "1";
      asset_topic["data_field"] =  (String)analogRead(Number);
      break;
    case SENSORID_FN:
      f = HapiFunctions[Number];
      asset_topic["name"] =  (String)f.fName;
      asset_topic["unit"] =  (String)f.fUnit;
//      asset_topic["virtual"] =  "0";
//      asset_topic["context"] =  "Sensor";
//      asset_topic["system"] =  "node";
//      asset_topic["enabled"] =  "1";
      funcVal = f.fPtr(Number);
      asset_topic["data"] =  String((int)funcVal);
      break;
    default:
      break;
  }

  asset_topic.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  Serial.println(MQTTOutput);

// PUBLISH to the MQTT Broker
  if (MQTTClient.publish(mqtt_topic_asset, MQTTOutput)) {
    return true;
  }
// If the message failed to send, try again, as the connection may have broken.
  else {
    Serial.println("Send Asset Message failed. Reconnecting to MQTT Broker and trying again .. ");
    if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
      Serial.println("reconnected to MQTT Broker!");
      delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
      if (MQTTClient.publish(mqtt_topic_asset, MQTTOutput)) {
        return true;
      }
      else {
        Serial.println("Send Asset Message failed after one retry.");
        return false;        
      }
    }
    else {
      Serial.println("Connection to MQTT Broker failed...");
      return false;
    }
  }
}

void MQTTcallback(char* topic, byte* payload, unsigned int length) {

  int i, j, k;
  const char* AssetId = "WrongId";
  const char* Command = "NoCommand";
  StaticJsonBuffer<200> hn_topic_command;            // Parsing buffer

  Serial.print("Topic: ");
  Serial.print(topic);
  Serial.print(" Length: ");
  Serial.println(length);
  Serial.print("Raw payload: ");
  for(i = 0; i < length; i++){
    Serial.print((char)payload[i]);
    MQTTInput[i] = (char)payload[i];
  }
  MQTTInput[i] = 0x00;
  Serial.print(" buffer: ");  
  Serial.print(MQTTInput);
  Serial.println();

  //Parse the topic data
  JsonObject& command_topic = hn_topic_command.parseObject(MQTTInput);
  if (!command_topic.success())
  {
    Serial.println("parseObject() failed");
    return;
  } else {
    Serial.println("Parsing .. ");
    for (JsonObject::iterator it=command_topic.begin(); it!=command_topic.end(); ++it)
    {
      Serial.print(it->key);
      Serial.print(":");
      Serial.println(it->value.asString());
    }
       
    if (command_topic.containsKey("AssetId")) {
      AssetId = command_topic["AssetId"];
    }

    if (command_topic.containsKey("Cmnd")) {
      Command = command_topic["Cmnd"];
    }
 
    if (strcmp(AssetId, hostString) == 0) {
      if (strcmp(topic, "COMMAND/") == 0) {
        if (strcmp(Command, "assets") == 0) sendAllMQTTAssets();
        if (strcmp(Command, "status") == 0) sendMQTTStatus();
      }
      else if (strcmp(topic, "EXCEPTION/") == 0) {
      }
    /* 
    else if (strcmp(topic, "STATUS/QUERY") == 0) {
      if (strcmp(AssetId, hostString) == 0) sendMQTTStatus();
      Serial.print("Found STATUS/QUERY = ");
      Serial.println(AssetId);
    }
    else if (strcmp(topic, "ASSET/QUERY") == 0) {
      if (strcmp(AssetId, hostString) == 0) sendAllMQTTAssets();
      Serial.print("Found ASSET/QUERY = ");
      Serial.println(AssetId);
    }
    */
    }
  }
}
