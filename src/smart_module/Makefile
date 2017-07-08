ENV_DIC = ../../venv

PACKAGES = avahi-daemon python-dev python-pip mosquitto sqlite3
PYTHON_FILES = $(wildcard *.py)
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

clean-pyc:
	@echo "[!] Cleaning compiled files."
	@rm -rfv *.pyc

compile: $(PYTHON_FILES)
	@echo "[*] Compilling all..."
	@python -m compileall .

clean-logs:
	@echo "[!] Cleaning log files."
	@rm -rfv *.log

virtual: requirements.txt
	@echo "[*] Building virtual environment for Python."
	@sudo pip install virtualenv
	@${VIRTUAL_ENV} $(ENV_DIC)
	@echo "[!] Make sure you have sourced the virtualenv. If not, run: 'source ${ENV_DIC}/bin/activate'"

packages:
	@echo "[!] Installing necessary packages."
	@pip install -r requirements.txt

.PHONY: system compile clean-pyc clean-logs virtual packages
