void setupTime()  {
  setSyncInterval(60);        // Set minimum seconds between re-sync via now() call
  setSyncProvider(RTC.get);   // Get the time from the RTC during operation
  epoch = getNtpTime();       // Get the time from ntp (if available)
  if (epoch != 0) {
    setTime(epoch);           // getNtpTime() returns 0 if no ntp server
    Serial.println("ntp has set the system time");
  }
  if(timeStatus() != timeSet) {   // Has the RTC been set?
     Serial.println("RTC not set and no ntp server !!");
     return;
  }
  Serial.println("RTC has the system time");          
}

void updateRTC(void) {
    setupTime();          // initialize RTC using ntp, if available
}

void digitalClockDisplay(){
  // digital clock display of the time
  Serial.print(hour());
  printDigits(minute());
  printDigits(second());
  Serial.print(" ");
  Serial.print(day());
  Serial.print(" ");
  Serial.print(month());
  Serial.print(" ");
  Serial.print(year()); 
  Serial.println(); 
}

void printDigits(int digits){
  // utility function for digital clock display: prints preceding colon and leading 0
  Serial.print(":");
  if(digits < 10)
    Serial.print('0');
  Serial.print(digits);
}

void flashLED(void) {
    digitalClockDisplay();
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
}

