#ifndef HAPI_TIME_H
#define HAPI_TIME_H

class HapiTime {
public:
  static void setupTime();
  static void updateRTC();
  static void digitalClockDisplay();
  static void printDigits(int digits);
  static void flashLED(void);
};

#endif // HAPI_TIME_H
