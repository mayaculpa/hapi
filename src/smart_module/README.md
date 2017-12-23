# Smart Module

## Preparing

We have provided a `Makefile` for use that allows you to install all the necessary packages and configuration files.

Running `make help` or `make usage` will show you all the commands supported.
Example:

```
*** Hydroponic Automation Platform Initiative ***
http://hapihq.com/ & https://github.com/mayaculpa/hapi & http://hapi.readthedocs.io/

make (help|usage)
    To display this help.

make system
    To install all the necessary system packages to run the application.

make clean-logs
    To clean logs files.

make clean-pyc
    To clean pyc files.

make clean-all
    To clean logs and pyc files.

make virtual
    To install the necessary packages in order to enable a virtual environment
    using virtualenv. The default path is venv.

make packages
    To install the necessary Python packages in order to run the application.
    You can use this option inside a virtual environment.

```

To have a fully Smart Module running on your Raspberry Pi Zero or 3, run the following commands, in exactly order as below:

* `make system`:
This will install all the necessary packages on your Raspbian.

* `make virtual`:
This will install and enable a virtual environment for save use and testing (virtualenv).

Attention: before running the 3rd command, make sure to enable, by sourcing, the virtual environment. `'source bin/activate'`

* `make packages`:
This will install and the necessary Python modules/libraries.

