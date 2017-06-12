These instructions are for installing the hapi smart module software on a
`Raspberry Pi <https://www.raspberrypi.org/>`_
`3B <https://www.raspberrypi.org/products/raspberry-pi-3-model-b/>`_ or
`Zero W <https://www.raspberrypi.org/products/pi-zero-w/>`_.

Install `Raspbian <https://www.raspberrypi.org/downloads/raspbian/>`_
according to their
`instruction guide <https://www.raspberrypi.org/documentation/installation/installing-images/README.md>`_.

The following are done on the smart module.

#. Boot Raspbian.
#. Connect to the web.
#. Open a web browser.
#. Browse to `this file <https://github.com/mayaculpa/hapi/blob/master/src/smart_module/INSTALL.rst>`_.

Open a terminal program and execute the following commands.
(Copy from browser and paste into terminal emulator program,
one line at a time.) ::

    sudo apt-get install git
    cd ~
    git clone https://github.com/mayaculpa/hapi.git
    cd ~/hapi/src/smart_module
    ./INSTALL.sh
