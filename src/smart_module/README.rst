The smart modules run on [Raspberry Pi](https://www.raspberrypi.org/)
[3B](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) or
[Zero W](https://www.raspberrypi.org/products/pi-zero-w/).

See INSTALL.rst for installation instructions.

**Note**: the system will try to import all the necessary sensor modules to run.
If it can't, then the system will automatically run on "mock" mode.
If you are facing any troubles to get it running, drop us a message or open an issue.

System Configuration
====================
Note: Soon we'll introduce configuration via regular file and/or database. For now all configuration are hardcoded.
The system needs the following packages installed and properly configured:

1. **Avahi** (daemon) configured to publish MQTT service.

   Here is an example. ![avahi-example](/readme/avahi-example)

   Note: it must be off by default (systemctl stop avahi-daemon.service or similar).
2. **MQTT Mosquitto** with default configuration.

   Here is an example. ![mosquitto-example](/readme/mosquitto-example)
3. **Influxdb** with default configuration.
4. **Grafana** [Optional] (highly recommended).

Usage:
======
.. code:: shell

    python smart_module.py


**You should get something like this:**

.. code:: shell

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

