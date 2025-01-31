1.0.3 2025-01-31
----------------

- Upgrade Development Status to ``Production``.

- Officially support Python 3.13.


1.0.2 2023-01-15
----------------

- Create ``asyncio.Queue`` with correct event loop.


1.0.1 2023-01-08
----------------

- Improve BLE device detection on MacOS.

- ``badges/shields``: Change to GitHub workflow badge routes.


1.0.0 2022-12-11
----------------

- Add BLE connection based on ``bleak``.

- Add "raw byte" protocol format.

- Implement BLE firmware update.


0.10.1 2022-11-24
-----------------

- Add checksum to reset and button press commands.


0.10.0 2022-11-22
-----------------

- Add ``ControlUnit.poll()`` method.

- Add ``ControlUnit.press()`` method and button IDs.


0.9.2 2022-11-20
----------------

- Fix ``SerialConnection.close()`` with invalid device.

- Improve firmware option and error handling.


0.9.1 2022-11-16
----------------

- Use ``windows-curses`` on Windows platforms.

- List serial devices with RMS command-line options.

- Improve documentation.


0.9.0 2022-11-09
----------------

- Add firmware update functions.

- Return CU version as a string.


0.8.0 2022-11-08
----------------

- Require Python 3.7 or later.

- Drop ``bluepy`` support.

- Prevent screen flicker in demo RMS.


0.7.0 2020-06-14
----------------

- Require Python 3.5 or later.


0.6.0 2017-12-05
----------------

- Add constants for key-emulating requests.

- Improve documentation.


0.5.0 2017-12-04
----------------

- Remove ``bluepy`` dependency.

- Move documentation to RTD.

- Add Python 3.6 support.

- Drop Python 3.3 support.


0.4.1 2017-05-06
----------------

- Minor demo UI improvements.


0.4.0 2017-05-06
----------------

- Add CU key codes to demo application.


0.3.0 2016-05-05
----------------

- Add ``bluepy`` dependency.

- Add workaround for changed ``?:`` format.

- Add support for Python 3.5, drop Python 3.2 support.


0.2.0 2015-07-17
----------------

- Add demo RMS.

- Add documentation.

- Refactor protocol handling.


0.1.0 2015-07-04
----------------

- Initial release.
