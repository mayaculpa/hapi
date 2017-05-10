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
  JsonObject& status_message = hn_topic_status.createObject();

// Publish current status
  // Identify HAPInode 
  status_message["AssetId"] = HN_id;
  // Returns the current status of the HN itself
  // Includes firmware version, MAC address, IP Address, Free RAM and Idle Mode
  status_message["FW"] = HAPI_FW_VERSION;
  status_message["time"] = epoch;
  status_message["DIO"] = String(NUM_DIGITAL);
  status_message["AIO"] = String(NUM_ANALOG);
  status_message["Free SRAM"] = String(freeRam()) + "k";
  if (idle_mode == false){
    status_message["Idle"] = false;
  }else{
    status_message["Idle"] = true;
  }

  status_message.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
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
        while (!(sendMQTTAsset(SENSORID_DIO, x)));  // Until it is sent
      }
    }
  }
//Process analog pins
  for (int x = 0; x < NUM_ANALOG; x++) {
    while (!(sendMQTTAsset(SENSORID_AIO, x+NUM_DIGITAL)));  // Until it is sent
  }
// Process Custom Functions
  for (int x = 0; x < CUSTOM_FUNCTIONS; x++) {
    while (!(sendMQTTAsset(SENSORID_FN, x)));  // Until it is sent
  }
  return true;
}

boolean sendMQTTAsset(int SensorIdx, int Number) {
  createAssetJSON(SensorIdx, Number);
  publishJSON(mqtt_topic_asset);
}

boolean sendMQTTException(int SensorIdx, int Number) {
  createAssetJSON(SensorIdx, Number);
  publishJSON(mqtt_topic_exception);
}
  
boolean createAssetJSON(int SensorIdx, int Number) {
  //For custom functions
  FuncDef f;
  int pinValue;
  float funcVal = -9.99;
  StaticJsonBuffer<256> hn_asset;                   // Sensor data for this HN
  JsonObject& asset_message = hn_asset.createObject();

// Set the AssetId
  asset_message["AssetId"] = HN_id;
  
  // Assembles a message with values from pins and custom functions
  // Returns a JSON string  ("pinnumber":value,"custom function abbreviation":value}

  JsonArray& SId = asset_message.createNestedArray("SId");  // create the SId array
  SId.add(SensorIdx);                                       //  add sensor type
  SId.add(Number);                                          //  add sensor number

  asset_message["time"] = epoch;                            // UTC time

  switch(SensorIdx) {
    case SENSORID_DIO:
      asset_message["name"] =  "DIO";
      asset_message["unit"] =  "";
//      asset_message["virtual"] =  "0";
//      asset_message["context"] =  "Sensor";
//      asset_message["system"] =  "node";
//      asset_message["enabled"] =  "1";
      pinValue = digitalRead(Number);
      asset_message["data"] = pinValue; 
      break;
    case SENSORID_AIO:
      asset_message["name"] =  "AIO";
      asset_message["unit"] =  "";
//      asset_message["virtual"] =  "0";
//      asset_message["context"] =  "Sensor";
//      asset_message["system"] =  "node";
//      asset_message["enabled"] =  "1";
      pinValue = analogRead(Number);
      asset_message["data"] = pinValue; 
      break;
    case SENSORID_FN:
      f = HapiFunctions[Number];
      asset_message["name"] =  (String)f.fName;
      asset_message["unit"] =  (String)f.fUnit;
//      asset_message["virtual"] =  "0";
//      asset_message["context"] =  "Sensor";
//      asset_message["system"] =  "node";
//      asset_message["enabled"] =  "1";
      funcVal = f.fPtr(Number);
      asset_message["data"] =  funcVal;     // Two decimal points
      break;
    default:
      break;
  }

  asset_message.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  Serial.println(MQTTOutput);
}

boolean publishJSON(const char* topic) {
// PUBLISH to the MQTT Broker
  if (MQTTClient.publish(topic, MQTTOutput)) {
    return true;
  }
// If the message failed to send, try again, as the connection may have broken.
  else {
    Serial.println("Send Message failed. Reconnecting to MQTT Broker and trying again .. ");
    if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
      Serial.println("reconnected to MQTT Broker!");
      delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
      if (MQTTClient.publish(topic, MQTTOutput)) {
        return true;
      }
      else {
        Serial.println("Send Message failed after one retry.");
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

  int i;
  const char* AssetId;    // AssetId for target HAPInode
  const char* Command;    // Command to execute
  int SensorIdx;          // Target Sensor Index
  int Number;             // Target pin# or function#
  int data;               // Data for output
  
  StaticJsonBuffer<200> hn_topic_command;            // Parsing buffer

// Copy topic to char* buffer
  for(i = 0; i < length; i++){
    MQTTInput[i] = (char)payload[i];
    Serial.print(MQTTInput[i]);
  }
  MQTTInput[i] = 0x00;
  Serial.println();

//Parse the topic data
  JsonObject& command_topic = hn_topic_command.parseObject(MQTTInput);
  if (!command_topic.success())
  {
    return;
  }
  else {
    Serial.println("Parsing .. ");
    for (JsonObject::iterator it=command_topic.begin(); it!=command_topic.end(); ++it)
    {
      Serial.print(it->key);
      Serial.print(":");
      Serial.println(it->value.asString());
    }
    
// Check correct AssetId       
    if (command_topic.containsKey("AssetId")) { // AssetId is required
      AssetId = command_topic["AssetId"];
    }
    else return;
          
// Main MQTT Command processing
    if ((strcmp(AssetId, hostString) == 0) || (strcmp(AssetId, "*") == 0)) { // Handle wildcard
      if (strcmp(topic, "COMMAND/") == 0) {
        if (command_topic.containsKey("Cmnd")) {  // Cmnd is required
          Command = command_topic["Cmnd"];
        }
        else return;

// Commands that do not require a Sensor ID
// ----------------------------------------
        if (strcmp(Command, "assets") == 0) {
          sendAllMQTTAssets();
          return;
        }
        if (strcmp(Command, "status") == 0) {
          sendMQTTStatus();
          return;
        }

// Commands that do require a Sensor ID
// ------------------------------------
        if (command_topic.containsKey("SId")) {     // SensorID is required
          SensorIdx = command_topic["SId"][0];      // Get SensorID
          Number = command_topic["SId"][1];         // Get pin or function #
        }
        else return;

        if (SensorIdx == SENSORID_DIO) {
          if (command_topic.containsKey("name")) {   // name - required
            if (!(strcmp(command_topic["name"], "DIO") == 0)) return;
          }
          else return;
            
          if (strcmp(Command, "dout") == 0) {
            if (command_topic.containsKey("data")) {  // Data - required
            data = command_topic["data"];
            }
            else return;          
            digitalWrite(Number, data);               // Set the digital pin
            return;
          }
          if (strcmp(Command, "din") == 0) {
            sendMQTTAsset(SensorIdx, Number);         // Publish digital data
            return;
          }
        }
        if (SensorIdx == SENSORID_AIO) {
          if (command_topic.containsKey("name")) {   // name - required
            if (!(strcmp(command_topic["name"], "AIO") == 0)) return;
          }
          else return;

          if (strcmp(Command, "aout") == 0) {
            if (command_topic.containsKey("data")) {  // Data - required
              data = command_topic["data"];
            }
            else return;          
            analogWrite(Number, data);              // Set the analog pin
            return;
          }
          if (strcmp(Command, "ain") == 0) {    
            sendMQTTAsset(SensorIdx, Number);       // Publish analog data
            return;
          }
        }

// Commands that execute a Sensor function
// ---------------------------------------
        if (SensorIdx == SENSORID_FN) {
          if ((Number >=0) && (Number < CUSTOM_FUNCTIONS)) {
            if (strcmp(Command, "fnout") == 0) {
              return;
            }
            if (strcmp(Command, "fnin") == 0) {
              sendMQTTAsset(SensorIdx, Number);       // Publish function data
            return;
            }
          }
          else return;
        }
      } // End (strcmp COMMAND/ topic
      
      if (strcmp(topic, "STATUS/QUERY") == 0) {
          sendMQTTStatus();
          return;
        }
      if (strcmp(topic, "ASSET/QUERY") == 0) {
          sendAllMQTTAssets();
          return;
        }
              
// Other topics go here
// ====================
      
    }   // end (strcmp AssetId
  }     // end Valid JSON object
}
