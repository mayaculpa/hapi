#!/bin/bash

set -eu
hapi_hostname="mqttbroker"

# Information and Fatal functions
# They can be updated to write to a log file
fatal() {
	echo "[FATAL] [$(date)] $*"; exit 1;
}

info() {
	echo "[INFO] [$(date)] $*"
}

# Check if we already have a device with the hostname mqttbroker{.local}
# It depends on avahi/bonjour
check_mqttbroker() {
	info "Checking if ${hapi_hostname} already exists."
	if ping -W 1 -c 2 -s 1 mqttbroker.local > /dev/null 2>&1 ; then
		info "${hapi_hostname} does exist."
		return 1
	else
		info "${hapi_hostname} does not exist."
		return 0
	fi
}

main() {
	# Are we root?
	if [ "$EUID" -ne 0 ] ; then
		info "Please run as root"
		exit 1
	fi
	
	if check_mqttbroker ; then
		info "Changing hostname to ${hapi_hostname}."
		if hostname ${hapi_hostname} ; then
			systemctl restart avahi-daemon.service && exit 0
			fatal "Failed trying to restart avahi-daemon."
		else
			fatal "Changing hostname not possible."
		fi
	else
		exit 1
	fi
}

# Call the main function (considering to remove it)
main
