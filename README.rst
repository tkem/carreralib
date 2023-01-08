carreralib
========================================================================

.. image:: http://img.shields.io/pypi/v/carreralib
   :target: https://pypi.org/project/carreralib/
   :alt: Latest PyPI version

.. image:: https://img.shields.io/github/actions/workflow/status/tkem/carreralib/ci.yml
   :target: https://github.com/tkem/carreralib/actions/workflows/ci.yml
   :alt: CI build status

.. image:: https://img.shields.io/readthedocs/carreralib
   :target: http://carreralib.readthedocs.io/
   :alt: Documentation build status

.. image:: https://img.shields.io/codecov/c/github/tkem/carreralib/master.svg
   :target: https://codecov.io/gh/tkem/carreralib
   :alt: Test coverage

.. image:: https://img.shields.io/github/license/tkem/cachetools
   :target: https://raw.github.com/tkem/cachetools/master/LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black


This module provides a Python interface to Carrera® DIGITAL 124/132
slotcar systems connected via a serial (cable) connection, or via
Bluetooth LE using Carrera AppConnect®.

.. code-block:: pycon

   >>> from carreralib import ControlUnit
   >>> cu = ControlUnit('/dev/ttyUSB0')
   >>> cu.version()
   '5337'
   >>> cu.poll()
   Status(fuel=(14, 14, 14, 14, 14, 14, 0, 0), start=0, mode=6,
          pit=(False, False, False, False, False, False, False, False),
          display=8)
   >>> cu.start()
   >>> cu.poll()
   Status(fuel=(14, 14, 14, 14, 14, 14, 0, 0), start=1, mode=6,
          pit=(False, False, False, False, False, False, False, False),
          display=8)
   >>> cu.start()
   >>> cu.poll()
   Timer(address=1, timestamp=105295, sector=1)
   >>> cu.poll()
   Timer(address=0, timestamp=105410, sector=1)

For demonstration purposes, the ``carreralib`` module can also be used
from the command line as a simple race management system (RMS).

Please refer to the online documentation_ for more information.


Installation
------------------------------------------------------------------------

carreralib is available from PyPI_ and can be installed by running::

    pip install carreralib


Project Resources
------------------------------------------------------------------------

- `Documentation`_
- `Issue Tracker`_
- `Source Code`_
- `Change Log`_


License
------------------------------------------------------------------------

Copyright (c) 2015-2022 Thomas Kemmer.

Licensed under the `MIT License`_.

Carrera® and Carrera AppConnect® are registered trademarks of Carrera
Toys GmbH.

``carreralib`` is not an official Carrera® product, and is not
affiliated with or endorsed by Carrera Toys GmbH.

Thanks to Stephan Heß (a.k.a. slotbaer_) for doing all the hard work.

.. _PyPI: https://pypi.org/project/carreralib/
.. _Documentation: http://carreralib.readthedocs.io/en/latest/
.. _Issue Tracker: https://github.com/tkem/carreralib/issues/
.. _Source Code: https://github.com/tkem/carreralib/
.. _Change Log: https://github.com/tkem/carreralib/blob/master/CHANGELOG.rst
.. _MIT License: http://raw.github.com/tkem/carreralib/master/LICENSE

.. _slotbaer: http://www.slotbaer.de/
