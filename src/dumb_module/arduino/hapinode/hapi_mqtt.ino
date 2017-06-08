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
  status_message[F("Node")] = HN_Id;
  // Returns the current status of the HN itself
  // Includes firmware version, MAC address, IP Address, Free RAM and Idle Mode
  status_message[F("FW")] = HAPI_FW_VERSION;
  status_message[F("time")] = currentTime;
  status_message[F("DIO")] = String(NUM_DIGITAL);
  status_message[F("AIO")] = String(NUM_ANALOG);
  status_message[F("Free SRAM")] = String(freeRam()) + F("k");
  status_message[F("Idle")] = idle_mode;

  status_message.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  strcpy(mqtt_topic, mqtt_topic_status);            // Generic status response topic
  strcat(mqtt_topic, hostString);                   // Add the NodeId

  Serial.print(mqtt_topic);
  Serial.print(F(" : "));
  Serial.println(MQTTOutput);

  // PUBLISH to the MQTT Broker
  if (MQTTClient.publish(mqtt_topic, MQTTOutput)) {
    return true;
  }
  // If the message failed to send, try again, as the connection may have broken.
  else {
    Serial.println(F("Status Message failed to publish. Reconnecting to MQTT Broker and trying again .. "));
    if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
      Serial.println(F("reconnected to MQTT Broker!"));
      delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
      if (MQTTClient.publish(mqtt_topic_status, MQTTOutput)) {
        Serial.println(F("Status Message published after one retry."));
        return true;
      }
      else {
        Serial.println(F("Status Message failed to publish after one retry."));
        return false;
      }
    }
    else {
      Serial.println(F("Connection to MQTT Broker failed..."));
      return false;
    }
  }
}

boolean sendAllMQTTAssets(void) {
  //Process digital pins
  for (int i = 0; i < NUM_DIGITAL; i++) {
    switch (pinControl[i]) {
    case DIGITAL_INPUT_PIN:
    case DIGITAL_INPUT_PULLUP_PIN:
    case DIGITAL_OUTPUT_PIN:
    case ANALOG_OUTPUT_PIN:
      while (!(sendMQTTAsset(SENSORID_DIO, i)))  // Until it is sent
        ;
      break;
    default:
      break;
    }
  }
  //Process analog pins
  for (int i = 0; i < NUM_ANALOG; i++) {
    while (!(sendMQTTAsset(SENSORID_AIO, i+NUM_DIGITAL)))  // Until it is sent
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
  strcat(mqtt_topic,F("/"));                           // /
  strcat(mqtt_topic,f.fName);                       // sensor name
  publishJSON(mqtt_topic);                          // Publish it

  Serial.print(mqtt_topic);
  Serial.print(F(" : "));
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
  asset_message[F("Node")] = HN_Id;

  // Assembles a message with values from pins and custom functions
  // Returns a JSON string

  asset_message[F("t")] = currentTime;                            // UTC time

  switch(AssetIdx) {
  case SENSORID_DIO:
    asset_message[F("Asset")] =  F("DIO");            // Asset ID
    asset_message[F("ctxt")] =  F("PIN");             // Context
    asset_message[F("unit")] =  F("");                // Units of measurement
    pinValue = digitalRead(Number);
    asset_message[F("data")] = pinValue;           // Data
    break;
  case SENSORID_AIO:
    asset_message[F("Asset")] =  F("AIO");
    asset_message[F("ctxt")] =  F("PIN");
    asset_message[F("unit")] =  F("");
    pinValue = analogRead(Number);
    asset_message[F("data")] = pinValue;
    break;
  case SENSORID_FN:
    f = HapisFunctions[Number];
    asset_message[F("Asset")] =  (String)f.fName;
    asset_message[F("ctxt")] =  (String)f.fType;
    asset_message[F("unit")] =  (String)f.fUnit;
    funcVal = f.fPtr(Number);
    asset_message[F("data")] =  funcVal;     // Two decimal points
    break;
  case CONTROLID_FN:
    c = HapicFunctions[Number];
    asset_message[F("Asset")] =  (String)c.fName;
    asset_message[F("ctxt")] =  (String)c.fType;
    asset_message[F("unit")] =  (String)c.fUnit;
    funcVal = c.iPtr(Number);
    asset_message[F("data")] =  funcVal;     // Two decimal points
    break;
  case CONTROLDATA1_FN:
    asset_message[F("Asset")] =  (String)d.hc_name;
    asset_message[F("pol")] =  (boolean)d.hc_polarity;
    asset_message[F("stt")] =  (unsigned long )d.hc_start;
    asset_message[F("end")] =  (unsigned long)d.hc_end;
    asset_message[F("rpt")] =  (unsigned long)d.hc_repeat;
    break;
  case CONTROLDATA2_FN:
    asset_message[F("Asset")] =  (String)d.hc_name;
    asset_message[F("von")] =  (float)d.hcs_onValue;
    asset_message[F("voff")] =  (float)d.hcs_offValue;
    break;

  default:
    break;
  }
  asset_message.printTo(MQTTOutput, 128);          // MQTT JSON string is max 96 bytes
  Serial.println(MQTTOutput);
}

boolean publishJSON(const char* topic) {
  // PUBLISH to the MQTT Broker
  if (MQTTClient.publish(topic, MQTTOutput))
    return true;

  // If the message failed to send, try again, as the connection may have broken.
  Serial.println(F("Send Message failed. Reconnecting to MQTT Broker and trying again .. "));
  if (MQTTClient.connect(clientID, MQTT_broker_username, MQTT_broker_password)) {
    Serial.println(F("reconnected to MQTT Broker!"));
    delay(100); // This delay ensures that client.publish doesn't clash with the client.connect call
    if (MQTTClient.publish(topic, MQTTOutput)) {
      return true;
    }
    else {
      Serial.println(F("Send Message failed after one retry."));
      return false;
    }
  }
  else {
    Serial.println(F("Connection to MQTT Broker failed..."));
    return false;
  }
}

void MQTTcallback(char* topic, byte* payload, unsigned int length) {
  int i;
  const char* Node = F("*");     // NodeId for target HAPInode, preset for anyone
  const char* Command = F(" ");  // Command to execute
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
  for (i = 0; i < length; i++) {
    MQTTInput[i] = (char)payload[i];
    Serial.print(MQTTInput[i]);
  }
  MQTTInput[i] = 0x00;                  // Null terminate buffer to use string functions
  Serial.println();

  //Parse the topic data
  JsonObject& command_topic = hn_topic_command.parseObject(MQTTInput);
  if (!command_topic.success())
    return;

  Serial.println(F("Parsing .. "));
  for (JsonObject::iterator it=command_topic.begin(); it!=command_topic.end(); ++it) {
    Serial.print(it->key);
    Serial.print(F(":"));
    Serial.println(it->value.as<char*>());
  }

  Serial.print(F("Node - "));
  Serial.println(Node);
// Check correct Node ID
  if (command_topic.containsKey(F("Node"))) { // NodeId is required for all messages, even if it is F("*")
    Node = command_topic[F("Node")];
  }
//    else return;

// Check for COMMAND/ topic based commands
// =======================================
  if ((strcmp(Node, hostString) == 0) || (strcmp(Node, F("*")) == 0)) { // Handle wildcard
    if (strcmp(topic, mqtt_topic_command) == 0) {
      if (command_topic.containsKey(F("Cmnd"))) {  // Cmnd is required
        Command = command_topic[F("Cmnd")];
      }
      else return;

// Commands that do not require an Asset ID
// ----------------------------------------
      if (strcmp(Command, F("assets")) == 0) {
        succeed = sendAllMQTTAssets();
        return;
      }
      if (strcmp(Command, F("status")) == 0) {
        sendMQTTStatus();
        return;
      }

// Commands that do require an Asset ID
// ------------------------------------
      if (!command_topic.containsKey(F("Asset"))) // AssetID is required
        return;

      Serial.println(F("Processing Asset"));
// Digital IO
      if (strcmp(command_topic[F("Asset")], F("DIO")) == 0) { // Digital IO
        if (command_topic.containsKey(F("pin"))) {   // pin - required
          Number = command_topic[F("pin")];
        }
        else return;
        if (strcmp(Command, F("din")) == 0) {
          AssetIdx = SENSORID_DIO;
          sendMQTTAsset(AssetIdx, Number);         // Publish digital data
          return;
        }
        if (strcmp(Command, F("dout")) == 0) {
          if (command_topic.containsKey(F("data"))) {  // Data - required
            data = command_topic[F("data")];
          }
          else return;
          digitalWrite(Number, data);               // Set the digital pin
          return;
        }
      }
      Serial.println(F(" .. not DIO"));

// Analog IO
      if (strcmp(command_topic[F("Asset")], F("AIO")) == 0) { // Analog IO
        if (command_topic.containsKey(F("pin"))) {   // pin - required
          Number = command_topic[F("pin")];
        }
        else return;
        if (strcmp(Command, F("ain")) == 0) {
          AssetIdx = SENSORID_AIO;
          sendMQTTAsset(AssetIdx, Number);         // Publish analog data
          return;
        }
        if (strcmp(Command, F("aout")) == 0) {
          if (command_topic.containsKey(F("data"))) {  // Data - required
            data = command_topic[F("data")];
          }
          else return;
#ifndef HN_ESP32
          analogWrite(Number, data);               // Set the analog pin
#endif
          return;
        }
      }
      Serial.println(F(" .. not AIO"));

      // Function IO
      Number = INVALID_VALUE;
      AssetIdx = SENSORID_FN;                    // Asset Function IO
      for (int i=0;i < ArrayLength(HapisFunctions);i++) {    // Scan for a match on the sensor name
        f = HapisFunctions[i];                    // Point to Asset read function structure
        if (strcmp(command_topic[F("Asset")],f.fName) == 0) {  // Asset match?
          Number = i;                             // Match for Sensor name
        }
      }
      if (Number != INVALID_VALUE) { //^^^ need to get away from this style
        sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
        return;
      }
      Serial.println(F(" .. not Sensor Read"));
      AssetIdx = CONTROLID_FN;                 // Control Function IO
      for (int i=0;i < ArrayLength(HapicFunctions);i++) { // Scan for a match on the control name
        c = HapicFunctions[i];                  // Point to control function structure
        if (strcmp(command_topic[F("Asset")],c.fName) == 0) {  // Asset match?
          Number = i;                           // Match for control name
        }
      }
      if (Number != INVALID_VALUE) { // If we have a match on the name //^^^ need to get away from this style
        if (strcmp(Command, F("fnin")) == 0) {
          sendMQTTAsset(AssetIdx, Number);       // Publish sensor or control function data
          return;
        }
        if (strcmp(Command, F("fnout")) == 0) {      // Function out only works for controls
          c = HapicFunctions[Number];             // Point to control output function structure
          // Control
          if (command_topic.containsKey(F("pol"))) {  // Polarity ( boolean)
            HapicData[Number].hc_polarity = command_topic[F("pol")];
          }
          if (command_topic.containsKey(F("stt"))) {  // Start time (unix secs)
            Serial.println(F("writing stt"));
            HapicData[Number].hc_start = command_topic[F("stt")];
          }
          if (command_topic.containsKey(F("end"))) {  // End time (unix secs)
            HapicData[Number].hc_end = command_topic[F("end")];
          }
          if (command_topic.containsKey(F("rpt"))) {  // Repeat time (s)
            HapicData[Number].hc_repeat = command_topic[F("rpt")];
          }
          // Associated sensor
          if (command_topic.containsKey(F("von"))) {  // Value to turn on
            HapicData[Number].hcs_onValue = command_topic[F("von")];
          }
          if (command_topic.containsKey(F("voff"))) {  // Value to turn off
            HapicData[Number].hcs_offValue = command_topic[F("voff")];
          }
        }
        return;
      }
      Serial.println(F(" .. not Control I/O"));
    } // End (strcmp COMMAND/ topic

    Serial.println(F(" .. not COMMAND/"));

// Check for CONFIG/ only topic values
// ===================================
    if (strcmp(topic, mqtt_topic_config) == 0) {
      if (command_topic.containsKey(F("timeZone"))) {  // Time Zone ?
        timeZone = command_topic[F("timeZone")];
      }
      else return;
    }
    Serial.println(F(" .. not CONFIG/"));

// STATUS topics
// =============
    Serial.print(F("Checking .. "));
    Serial.println(topic);

    strcpy(hn_topic,mqtt_topic_array[STATUSSTART]);     // Status query, any NodeId
    if (strcmp(topic, hn_topic) == 0) {
      sendMQTTStatus();
      return;
    }
    Serial.print(F(" .. not "));
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
      Serial.print(F(" .. not "));
      Serial.println(hn_topic);
    }

// Handle sensors
    AssetIdx = SENSORID_FN;                    // Sensor Function IO
    Number = INVALID_VALUE;
    for (int i=0;i < ArrayLength(HapisFunctions);i++) {    // Scan for a match on the sensor name
      f = HapisFunctions[i];                    // Point to sensor read function structure
      strcpy(hn_topic,mqtt_topic_array[ASSETSTART+1]);     // Set base topic for a specific asset query
      strcat(hn_topic,hostString);              // NodeId next
      strcat(hn_topic,F("/"));                     //  .. MQTT separator
      strcat(hn_topic, f.fName);                //  .. and the sensor name
      if (strcmp(topic, hn_topic) == 0) {         // Asset match?
        Number = i;                             // Match for Sensor name
      }
    }
    if (Number != INVALID_VALUE) { //^^^ need to get rid of this style of test
      sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
      return;                                   //  and exit
    }
    Serial.print(F(" .. not "));
    Serial.println(hn_topic);
// Handle Controls
    AssetIdx = CONTROLID_FN;                   // Control Function IO
    for (int i=0;i < ArrayLength(HapicFunctions);i++) {   // Scan for a match on the control name
      c = HapicFunctions[i];                    // Point to control function structure
      strcpy(hn_topic,mqtt_topic_array[1]);     // Set base topic for an asset query
      strcat(hn_topic,hostString);              // NodeId next
      strcat(hn_topic,F("/"));                     //  .. MQTT separator
      strcat(hn_topic, c.fName);                //  .. and the control name
      if (strcmp(topic, hn_topic) == 0) {         // Asset match?
        Number = i;                             // Match for Sensor name
      }
    }
    if (Number != INVALID_VALUE) {
      sendMQTTAsset(AssetIdx, Number);         // Publish sensor or control function data
      return;                                   //  and exit
    }
    Serial.print(F(" .. not "));
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
      strcat(hn_topic,F("/"));                     //  .. MQTT separator
      strcat(hn_topic, c.fName);                //  .. and the sensor name
      if (strcmp(topic, hn_topic) == 0) {       // Asset match?
        Number = i;                             // Match for Sensor name
      }
    }
    if (Number != INVALID_VALUE) {
      c = HapicFunctions[Number];             // Point to control output function structure
// Control
      if (command_topic.containsKey(F("pol"))) {  // Polarity ( boolean)
        HapicData[Number].hc_polarity = command_topic[F("pol")];
      }
      if (command_topic.containsKey(F("stt"))) {  // Start time (unix secs)
        HapicData[Number].hc_start = command_topic[F("stt")];
      }
      if (command_topic.containsKey(F("end"))) {  // End time (unix secs)
        HapicData[Number].hc_end = command_topic[F("end")];
      }
      if (command_topic.containsKey(F("rpt"))) {  // Repeat time (s)
        HapicData[Number].hc_repeat = command_topic[F("rpt")];
      }
// Associated sensor
      if (command_topic.containsKey(F("von"))) {  // Value to turn on
        HapicData[Number].hcs_onValue = command_topic[F("von")];
      }
      if (command_topic.containsKey(F("voff"))) {  // Value to turn off
        HapicData[Number].hcs_offValue = command_topic[F("voff")];
      }
      return;
    }
    Serial.print(F(" .. not "));
    Serial.println(hn_topic);

// Other topics go here
// ====================

  }   // end strcmp NodeId
}
