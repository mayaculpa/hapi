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
1. Python influxdb: ```pip install influxdb```
2. Python schedule: ```pip install schedule```
3. Python zeroconf: ```pip install zeroconf```
4. Python psutil: ```pip install psutil```
5. Python Paho-MQTT: ```pip install paho-mqtt```
6. Python SDL_DS3231: ![SDL_DS3231 module](https://github.com/switchdoclabs/RTC_SDL_DS3231)
7. Python RPi.GPIO: ![RPi module](about:blank)

You might also considering using a Virtual Environment for testing.

**Note**: the system will try to import all the necessary sensor modules to run. If it can't, then the system will automatically run on "mock" mode.
If you are facing any troubles to get it running, drop us a message or open an issue.

### *System Configuration*
Note: Soon we'll introduce configuration via regular file and/or database. For now all configuration are hardcoded.
The system needs the following packages installed and properly configured:

1. **Avahi** (daemon) configured to publish MQTT service.

   Here is an example. ![avahi-example](/readme/avahi-example)

   Note: it must be off by default (systemctl stop avahi-daemon.service or similar).
2. **MQTT Mosquitto** with default configuration.

   Here is an example. ![mosquitto-example](/readme/mosquitto-example)
3. **Influxdb** with default configuration.
4. **Grafana** [Optional] (highly recommended).

### *Usage:*
```python smart_module.py```

**You should get something as this:**

    $ python smart_module.py
    2017-05-15 22:37:55.089210 - communicator.log - INFO - Communicator initialized
    Mock Smart Module hosting asset  HSM-WT123-MOCK wt Environment
    2017-05-15 22:37:55.091207 - smartmodule.log - INFO - Performing Discovery...
    2017-05-15 22:37:55.091782 - smartmodule.log - INFO - Waiting Broker information on attempt: 1.
    2017-05-15 22:37:56.092877 - smartmodule.log - INFO - MQTT Broker: ArchMain.local. IP: 192.168.0.99.
    2017-05-15 22:37:56.093225 - communicator.log - INFO - Connecting to ArchMain.local. at 192.168.0.99.
    2017-05-15 22:37:57.094778 - communicator.log - INFO - Connected with result code 0
    $SYS/broker/clients/total 0
    $SYS/broker/clients/total 1
    2017-05-15 22:38:02.648088 - smartmodule.log - INFO - No Scheduler found. Becoming the Scheduler.
    2017-05-15 22:38:02.648342 - scheduler.log - INFO - Loading Schedule Data...
    2017-05-15 22:38:02.648997 - scheduler.log - INFO - Schedule Data Loaded.
    2017-05-15 22:38:02.649105 - scheduler.log - INFO -   Loading seconds job: System Status.
    2017-05-15 22:38:02.649160 - scheduler.log - INFO -   Loading seconds job: Check Alert.
    2017-05-15 22:38:02.649627 - smartmodule.log - INFO - Scheduler program loaded.
    2017-05-15 22:38:02.650200 - smartmodule.log - INFO - Site data loaded.
    Running command self.smart_module.on_query_status()
    Running command self.smart_module.on_check_alert()
    STATUS/QUERY I might need to know how you are!
    ASSET/QUERY/HSM-WT123-MOCK Is it warm here?
    STATUS/RESPONSE [{'memory': {'cached': 913498112, 'used': 2294038528, 'free': 533913600}, 'disk': {'total': 52472872960, 'free': 36725215232, 'used': 13051768832}, 'network': {'packet_recv': 558630, 'packet_sent': 601295}, 'time': 1494898693.364454, 'hostname': 'ArchMain', 'boot': '2017-05-15 17:09:17', 'cpu': {'percentage': 3.2}, 'clients': 1}]
    ASSET/RESPONSE/HSM-WT123-MOCK 8.0
    2017-05-15 22:38:13.892977 - alert.log - INFO - Fetching alert param. from database
    2017-05-15 22:38:13.893555 - alert.log - INFO - ALERT DETECTED. Value: 8.0.
    2017-05-15 22:38:14.283729 - smartmodule.log - INFO - Wrote to analytic database: [{'fields': {'unit': 'C', 'value': '8.0'}, 'tags': {'site': u'HPF-0', 'asset': 'Indoor Temperature'}, 'time': '2017-05-15 22:38:14.010127', 'measurement': 'Environment'}].

An important note: we're currently using sqlite3 database to load schedule jobs and others information.
You can check/use a demo of the database here: ![Database example](/readme/database-example)
For now you should place it on the same folder as `smart_module.py` and name it as `hapi_core.db`.

You might have noticed we're using many hard-coded information. We will refactor them soon.

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
