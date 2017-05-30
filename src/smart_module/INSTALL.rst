These instructions are for installing the hapi smart module software on a
Raspberry Pi 3B or Raspberry Pi Zero W.

Install [Raspbian](https://www.raspberrypi.org/downloads/raspbian/)
according to their [instruction guide](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

The following are done on the smart module.

Boot Raspbian.
Connect to the web.
Open a web browser.
Browse to [this file](https://github.com/mayaculpa/hapi/blob/master/src/smart_module/INSTALL.rst).

Open a terminal program and execute the following commands.
(Copy from browser and paste into terminal emulator program,
one line at a time.)

    sudo apt-get install git
    cd ~
    git clone https://github.com/mayaculpa/hapi.git
    cd ~/hapi/src/smart_module
    ./INSTALL.sh

