============
UCI cBP demo
============


.. image:: https://img.shields.io/pypi/v/uci_cbp_demo.svg
        :target: https://pypi.python.org/pypi/uci_cbp_demo

.. image:: https://img.shields.io/travis/taoyilee/uci_cbp_demo.svg
        :target: https://travis-ci.com/taoyilee/uci_cbp_demo

.. image:: https://readthedocs.org/projects/uci-cbp-demo/badge/?version=latest
        :target: https://uci-cbp-demo.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




GUI to demo continuous blood pressure sensing works on Linux, Windows, and MacOS X.
This GUI requires custom firmware installed on `MbientLab Metamotion R device <https://mbientlab.com/metamotionr>`_, and a capacitor to digital converter
from Analog Devices, `AD7746 <https://www.analog.com/media/en/technical-documentation/data-sheets/AD7745_7746.pdf>`_.

Pull requests welcome! Please fork repository to begin with.


* Free software: MIT license
* Documentation: https://uci-bp-demo.readthedocs.io/en/latest/index.html.


Quick Start
-------------
Following command assumes a Linux environment. For Windows and MacOSX setup, you may need to tweak the commands a
little bit, according to your system setup.

.. code-block:: console

    # setup virtual environment
    python -m venv venv

    # enter virtual environment
    source venv/bin/activate

    # install the latest code from PyPI
    pip install uci-cbp-demo

    # power up the hardware

    # start GUI with parameters a=1 b=0
    uci_cbp_demo gui -a 1 -b 0

To list available CLI options, use

.. code-block:: console

    uci_cbp_demo gui --help
    # Usage: uci_cbp_demo gui [OPTIONS]
    #
    # Options:
    # -a INTEGER  Scaling coefficient
    # -b INTEGER  Shifting in Y
    # --help      Show this message and exit.

Troubleshooting
------------------
1. If you run into issues saying

      Could not fetch URL https://pypi.python.org/ ... There was a problem confirming the ssl certificate: [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl.c:645) - skipping

   Try follow steps described in `pypa repository <https://github.com/pypa/pip/issues/5236>`_

.. code-block:: console

    curl https://bootstrap.pypa.io/get-pip.py | python

MAC OS Notes
------------------
1. OS X/macOS support via Core Bluetooth API, from at least version 10.11
2. The macOS backend of Bleak is written with pyobjc directives for interfacing with Foundation and CoreBluetooth APIs. There are some values that pyobjc is not able to overwrite and thuse the corebleak framework was written to circumvent these issues. The most noticible difference between the other backends of bleak and this backend, is that CoreBluetooth doesn’t scan for other devices via MAC address. Instead, UUIDs are utilized that are often unique between the device that is scanning the the device that is being scanned.

Credits
-------
This package is co-developed with Wongi Baek and Joonkyu Seo.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
