#!/usr/bin/env bash

# This takes care of latter part of installation of hapi smart module software
# on suitable computer running Raspbian.

# virtualenv for legacy Python (i.e., Python 2)
# sudo apt-get install virtualenv ;# use pip instead
sudo pip install virtualenv
virtualenv env
source env/bin/activate

sudo apt-get install python-dev ;# Needed for RPi.GPIO

pip install -r requirements.txt

# Installing a lone file from a project is ugly and suspicious.
# Following needed only if running on real mode (with actual sensor data).
wget https://raw.githubusercontent.com/switchdoclabs/RTC_SDL_DS3231/master/SDL_DS3231.py
