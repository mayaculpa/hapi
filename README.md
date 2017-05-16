![HAPI Project](/readme/hapi.png?raw=true "HAPI Project")

# Zero-footprint Autonomous Food Production

# Under heavy development
We're currently under heavy development.
We would love to have you participate! Drop us a note and we'll add you into our product development Slack server so you can keep up with the latest.

# Requirements
The default developing platform is Raspbian, a GNU/Linux Distribution for Raspberry Pi.
We can't provide any further information about other distributions, but we strongly believe it won't be a problem to run as long as you have all the requirements.
Note: we can say that Linux Mint and Arch Linux was used to run some tests, though.

## *Development Requirements*
### **Smart Module**
1. Python influxdb:
    ```pip install influxdb```
2. Python schedule:
    ```pip install schedule```
3. Python zeroconf:
    ```pip install zeroconf```
4. Python psutil:
    ```pip install psutil```
5. Python SDL_DS3231:
    ![SDL_DS3231 module](about:blank)
6. Python RPi.GPIO:
    ![RPi module](about:blank)

You might also considering using a Virtual Environment for testing.

**Note**: the system will try to import all the necessary sensor modules to run. If it can't, then the system will automatically run on "mock" mode.
If you are facing any troubles to get it running, drop us a message or open an issue.

### *System Configuration*
Note: Soon we'll introduce configuration via regular file and/or database. For now all configuration are hardcoded.
The system needs the following packages installed and properly configured:
1. **Avahi** (daemon) configured to publish MQTT service:
Here is an example. ![avahi-example](/readme/avahi-example)
Note: it must be off by default (systemctl stop avahi-daemon.service or similar).
2. **MQTT Mosquitto** with default configuration:
Here is an example. ![mosquitto-example](/readme/mosquitto-example)
3. **Influxdb** with default configuration:
4. **Grafana** [Optional] (highly recommended)

### *Usage:*
```python smart_module.py```

You should get something as this:
INSERT IMAGE HERE.

### Node (HAPInode)
**Soon.**

## HAPI
http://hapihq.com/

## Wiki Page
Don't forget to check our Wiki Page.
Note: we're currently redefining a few things. You might want to check it again later.
![HAPI Wiki Page](/../../wiki "Wiki Page")

## Our purpose
Develop a suite of tools that will allow people to grow a variety of food in diverse environments. Our primary focus is on building intelligent automation for hydroponics and aquaponics.
Imagine systems in your garage, basement or local community center that can churn out strawberries and kale, year-round with minimal expertise, expense and effort.
That’s what we’re shooting for.

However, people live in diverse locations and are faced with different resource constraints. For instance, access to clean water could be a challenge in Ghana whereas access to energy could be a challenge in Greenland.
So alongside the automation platform, we’re also developing equipment to help people overcome those challenges. The multi-stage water filter and the solar thermal air heater are results of this effort.

## Open Source
HAPI is an open project, meaning anyone and everyone can participate to the best of their ability.
While many aspects of the project are highly technical, there are also areas where non-technical expertise is needed.

If you would like to see what’s going on and what cool stuff we’ll be working on next, contact us.

## Contact
If you have any question or sugestion, you can contact us through the link below.
http://hapihq.com/contact-us-2/

However if you have found any problem or just want to make a suggestion, please check the Issue page.

## System Overview
![System Overview of the HAPI Project](/readme/system-overview.png?raw=true "HAPI Project System Overview")
Please note: we're currently working on the system design. Some changes on this image will probably be necessary in the near future.
