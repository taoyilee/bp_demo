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




GUI to demo continuous blood pressure sensing


* Free software: MIT license
* Documentation: https://uci-cbp-demo.readthedocs.io.


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
    pip install pip install uci-cbp-demo

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

Credits
-------
This package is co-developed with Wongi Baek and Joonkyu Seo.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
