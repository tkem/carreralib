carreralib
========================================================================

Python library for communicating with a Carrera Digital 124/132
Control Unit.

.. code-block:: pycon

   >>> from carreralib import ControlUnit
   >>> cu = ControlUnit('D4:8B:C6:FC:D8:07', timeout=1.0)
   >>> cu.version()
   '5331'
   >>> cu.start()
   >>> cu.status()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=1, mode=6, pit=0)
   >>> cu.start()
   >>> cu.status()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=2, mode=6, pit=0)
   >>> cu.status()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=3, mode=6, pit=0)
   >>> cu.status()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=4, mode=6, pit=0)
   >>> cu.status()
   Status(fuel=(15, 15, 15, 15, 15, 15, 0, 0), start=0, mode=6, pit=0)
   >>> cu.status()
   Lap(car=2, time=742236, timer=0)


Installation
------------------------------------------------------------------------

Install carreralib using pip::

    pip install carreralib


Project Resources
------------------------------------------------------------------------

.. image:: http://img.shields.io/pypi/v/carreralib.svg?style=flat
   :target: https://pypi.python.org/pypi/carreralib/
   :alt: Latest PyPI version

.. image:: http://img.shields.io/pypi/dm/carreralib.svg?style=flat
   :target: https://pypi.python.org/pypi/carreralib/
   :alt: Number of PyPI downloads

- `Issue Tracker`_
- `Source Code`_
- `Change Log`_


License
------------------------------------------------------------------------

Copyright (c) 2015 Thomas Kemmer.

Licensed under the `MIT License`_.


.. _Issue Tracker: https://github.com/tkem/carreralib/issues/
.. _Source Code: https://github.com/tkem/carreralib/
.. _Change Log: https://github.com/tkem/carreralib/blob/master/CHANGES.rst
.. _MIT License: http://raw.github.com/tkem/carreralib/master/LICENSE
