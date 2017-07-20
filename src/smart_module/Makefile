ENV_DIC = venv
PACKAGES = avahi-daemon python-dev python-pip mosquitto sqlite3
PIP_REQ = requirements.txt
SDL = https://raw.githubusercontent.com/switchdoclabs/RTC_SDL_DS3231/master/SDL_DS3231.py
UPDATE = yes
VIRTUAL_ENV = virtualenv

# TODO
# 'install'
#     In order to install, if necessary, all the files in their respective folders.

usage help:
	@echo "*** Hydroponic Automation Platform Initiative ***"
	@echo "http://hapihq.com/ & https://github.com/mayaculpa/hapi & http://hapi.readthedocs.io/"
	@echo " "
	@echo "make (help|usage)"
	@echo "    To display this help."
	@echo " "
	@echo "make system"
	@echo "    To install all the necessary system packages to run the application."
	@echo " "
	@echo "make clean-logs"
	@echo "    To clean logs files."
	@echo " "
	@echo "make clean-pyc"
	@echo "    To clean pyc files."
	@echo " "
	@echo "make clean-all"
	@echo "    To clean logs and pyc files."
	@echo " "
	@echo "make virtual"
	@echo "    To install the necessary packages in order to enable a virtual environment "
	@echo "    using $(VIRTUAL_ENV). The default path is $(ENV_DIC)."
	@echo " "
	@echo "make packages"
	@echo "    To install the necessary Python packages in order to run the application."
	@echo "    You can use this option inside a virtual environment."
	@echo " "

system:
	@echo "[*] Installing: $(PACKAGES)"
ifeq ($(UPDATE),yes)
	@sudo apt-get update
endif
	@sudo apt-get -y install $(PACKAGES)
	@echo "[*] Fetching standalone module from github: $(SDL)"
	@wget $(SDL)
	@echo "[*] Copying configuration files."
	@sudo cp -fv ../../docs/example_configs/mosquitto-example /etc/mosquitto/mosquitto.conf
	@sudo cp -fv ../../docs/example_configs/avahi-example /etc/avahi/services/mosquitto.service

virtual:
	@echo "[*] Building virtual environment for Python."
	@sudo pip install virtualenv
	@${VIRTUAL_ENV} $(ENV_DIC)
	@echo -e "[!] Make sure to run: 'source $(PWD)/$(ENV_DIC)/bin/activate'"

packages: $(PIP_REQ)
	@echo "[!] Installing necessary packages."
	@pip install -r $(PIP_REQ)

clean-pyc:
	@echo "[!] Cleaning compiled files."
	@rm -rfv *.pyc

clean-logs:
	@echo "[!] Cleaning log files."
	@rm -rfv *.log

clean-all: clean-pyc clean-logs

.PHONY: usage help system clean-pyc clean-logs clean-all virtual packages
