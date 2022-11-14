class ConnectionError(Exception):
    """The base class of all connection exceptions."""

    pass


class BufferTooShort(ConnectionError):
    """Raised when the supplied buffer is too small a message."""

    pass


class TimeoutError(ConnectionError):
    """Raised when a timeout expires."""

    pass


class Connection(object):
    """Base class for connections to a Carrera digital slotcar
    system."""

    def __init__(self, device, **kwargs):
        pass

    def close(self):
        """Close the connection."""
        pass

    def recv(self, maxlength=None):
        """Return a complete message of byte data sent from the other
        end of the connection as a bytes object.

        """
        raise NotImplementedError

    def send(self, buf, offset=0, size=None):
        """Send byte data rom an object supporting the buffer
        interface as a complete message."""
        raise NotImplementedError


def open(device, **kwargs):
    """Open a connection to the given device."""
    from .serial import SerialConnection

    return SerialConnection(device, **kwargs)


def scan():
    """Search for potential devices."""
    from .serial import SerialConnection

    return SerialConnection.scan()
