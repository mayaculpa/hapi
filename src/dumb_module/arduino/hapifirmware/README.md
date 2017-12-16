# Installing PlatformIO

- Download and install [PlatformIO (VS-Code)](http://platformio.org/get-started/ide?install=vscode)
- After installing PlatformIO extension, go to *PIO Home* tab
- Click on *Open Project* and select the `hapi/src/dumb_module/arduino/hapifirmware` folder
- Compile by clicking the check mark at the bottom (tooltip *PlatformIO: Build*)
- Flash the ESP8266 (esp12e) by clicking the arrow to the right at the bottom (tooltip *PlatformIO: Upload*)

# WiFi
To define your wifi SSID and password, set the build_flags value in platformio.ini. An example would be:

    build_flags = '-DHAPI_SSID="MyWifiName"' '-DHAPI_PWD="MyWifiPassword"'
