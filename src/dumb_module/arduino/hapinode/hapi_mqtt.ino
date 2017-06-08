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
  status_message["Node"] = HN_Id;
  // Returns the current status of the HN itself
  // Includes firmware version, MAC address, IP Address, Free RAM and Idle Mode
  status_message["FW"] = HAPI_FW_VERSION;
  status_message["time"] = currentTime;
  status_message["DIO"] = String(NUM_DIGITAL);
  status_message["AIO"] = String(NUM_ANALOG);
  status_message["Free SRAM"] = String(freeRam()) + "k";
  status_message["Idle"] = idle_mode;

  status_message.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  strcpy(mqtt_topic, mqtt_topic_status);            // Generic status response topic
  strcat(mqtt_topic, hostString);                   // Add the NodeId

  Serial.print(mqtt_topic);
  Serial.print(" : ");
  Serial.println(MQTTOutput);

  // PUBLISH to the MQTT Broker
  if (MQTTClient.publish(mqtt_topic, MQTTOutput)) {
    return true;
  }
  // If the message failed to send, try again, as the connection may have broken.
  else {
    Serial.println("Status Message failed to publish. Reconnecting to MQTT Broker and trying again .. ");
    if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
      Serial.println("reconnected to MQTT Broker!");
      delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
      if (MQTTClient.publish(mqtt_topic_status, MQTTOutput)) {
        Serial.println("Status Message published after one retry.");
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
  for (int i = 0; i < NUM_DIGITAL; i++) {
    if (0 < pinControl[i] && pinControl[i] < 5) {
      while (!(sendMQTTAsset(SENSORID_DIO, i)))  // Until it is sent
        ;
    }
  }
  //Process analog pins
  for (int x = 0; x < NUM_ANALOG; x++) {
    while (!(sendMQTTAsset(SENSORID_AIO, x+NUM_DIGITAL)))  // Until it is sent
      ;
  }
  // Process Custom Functions
  for (int i = 0; i < ArrayLength(HapisFunctions); i++) {
    while (!(sendMQTTAsset(SENSORID_FN, i)))  // Until it is sent
      ;
  }
  // Process Custom Functions
  for (int i = 0; i < ArrayLength(HapicFunctions); i++) {
    while (!(sendMQTTAsset(CONTROLID_FN, i)))  // Until it is sent
      ;
  }
  // Process Custom Functions
  for (int i = 0; i < ArrayLength(HapicFunctions); i++) {
    while (!(sendMQTTAsset(CONTROLDATA1_FN, i)))  // Until it is sent
      ;
  }
  // Process Custom Functions
  for (int i = 0; i < ArrayLength(HapicFunctions); i++) {
    while (!(sendMQTTAsset(CONTROLDATA2_FN, i)))  // Until it is sent
      ;
  }
  return true;
}

boolean sendMQTTAsset(int AssetIdx, int Number) {
  FuncDef f = HapisFunctions[Number];               // Pointer to current sensor
  createAssetJSON(AssetIdx, Number);                // (Store result in MQTTOutput)
  strcpy(mqtt_topic, mqtt_topic_asset);             // Generic asset response topic
  strcat(mqtt_topic, hostString);                   // Add the NodeId
  strcat(mqtt_topic,"/");                           // /
  strcat(mqtt_topic,f.fName);                       // sensor name
  publishJSON(mqtt_topic);                          // Publish it

  Serial.print(mqtt_topic);
  Serial.print(" : ");
  Serial.println(MQTTOutput);
}

boolean sendMQTTException(int AssetIdx, int Number) {
  createAssetJSON(AssetIdx, Number);
  publishJSON(mqtt_topic_exception);
}

boolean createAssetJSON(int AssetIdx, int Number) {
  //For custom functions
  FuncDef f = HapisFunctions[Number];
  CFuncDef c = HapicFunctions[Number];
  ControlData d = HapicData[Number];
  int pinValue;
  float funcVal = -9.99;
  StaticJsonBuffer<256> hn_asset;                   // Asset data for this HN
  JsonObject& asset_message = hn_asset.createObject();

// Set the NodeId
  asset_message["Node"] = HN_Id;

  // Assembles a message with values from pins and custom functions
  // Returns a JSON string

  asset_message["t"] = currentTime;                            // UTC time

  switch(AssetIdx) {
    case SENSORID_DIO:
      asset_message["Asset"] =  "DIO";            // Asset ID
      asset_message["ctxt"] =  "PIN";             // Context
      asset_message["unit"] =  "";                // Units of measurement
      pinValue = digitalRead(Number);
      asset_message["data"] = pinValue;           // Data
      break;
    case SENSORID_AIO:
      asset_message["Asset"] =  "AIO";
      asset_message["ctxt"] =  "PIN";
      asset_message["unit"] =  "";
      pinValue = analogRead(Number);
      asset_message["data"] = pinValue;
      break;
    case SENSORID_FN:
      f = HapisFunctions[Number];
      asset_message["Asset"] =  (String)f.fName;
      asset_message["ctxt"] =  (String)f.fType;
      asset_message["unit"] =  (String)f.fUnit;
      funcVal = f.fPtr(Number);
      asset_message["data"] =  funcVal;     // Two decimal points
      break;
    case CONTROLID_FN:
      c = HapicFunctions[Number];
      asset_message["Asset"] =  (String)c.fName;
      asset_message["ctxt"] =  (String)c.fType;
      asset_message["unit"] =  (String)c.fUnit;
      funcVal = c.iPtr(Number);
      asset_message["data"] =  funcVal;     // Two decimal points
      break;
    case CONTROLDATA1_FN:
      asset_message["Asset"] =  (String)d.hc_name;
      asset_message["pol"] =  (boolean)d.hc_polarity;
      asset_message["stt"] =  (unsigned long )d.hc_start;
      asset_message["end"] =  (unsigned long)d.hc_end;
      asset_message["rpt"] =  (unsigned long)d.hc_repeat;
      break;
    case CONTROLDATA2_FN:
      asset_message["Asset"] =  (String)d.hc_name;
      asset_message["von"] =  (float)d.hcs_onValue;
      asset_message["voff"] =  (float)d.hcs_offValue;
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
  const char* Node = "*";     // NodeId for target HAPInode, preset for anyone
  const char* Command = " ";  // Command to execute
  char* hn_topic;             // Variable to hold all node topics
  FuncDef f;                  // Read Data Functions
  CFuncDef c;                 // Control functions
  ControlData cd;             // Data for control functions
  int AssetIdx;              // Target Sensor Index
  int Number;                 // Target pin# or function#
  int data;                   // Data for output
  boolean succeed;

  hn_topic = &MQTTOutput[0];
  StaticJsonBuffer<200> hn_topic_command;            // Parsing buffer

  Serial.println(topic);
// Copy topic to char* buffer
  for(i = 0; i < length; i++){
    MQTTInput[i] = (char)payload[i];
    Serial.print(MQTTInput[i]);
  }
  MQTTInput[i] = 0x00;                  // Null terminate buffer to use string functions
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
      Serial.println(it->value.as<char*>());
    }

    Serial.print("Node - ");
    Serial.println(Node);
// Check correct Node ID
    if (command_topic.containsKey("Node")) { // NodeId is required for all messages, even if it is "*"
      Node = command_topic["Node"];
    }
//    else return;

// Check for COMMAND/ topic based commands
// =======================================
    if ((strcmp(Node, hostString) == 0) || (strcmp(Node, "*") == 0)) { // Handle wildcard
      if (strcmp(topic, mqtt_topic_command) == 0) {
        if (command_topic.containsKey("Cmnd")) {  // Cmnd is required
          Command = command_topic["Cmnd"];
        }
        else return;

// Commands that do not require an Asset ID
// ----------------------------------------
        if (strcmp(Command, "assets") == 0) {
          succeed = sendAllMQTTAssets();
          return;
        }
        if (strcmp(Command, "status") == 0) {
          sendMQTTStatus();
          return;
        }

// Commands that do require an Asset ID
// ------------------------------------
        if (command_topic.containsKey("Asset")) {     // AssetID is required
          Serial.println("Processing Asset");
// Digital IO
          if (strcmp(command_topic["Asset"], "DIO") == 0) { // Digital IO
            if (command_topic.containsKey("pin")) {   // pin - required
              Number = command_topic["pin"];
            }
            else return;
            if (strcmp(Command, "din") == 0) {
              AssetIdx = SENSORID_DIO;
              sendMQTTAsset(AssetIdx, Number);         // Publish digital data
              return;
            }
            if (strcmp(Command, "dout") == 0) {
              if (command_topic.containsKey("data")) {  // Data - required
                data = command_topic["data"];
              }
              else return;
              digitalWrite(Number, data);               // Set the digital pin
              return;
            }
          }
          Serial.println(" .. not DIO");

// Analog IO
          if (strcmp(command_topic["Asset"], "AIO") == 0) { // Analog IO
            if (command_topic.containsKey("pin")) {   // pin - required
              Number = command_topic["pin"];
            }
            else return;
            if (strcmp(Command, "ain") == 0) {
              AssetIdx = SENSORID_AIO;
              sendMQTTAsset(AssetIdx, Number);         // Publish analog data
              return;
            }
            if (strcmp(Command, "aout") == 0) {
              if (command_topic.containsKey("data")) {  // Data - required
                data = command_topic["data"];
              }
              else return;
#ifndef HN_ESP32
              analogWrite(Number, data);               // Set the analog pin
#endif
              return;
            }
          }
          Serial.println(" .. not AIO");

// Function IO
          Number = INVALID_VALUE;
          AssetIdx = SENSORID_FN;                    // Asset Function IO
          for (int i=0;i < ArrayLength(HapisFunctions);i++) {    // Scan for a match on the sensor name
            f = HapisFunctions[i];                    // Point to Asset read function structure
            if (strcmp(command_topic["Asset"],f.fName) == 0) {  // Asset match?
              Number = i;                             // Match for Sensor name
            }
          }
          if (Number != INVALID_VALUE) { //^^^ need to get away from this style
            sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
            return;
          }
          else {                                      // Did not find a sensor, so try controls
            Serial.println(" .. not Sensor Read");
            AssetIdx = CONTROLID_FN;                 // Control Function IO
            for (int i=0;i < ArrayLength(HapicFunctions);i++) { // Scan for a match on the control name
              c = HapicFunctions[i];                  // Point to control function structure
              if (strcmp(command_topic["Asset"],c.fName) == 0) {  // Asset match?
                Number = i;                           // Match for control name
              }
            }
          }
          if (Number != INVALID_VALUE) {             // If we have a match on the name
            if (strcmp(Command, "fnin") == 0) {
              sendMQTTAsset(AssetIdx, Number);       // Publish sensor or control function data
            return;
            }
            if (strcmp(Command, "fnout") == 0) {      // Function out only works for controls
              c = HapicFunctions[Number];             // Point to control output function structure
// Control
              if (command_topic.containsKey("pol")) {  // Polarity ( boolean)
                HapicData[Number].hc_polarity = command_topic["pol"];
              }
              if (command_topic.containsKey("stt")) {  // Start time (unix secs)
                Serial.println("writing stt");
                HapicData[Number].hc_start = command_topic["stt"];
              }
              if (command_topic.containsKey("end")) {  // End time (unix secs)
                HapicData[Number].hc_end = command_topic["end"];
              }
              if (command_topic.containsKey("rpt")) {  // Repeat time (s)
                HapicData[Number].hc_repeat = command_topic["rpt"];
              }
// Associated sensor
              if (command_topic.containsKey("von")) {  // Value to turn on
                HapicData[Number].hcs_onValue = command_topic["von"];
              }
              if (command_topic.containsKey("voff")) {  // Value to turn off
                HapicData[Number].hcs_offValue = command_topic["voff"];
              }
              return;
            }
            else return;         // Found a valid control name but no valid command or data
          }
          Serial.println(" .. not Control I/O");
        } // Command topic contains a SensorId
        else return;
      } // End (strcmp COMMAND/ topic

      Serial.println(" .. not COMMAND/");

// Check for CONFIG/ only topic values
// ===================================
      if (strcmp(topic, mqtt_topic_config) == 0) {
        if (command_topic.containsKey("timeZone")) {  // Time Zone ?
          timeZone = command_topic["timeZone"];
        }
        else return;
      }
      Serial.println(" .. not CONFIG/");

// STATUS topics
// =============
      Serial.print("Checking .. ");
      Serial.println(topic);

      strcpy(hn_topic,mqtt_topic_array[STATUSSTART]);     // Status query, any NodeId
      if (strcmp(topic, hn_topic) == 0) {
        sendMQTTStatus();
        return;
      }
      Serial.print(" .. not ");
      Serial.println(hn_topic);

// ASSET topics
// ============
// Handle wildcards
      Serial.println(mqtt_topic_array[ASSETSTART]);   // Assets start
      for (int i=1;i < CONFIGSTART;i++) {             // Wildcard topics
        strcpy(hn_topic,mqtt_topic_array[i]);         // Asset query, any NodeId
        if (strcmp(topic, hn_topic) == 0) {
            sendAllMQTTAssets();
            return;
        }
        Serial.print(" .. not ");
        Serial.println(hn_topic);
      }

// Handle sensors
      AssetIdx = SENSORID_FN;                    // Sensor Function IO
      Number = INVALID_VALUE;
      for (int i=0;i < ArrayLength(HapisFunctions);i++) {    // Scan for a match on the sensor name
        f = HapisFunctions[i];                    // Point to sensor read function structure
        strcpy(hn_topic,mqtt_topic_array[ASSETSTART+1]);     // Set base topic for a specific asset query
        strcat(hn_topic,hostString);              // NodeId next
        strcat(hn_topic,"/");                     //  .. MQTT separator
        strcat(hn_topic, f.fName);                //  .. and the sensor name
        if (strcmp(topic, hn_topic) == 0) {         // Asset match?
          Number = i;                             // Match for Sensor name
        }
      }
      if (Number != INVALID_VALUE) {
        sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
        return;                                   //  and exit
      }
      Serial.print(" .. not ");
      Serial.println(hn_topic);
// Handle Controls
      AssetIdx = CONTROLID_FN;                   // Control Function IO
      for (int i=0;i < ArrayLength(HapicFunctions);i++) {   // Scan for a match on the control name
        c = HapicFunctions[i];                    // Point to control function structure
        strcpy(hn_topic,mqtt_topic_array[1]);     // Set base topic for an asset query
        strcat(hn_topic,hostString);              // NodeId next
        strcat(hn_topic,"/");                     //  .. MQTT separator
        strcat(hn_topic, c.fName);                //  .. and the control name
        if (strcmp(topic, hn_topic) == 0) {         // Asset match?
          Number = i;                             // Match for Sensor name
        }
      }
      if (Number != INVALID_VALUE) {
        sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
        return;                                   //  and exit
      }
      Serial.print(" .. not ");
      Serial.println(hn_topic);

// CONFIG topic
// ============
// Wildcards are not allowed in CONFIG
// It must have a valid NodeId, Asset and data to work
      Number = INVALID_VALUE;
      for (int i=0;i < ArrayLength(HapicFunctions);i++) {     // Scan for a match on the control name
        c = HapicFunctions[i];                    // Point to control function structure
        strcpy(hn_topic,mqtt_topic_array[CONFIGSTART]);       // Set base topic for a specific asset query
        strcat(hn_topic,hostString);              // NodeId next
        strcat(hn_topic,"/");                     //  .. MQTT separator
        strcat(hn_topic, c.fName);                //  .. and the sensor name
        if (strcmp(topic, hn_topic) == 0) {       // Asset match?
          Number = i;                             // Match for Sensor name
        }
      }
      if (Number != INVALID_VALUE) {
        c = HapicFunctions[Number];             // Point to control output function structure
// Control
        if (command_topic.containsKey("pol")) {  // Polarity ( boolean)
          HapicData[Number].hc_polarity = command_topic["pol"];
        }
        if (command_topic.containsKey("stt")) {  // Start time (unix secs)
          HapicData[Number].hc_start = command_topic["stt"];
        }
        if (command_topic.containsKey("end")) {  // End time (unix secs)
          HapicData[Number].hc_end = command_topic["end"];
        }
        if (command_topic.containsKey("rpt")) {  // Repeat time (s)
          HapicData[Number].hc_repeat = command_topic["rpt"];
        }
// Associated sensor
        if (command_topic.containsKey("von")) {  // Value to turn on
          HapicData[Number].hcs_onValue = command_topic["von"];
        }
        if (command_topic.containsKey("voff")) {  // Value to turn off
          HapicData[Number].hcs_offValue = command_topic["voff"];
        }
        return;
    }
      Serial.print(" .. not ");
      Serial.println(hn_topic);

// Other topics go here
// ====================

    }   // end strcmp NodeId
  }     // end Valid JSON object
}
