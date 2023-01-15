import asyncio
import logging
import queue
import threading

from .connection import BufferTooShort, Connection, TimeoutError

SERVICE_UUID = "39df7777-b1b4-b90b-57f1-7144ae4e4a6a"
OUTPUT_UUID = "39df8888-b1b4-b90b-57f1-7144ae4e4a6a"
NOTIFY_UUID = "39df9999-b1b4-b90b-57f1-7144ae4e4a6a"

logger = logging.getLogger(__name__)


class BleakThread(threading.Thread):

    STOP_DATA = b""

    def __init__(self, address):
        super().__init__()
        self.__address = address
        self.__connected = threading.Event()
        self.__loop = None
        self.__input = queue.Queue()
        self.__output = None

    def run(self):
        asyncio.run(self.main())

    def start(self, timeout=None):
        super().start()
        if not self.__connected.wait(timeout):
            raise TimeoutError("Timeout waiting for BLE connection")

    def recv(self, timeout):
        try:
            return self.__input.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("Timeout waiting for BLE input")

    def send(self, data, timeout):
        # avoid RuntimeWarning if loop is already closed
        if self.__loop.is_running():

            async def coro():
                await self.__output.put(data)

            try:
                f = asyncio.run_coroutine_threadsafe(coro(), self.__loop)
                return f.result(timeout=timeout)
            except RuntimeError:
                if self.__loop.is_running():
                    raise

    def stop(self, timeout=None):
        self.send(self.STOP_DATA, timeout)

    async def main(self):
        from bleak import BleakClient

        self.__loop = asyncio.get_running_loop()
        self.__output = asyncio.Queue()

        async with BleakClient(self.__address) as client:
            logger.info("Connected to BLE device: %r", client)

            def notify(_, data: bytearray):
                logger.debug("Received BLE notification: %r", data)
                try:
                    self.__input.put_nowait(data)
                except asyncio.QueueFull:
                    logger.error("BLE input queue is full")

            await client.start_notify(NOTIFY_UUID, notify)

            self.__connected.set()

            while True:
                data = await self.__output.get()
                if data is not self.STOP_DATA:
                    logger.debug("Writing BLE data: %r", data)
                    await client.write_gatt_char(OUTPUT_UUID, data)
                else:
                    break

            logger.info("Closing BLE connection: %r", client)


class BLEConnection(Connection):
    def __init__(self, address, timeout=1.0):
        self.__thread = t = BleakThread(address)
        self.__timeout = timeout
        t.start()

    def close(self):
        self.__thread.stop()
        self.__thread.join()

    def recv(self, maxlength=None):
        buf = self.__thread.recv(self.__timeout)
        # BLE notifications ending with '$' do not start with command letter
        if buf.endswith(b"$"):
            if len(buf) == 6:
                buf = b"0" + buf[:-1]
            else:
                buf = b"?" + buf[:-1]
        if maxlength is not None and maxlength < len(buf):
            raise BufferTooShort("Buffer too short for data received")
        else:
            return buf

    def send(self, buf, offset=0, size=None):
        n = len(buf)
        if offset < 0:
            raise ValueError("offset is negative")
        elif n < offset:
            raise ValueError("buffer length < offset")
        elif size is None:
            size = n - offset
        elif size < 0:
            raise ValueError("size is negative")
        elif offset + size > n:
            raise ValueError("buffer length < offset + size")
        self.__thread.send(buf[offset : offset + size], self.__timeout)

    max_fwu_block_size = 18

    @classmethod
    def scan(_):
        from bleak import BleakScanner
        from bleak.exc import BleakError

        def is_cu(device, *_):
            return device.name == "Control_Unit"

        async def discover():
            # TODO: this will return only the first CU/AppConnect device found
            try:
                device = await BleakScanner.find_device_by_filter(is_cu)
                return [(device.address, device.name)] if device else []
            except BleakError:
                return []

        yield from asyncio.run(discover())
