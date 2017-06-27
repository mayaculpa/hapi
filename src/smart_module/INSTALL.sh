#!/usr/bin/env bash

# This takes care of latter part of installation of hapi smart module software
# on suitable computer running Raspbian.

# Exit on error
set -e

# Virtualenv settings
VIRTUAL_ENV="false"
VIRTUAL_PATH=""

# System packages
NECESSARY_PACKAGES=('avahi-daemon' 'python-dev' 'python-pip' 'mosquitto')
# We still *need* influxdb and *maybe* grafana

# Information output, same as echo but with timestamp
info() { echo "[*] [$(date)] : $*"; }

main() {
    case "$1" in
        --help|-h)
            echo "Usage: $0 [--virtualenv|-v path]"
            exit 0
            ;;
        --virtual|-v)
            info "Make sure you have virtualenv installed."
            VIRTUAL_ENV="true"
            if [ -z "$2" ]; then
                info "Error. You didn't provide a path for virtualenv."
                exit -1
            fi
            ;;
    esac

    # Installing necessary system packages. python-dev needed for RPi.GPIO
    info "Installing necessay system packages: ${NECESSARY_PACKAGES[*]}"
    apt-get install "${NECESSARY_PACKAGES[*]}"

    if [ "$VIRTUAL_ENV" == "true" ]; then
        info "Enabling virtualenv at $VIRTUAL_PATH"
        # virtualenv for legacy Python (i.e., Python 2)
        # sudo apt-get install virtualenv ;# use pip instead
        virtualenv "$VIRTUAL_PATH"
        source "${VIRTUAL_PATH}/bin/activate"
    fi

    info "Installing python modules..."
    pip install -r requirements.txt

    # Installing a lone file from a project is ugly and suspicious.
    # Following needed only if running on real mode (with actual sensor data).
    info "Fetching SDL module..."
    wget https://raw.githubusercontent.com/switchdoclabs/RTC_SDL_DS3231/master/SDL_DS3231.py
}

main "$@"
