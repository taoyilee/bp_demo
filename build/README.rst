============================
Building Windows installer
============================

Follow the instruction `here <https://pynsist.readthedocs.io/en/latest/faq.html#packaging-with-tkinter>`_.
The TCL packages are included under ``pynsist_pkgs`` and ``lib`` which may be removed in the future releases.


Bump version
===================
Basic usage is

.. code-block:: bash

    bumpversion [options] part [file]

to bump version, use the following syntax

.. code-block:: bash

    bumpversion --current-version x.y.z {major,minor,patch} setup.py



Check dependency tree
============================
.. code-block:: bash

    pip install pipdeptree # if pipdeptree has not been installed
    pipdeptree -fl
