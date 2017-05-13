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

void setupControls(void){
  int i;
  // Initialize 
}

boolean checkControls(void) {
  CFuncDef c;  
  for (int i=0;i<CONTROL_FUNCTIONS;i++) {
    c = HapicFunctions[i];                // initialize access structure
    c.oPtr(i);                            // call the check function
  }
}

float controlPumps(int Device){
  CFuncDef c;
  c = HapicFunctions[Device];
  if (HapicData[Device].hc_running) {           // is the pump running?
    if (HapicData[Device].hc_end > epoch) {     // Yes, should it be turned off?
      HapicData[Device].hc_running = false;
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 0);
      else digitalWrite(HapicData[Device].hc_controlpin, 1);      
      if (HapicData[Device].hc_repeat != 0) {   // Is repeat active?
        HapicData[Device].hc_start += HapicData[Device].hc_repeat;
        HapicData[Device].hc_end += HapicData[Device].hc_repeat;
      }
    }
    if (c.iPtr(Device) < HapicData[Device].hcs_offValue) { // is the TurnOff value exceeded?
      HapicData[Device].hc_running = false;
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 0);
      else digitalWrite(HapicData[Device].hc_controlpin, 1);    
    }    
  } else 
  {
    if (HapicData[Device].hc_start >= epoch) {       // Is the timeOn value exceeded?
      HapicData[Device].hc_running = true;        // Turn it On, Pump is now running
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 1);
      else digitalWrite(HapicData[Device].hc_controlpin, 0);
    }
    if (c.iPtr(Device) > HapicData[Device].hcs_onValue) { // Is the turnOn value exceeded?
      HapicData[Device].hc_running = true;        // Turn it On, Pump is now running
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 1);
      else digitalWrite(HapicData[Device].hc_controlpin, 0);
    }
  }
}

float controlLamps(int Device){
  CFuncDef c;
  c = HapicFunctions[Device];
  if (HapicData[Device].hc_running) {           // is the Lamp On?
    if (HapicData[Device].hc_end > epoch) {     // Yes, should it be turned off?
      HapicData[Device].hc_running = false;
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 0);
      else digitalWrite(HapicData[Device].hc_controlpin, 1);      
      if (HapicData[Device].hc_repeat != 0) {   // Is repeat active?
        HapicData[Device].hc_start += HapicData[Device].hc_repeat;
        HapicData[Device].hc_end += HapicData[Device].hc_repeat;
      }
    }
    if (c.iPtr(Device) < HapicData[Device].hcs_offValue) { // is the TurnOff value exceeded?
      HapicData[Device].hc_running = false;
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 0);
      else digitalWrite(HapicData[Device].hc_controlpin, 1);    
    }    
  } else 
  {
    if (HapicData[Device].hc_start >= epoch) {    // Is the timeOn value exceeded?
      HapicData[Device].hc_running = true;        // Turn it On, Lamp is now on
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 1);
      else digitalWrite(HapicData[Device].hc_controlpin, 0);
    }
    if (c.iPtr(Device) > HapicData[Device].hcs_onValue) { // Is the turnOn value exceeded?
      HapicData[Device].hc_running = true;                // Turn it On, Lamp is now on
      if (HapicData[Device].hc_polarity) digitalWrite(HapicData[Device].hc_controlpin, 1);
      else digitalWrite(HapicData[Device].hc_controlpin, 0);
    }
  }
}


