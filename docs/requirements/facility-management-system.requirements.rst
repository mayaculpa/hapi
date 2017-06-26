===========================================
Facility Management System (FMS) Activities
===========================================

.. image:: ../img/hapi-four-leaf-square.png

Home Screen
===========

- User can see/edit Site Name
- User can see activated Alerts
- Show current Asset (sensor) readings
- User can rename an asset
- User can select frequency of screen refresh
- HAPI Logo should be visible

Configure Site
==============
- Set WiFi SSID and Password (bluetooth based)
- Set Cloud Analytics User and Password
- Set Site Name
- Set Operator Email Address
- Set Latitude and Longitude
- Set Weather Underground API Key Information (tentative)
- Set Twilio Account Information (SSID & Token) (tentative)

Manage Scheduled Jobs
=====================
- Schedulable Jobs are
    - Check Alerts
    - Get Sensor Data
    - Get System Health
    - Get Weather Data (if Wunderground info is set)
- User can Enable/Disable jobs
- User can set job time interval to seconds, minutes, hours or days
- User can set the frequency in integer values
    - The above 2 reqs allow the user to run a job “every 10 seconds", “every 3 hours”, etc

View Analytics
==============
- User can view historic/analytic visualizations in WebView

Manage Alerts
=============
- User can Create an alert with Asset Name, Lower Threshold, Upper Threshold
- User can edit alert message e.g. “Reservoir Level Low”
- User can set 1 or more notification options for an alert (email, SMS, Home Screen)
- Multiple alerts can be created for any 1 asset
    - This supports scenarios like show an On-Screen if the level is low and send a text message
- if it goes empty.
- User can Disable/Enable an alert
- User can Delete an alert
