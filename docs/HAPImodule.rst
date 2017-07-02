HAPImodule
==========

Release 1 of the HAPI system uses Raspberry Pi Zeros (HAPiZ) as the **Smart Modules** that run the system code, the sensor code and the control code. Multiple HAPiZ devices can exist within the system and collaborate to determine the tasks performed by each module.

Hardware Setup
--------------
A minimum HAPiZ module consists of the following components:

* Raspberry Pi Zero
* Real-time-clock (DS3231)
* Temperature and humidity sensor (DHT22)

  .. image:: img/DHT22.jpg

* Water temperature sensor (DS18B20)

  .. image:: img/DS18B20.jpg

Prototype Diagram
~~~~~~~~~~~~~~~~~
.. image:: img/HAPImodule.png

Software Setup
--------------
Note: Soon we'll introduce configuration via regular file and/or database. For now all configuration are hardcoded.

1. Install `Raspbian <https://www.raspberrypi.org/downloads/raspbian/>`_ on the Raspberry Pi

  * `Raspbian installation guide <https://www.raspberrypi.org/documentation/installation/installing-images/README.md>`_.

2. Install dependencies on the Pi

  * Dependencies:

    * **Avahi** (daemon) configured to publish MQTT service.

      * :download:`Example config <example_configs/avahi-example>`
      * Restart to apply changes:

        .. code:: shell

            systemctl restart avahi-daemon.service

    * **MQTT Mosquitto** with default configuration.

      * :download:`Example config <example_configs/mosquitto-example>`

    * **Influxdb** with default configuration.
    * **Grafana** [Optional] (highly recommended).

  * There is also a script from the repo for installing the first two system dependencies and then setup the python environment:

      .. code:: shell

          sudo apt-get install git
          cd ~
          git clone https://github.com/mayaculpa/hapi.git
          cd ~/hapi/src/smart_module
          ./INSTALL.sh

    * It is good practice to look over scripts you download from the Internet before running them.

Usage
-----
**Start the program:**

.. code:: shell

    python smart_module.py


**You should get output like this:**

.. code:: shell

    (venv) $ python smart_module.py
    2017-07-02 12:15:58.202878 - smartmodule.log - [*] INFO - Communicator initialized
    Mock Smart Module hosting asset HSM-WT123-MOCK wt Environment.
    2017-07-02 12:15:58.211355 - smartmodule.log - [*] INFO - Performing Broker discovery...
    2017-07-02 12:16:01.213817 - smartmodule.log - [*] INFO - MQTT Broker: ArchMain.local. IP: 192.168.0.99.
    2017-07-02 12:16:04.217127 - smartmodule.log - [*] INFO - Connecting to ArchMain.local. at 192.168.0.99.
    2017-07-02 12:16:04.218420 - smartmodule.log - [*] INFO - Closing Zeroconf connection.
    2017-07-02 12:16:04.239513 - smartmodule.log - [*] INFO - Connected with result code 0
    $SYS/broker/clients/total 0
    2017-07-02 12:16:08.720840 - smartmodule.log - [*] INFO - No Scheduler found. Becoming the Scheduler.
    2017-07-02 12:16:08.721437 - smartmodule.log - [*] INFO - Loading Schedule Data...
    2017-07-02 12:16:08.748795 - smartmodule.log - [*] INFO - Schedule Data Loaded.
    2017-07-02 12:16:08.749374 - smartmodule.log - [*] INFO -   Loading seconds job: System Status.
    2017-07-02 12:16:08.749580 - smartmodule.log - [*] INFO -   Loading seconds job: Check Alert.
    2017-07-02 12:16:08.750986 - smartmodule.log - [*] INFO - Scheduler program loaded.
    2017-07-02 12:16:08.753495 - smartmodule.log - [*] INFO - Influxdb information loaded.
    2017-07-02 12:16:08.755970 - smartmodule.log - [*] INFO - Site data loaded.
    $SYS/broker/clients/total 1
    Running command self.smart_module.on_check_alert()
    ASSET/QUERY Is it warm here?
    ASSET/RESPONSE/HSM-WT123-MOCK {"value_current": "31.0", "name": "Temperature Sensor", "context": "Environment", "virtual": 1, "type": "wt", "enabled": 1, "id": "HSM-WT123-MOCK", "unit": "C", "system": ""}
    2017-07-02 12:16:19.070110 - smartmodule.log - [*] INFO - Wrote to analytic database.
    2017-07-02 12:16:19.070215 - smartmodule.log - [*] INFO - Fetching alert parameters from database.
    2017-07-02 12:16:19.070936 - smartmodule.log - [*] INFO - Closing Alert database connection.
    2017-07-02 12:16:19.071006 - smartmodule.log - [*] INFO - [!] ALERT DETECTED. Value: 31.0.
    ALERT/HSM-WT123-MOCK {"upper": 30.0, "lower": 10.0, "value_current": "31.0", "response": "email,sms", "message": "Houston, we have a problem", "notify_enabled": 1, "id": "HSM-WT123-MOCK"}
    2017-07-02 12:16:19.071630 - smartmodule.log - [*] INFO - Sending email notification.
    2017-07-02 12:16:19.072025 - smartmodule.log - [*] INFO - Mail settings loaded.
    2017-07-02 12:16:22.287407 - smartmodule.log - [*] INFO - Email notification sent.
    2017-07-02 12:16:22.485832 - smartmodule.log - [*] INFO - Sending SMS notification.
    [...]


An important note: we're currently using sqlite3 database to load schedule jobs and others information.
You can check/use a demo of the database here: :download:`database-example <example_configs/database-example>`
For now you should place it on the same folder as `smart_module.py` and name it as `hapi_core.db`.
