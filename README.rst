carreralib
========================================================================

This module provides a Python interface to Carrera(R) DIGITAL 124/132
slotcar systems connected via serial port or Bluetooth.

.. code-block:: pycon

   >>> from carreralib import ControlUnit
   >>> cu = ControlUnit('D4:8B:C6:FC:D8:07')
   >>> cu.version()
   b'5331'
   >>> cu.request()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=0, mode=6,
          pit=(False, False, False, False, False, False, False, False),
          display=8)
   >>> cu.start()
   >>> cu.request()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=1, mode=6,
          pit=(False, False, False, False, False, False, False, False),
          display=8)
   >>> cu.start()
   >>> cu.request()
   Timer(address=1, timestamp=243019, sector=1)
   >>> cu.request()
   Timer(address=0, timestamp=245704, sector=1)

For Bluetooth access you will need the Carrera AppConnect(R) adapter,
a Bluetooth Low Energy compatible device, and bluepy_ installed, which
is only available for Linux. A serial connection should work on all
platforms supported by pySerial_.

For demonstration purposes, the ``carreralib`` module can also be used
from the command line as a simple race management system (RMS).

Please refer to the online documentation_ for more information.


Installation
------------------------------------------------------------------------

Install carreralib using pip::

    pip install carreralib


Project Resources
------------------------------------------------------------------------

.. image:: http://img.shields.io/pypi/v/carreralib.svg?style=flat
   :target: https://pypi.python.org/pypi/carreralib/
   :alt: Latest PyPI version

.. image:: http://img.shields.io/travis/tkem/carreralib/master.svg?style=flat
    :target: https://travis-ci.org/tkem/carreralib/
    :alt: Travis CI build status

.. image:: http://img.shields.io/coveralls/tkem/carreralib/master.svg?style=flat
   :target: https://coveralls.io/r/tkem/carreralib
   :alt: Test coverage

.. image:: https://readthedocs.org/projects/carreralib/badge/?version=latest&style=flat
   :target: http://carreralib.readthedocs.io/en/latest/
   :alt: Documentation Status

- `Issue Tracker`_
- `Source Code`_
- `Change Log`_


License
------------------------------------------------------------------------

Copyright (c) 2015-2017 Thomas Kemmer.

Licensed under the `MIT License`_.

Carrera and Carrera AppConnect are registered trademarks of Stadlbauer
Marketing + Vertrieb GmbH.

Thanks to Stephan Heß (a.k.a. slotbaer_) for doing all the hard work.


.. _bluepy: https://github.com/IanHarvey/bluepy
.. _pyserial: http://pythonhosted.org/pyserial/

.. _Documentation: http://carreralib.readthedocs.io/en/latest/
.. _Issue Tracker: https://github.com/tkem/carreralib/issues/
.. _Source Code: https://github.com/tkem/carreralib/
.. _Change Log: https://github.com/tkem/carreralib/blob/master/CHANGES.rst
.. _MIT License: http://raw.github.com/tkem/carreralib/master/LICENSE

.. _slotbaer: http://www.slotbaer.de/
