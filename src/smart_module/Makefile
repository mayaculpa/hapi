ENV_DIC = venv
PACKAGES = avahi-daemon python-dev python-pip mosquitto sqlite3
PIP_REQ = requirements.txt
SDL = https://raw.githubusercontent.com/switchdoclabs/RTC_SDL_DS3231/master/SDL_DS3231.py
UPDATE = yes
VIRTUAL_ENV = virtualenv

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

clean-pyc:
	@echo "[!] Cleaning compiled files."
	@rm -rfv *.pyc

clean-logs:
	@echo "[!] Cleaning log files."
	@rm -rfv *.log

clean-all: clean-pyc clean-logs

virtual:
	@echo "[*] Building virtual environment for Python."
	@sudo pip install virtualenv
	@${VIRTUAL_ENV} $(ENV_DIC)
	@echo -e "\033[33;5;7m[!] Don't forget to run: 'source $(PWD)/${ENV_DIC}/bin/activate' before running 'packages' \033[0m"

packages: $(PIP_REQ)
	@echo "[!] Installing necessary packages."
	@pip install -r $(PIP_REQ)

.PHONY: system clean-pyc clean-logs clean-all virtual packages
