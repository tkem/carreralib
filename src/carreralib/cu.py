import logging
from collections import namedtuple

from . import connection
from . import protocol

logger = logging.getLogger(__name__)


class ControlUnit(object):
    """Interface to a Carrera Digital 124/132 Control Unit."""

    class Status(namedtuple("Status", "fuel start mode pit display")):
        """Response type returned if no timer events are pending.

        This is a :class:`collections.namedtuple` subclass with the
        following read-only attributes:

        +-----------------+-------+-------------------------------------------+
        | Attribute       | Index | Value                                     |
        +=================+=======+===========================================+
        | :attr:`fuel`    | 0     | Eight-item list of fuel levels (0..15)    |
        +-----------------+-------+-------------------------------------------+
        | :attr:`start`   | 1     | Start light indicator (0..9)              |
        +-----------------+-------+-------------------------------------------+
        | :attr:`mode`    | 2     | 4-bit mode bit mask                       |
        +-----------------+-------+-------------------------------------------+
        | :attr:`pit`     | 3     | 8-bit pit lane bit mask                   |
        +-----------------+-------+-------------------------------------------+
        | :attr:`display` | 4     | Number of drivers to display (6 or 8)     |
        +-----------------+-------+-------------------------------------------+

        """

        __slots__ = ()

        FUEL_MODE = 0x1
        """Mode bit mask indicating fule mode is enabled."""

        REAL_MODE = 0x2
        """Mode bit mask indicating real fuel mode is enabled."""

        PIT_LANE_MODE = 0x4
        """Mode bit mask indicating a pit lane adapter is connected."""

        LAP_COUNTER_MODE = 0x8
        """Mode bit mask indicating a lap counter is connected."""

    class Timer(namedtuple("Timer", "address timestamp sector")):
        """Response type for timer events.

        This is a :class:`collections.namedtuple` subclass with the
        following read-only attributes:

        +-------------------+-------+-----------------------------------------+
        | Attribute         | Index | Value                                   |
        +===================+=======+=========================================+
        | :attr:`address`   | 0     | Controller address (0..7)               |
        +-------------------+-------+-----------------------------------------+
        | :attr:`timestamp` | 1     | 32-bit time stamp in milleseconds       |
        +-------------------+-------+-----------------------------------------+
        | :attr:`sector`    | 2     | Sector (1 for start/finish, 2 or 3 for  |
        |                   |       | times reported by Check Lanes)          |
        +-------------------+-------+-----------------------------------------+

        """

        pass

    PACE_CAR_KEY = b"T1"
    """Request for emulating the Control Unit's PACE CAR/ESC key."""

    START_KEY = b"T2"
    """Request for emulating the Control Unit's START/ENTER key."""

    SPEED_KEY = b"T5"
    """Request for emulating the Control Unit's SPEED key."""

    BRAKE_KEY = b"T6"
    """Request for emulating the Control Unit's BRAKE key."""

    FUEL_KEY = b"T7"
    """Request for emulating the Control Unit's FUEL key."""

    CODE_KEY = b"T8"
    """Request for emulating the Control Unit's CODE key."""

    def __init__(self, device, **kwargs):
        if isinstance(device, connection.Connection):
            self.__connection = device
        else:
            logger.debug("Connecting to %s", device)
            self.__connection = connection.open(device, **kwargs)
            logger.debug("Connection established")

    def close(self):
        """Close the connection to the CU."""
        logger.debug("Closing connection")
        self.__connection.close()

    def clrpos(self):
        """Clear/reset the Position Tower display."""
        self.setword(6, 0, 9)

    def ignore(self, mask):
        """Ignore the controllers represented by bitmask `mask`."""
        self.request(protocol.pack("cBC", b":", mask))

    def request(self, buf=b"?", maxlength=None):
        """Send a message to the CU and wait for a response.

        The returned value will be an instance of either
        :class:`ControlUnit.Timer` or :class:`ControlUnit.Status`,
        depending on whether any timer events are pending.

        """
        logger.debug("Sending message %r", buf)
        self.__connection.send(buf)
        while True:
            res = self.__connection.recv(maxlength)
            if not res:
                logger.warn("Received unknown command response")
                break
            elif res.startswith(buf[0:1]):
                break
            else:
                logger.warn("Received unexpected message %r", res)
        logger.debug("Received message %r", res)
        if res.startswith(b"?:"):
            # recent CU versions report two extra unknown bytes with '?:'
            try:
                parts = protocol.unpack("2x8YYYBYC", res)
            except protocol.ChecksumError:
                parts = protocol.unpack("2x8YYYBYxxC", res)
            fuel, (start, mode, pitmask, display) = parts[:8], parts[8:]
            pit = tuple(pitmask & (1 << n) != 0 for n in range(8))
            return ControlUnit.Status(fuel, start, mode, pit, display)
        elif res.startswith(b"?"):
            address, timestamp, sector = protocol.unpack("xYIYC", res)
            return ControlUnit.Timer(address - 1, timestamp, sector)
        else:
            return res

    def reset(self):
        """Reset the CU timer."""
        self.request(b"=10")

    def setbrake(self, address, value):
        """Set the brake value for controller `address`."""
        self.setword(1, address, value, repeat=2)

    def setfuel(self, address, value):
        """Set the fuel value for controller `address`."""
        self.setword(2, address, value, repeat=2)

    def setlap(self, value):
        """Set the current lap displayed by the Position Tower."""
        if value < 0 or value > 255:
            raise ValueError("Lap value out of range")
        self.setlap_hi(value >> 4)
        self.setlap_lo(value & 0xF)

    def setlap_hi(self, value):
        """Set the high nibble of the current lap."""
        self.setword(17, 7, value)

    def setlap_lo(self, value):
        """Set the low nibble of the current lap."""
        self.setword(18, 7, value)

    def setpos(self, address, position):
        """Set the controller's position displayed by the Position Tower."""
        if position < 1 or position > 8:
            raise ValueError("Position out of range")
        self.setword(6, address, position)

    def setspeed(self, address, value):
        """Set the speed value for controller address."""
        self.setword(0, address, value, repeat=2)

    def setword(self, word, address, value, repeat=1):
        if word < 0 or word > 31:
            raise ValueError("Command word out of range")
        if address < 0 or address > 7:
            raise ValueError("Address out of range")
        if value < 0 or value > 15:
            raise ValueError("Value out of range")
        if repeat < 1 or repeat > 15:
            raise ValueError("Repeat count out of range")
        buf = protocol.pack("cBYYC", b"J", word | address << 5, value, repeat)
        return self.request(buf)

    def start(self):
        """Initiate the CU start sequence."""
        self.request(self.START_KEY)

    def version(self):
        """Retrieve the CU version as a string."""
        res = self.request(b"0")
        if res:
            return protocol.unpack("x4sC", res)[0].decode()
        else:
            return None  # TODO: raise here?

    def fwu_start(self):
        """Initiate a CU firmware update."""
        # G: start update, B: control unit
        self.request(protocol.pack("ccC", b"G", b"B"))

    def fwu_write(self, data):
        """Write CU firmware update data."""
        # TODO: with BLE, data is split into chunks of max. 18 bytes,
        # chunks are preceded by 'F', and EOL is written as a
        # seperate, empty 'E' command...
        self.request(protocol.pack(f"c{len(data)}sC", b"E", data))
