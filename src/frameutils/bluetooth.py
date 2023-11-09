import asyncio

from bleak import BleakClient, BleakScanner


class Bluetooth:
    """
    Frame bluetooth class for managing a connection and transferring data to and
    from the device.
    """

    _SERVICE_UUID = "7a230001-5475-a6a4-654c-8431f6ad49c4"
    _TX_CHARACTERISTIC_UUID = "7a230002-5475-a6a4-654c-8431f6ad49c4"
    _RX_CHARACTERISTIC_UUID = "7a230003-5475-a6a4-654c-8431f6ad49c4"

    def __init__(self):
        self._awaiting_print_response = False
        self._awaiting_data_response = False
        self._client = None
        self._print_response = bytearray()
        self._data_response = bytearray()
        self._tx_characteristic = None
        self._user_data_response_handler = lambda: None
        self._user_disconnect_handler = lambda: None
        self._user_print_response_handler = lambda: None

    def _filter_uuid(self, _, adv):
        return self._SERVICE_UUID in adv.service_uuids

    def _disconnect_handler(self, _):
        self._user_disconnect_handler()
        self.__init__()

    async def _notification_handler(self, _, data):
        if data[0] == 1:
            if self._awaiting_data_response:
                self._awaiting_data_response = False
                self._data_response = data[1:]
            self._user_data_response_handler(data[1:])
        else:
            if self._awaiting_print_response:
                self._awaiting_print_response = False
                self._print_response = data.decode()
            self._user_print_response_handler(data.decode())

    async def connect(
        self,
        print_response_handler=lambda _: None,
        data_response_handler=lambda _: None,
        disconnect_handler=lambda: None,
    ):
        """
        Connects to the nearest Frame device.

        `print_response_handler` and `data_response_handler` can be provided and
        will be called whenever data arrives from the device asynchronously.

        `disconnect_handler` can be provided to be called to run
        upon a disconnect.
        """
        self._user_disconnect_handler = disconnect_handler
        self._user_print_response_handler = print_response_handler
        self._user_data_response_handler = data_response_handler

        device = await BleakScanner.find_device_by_filter(
            self._filter_uuid,
        )

        if device is None:
            raise Exception("no devices found")

        self._client = BleakClient(
            device,
            disconnected_callback=self._disconnect_handler,
        )

        # TODO find a way to connect to the closest device (highest RSSI)

        await self._client.connect()

        await self._client.start_notify(
            self._RX_CHARACTERISTIC_UUID,
            self._notification_handler,
        )

        service = self._client.services.get_service(
            self._SERVICE_UUID,
        )

        self._tx_characteristic = service.get_characteristic(
            self._TX_CHARACTERISTIC_UUID,
        )

    async def disconnect(self):
        """
        Disconnects from the device.
        """
        await self._client.disconnect()
        self._disconnect_handler(None)

    def is_connected(self):
        """
        Returns `True` if the device is connected. `False` otherwise.
        """
        try:
            return self._client.is_connected
        except AttributeError:
            return False

    def max_lua_payload(self):
        """
        Returns the maximum length of a Lua string which may be transmitted.
        """
        try:
            return self._client.mtu_size - 3
        except AttributeError:
            return 0

    def max_data_payload(self):
        """
        Returns the maximum length of a raw bytearray which may be transmitted.
        """
        try:
            return self._client.mtu_size - 4
        except AttributeError:
            return 0

    async def _transmit(self, data, show_me=False):
        if show_me:
            print(data)  # TODO make this print nicer

        if len(data) > self._client.mtu_size - 3:
            raise Exception("payload length is too large")

        await self._client.write_gatt_char(self._tx_characteristic, data)

    async def send_lua(self, string: str, show_me=False, await_print=False):
        """
        Sends a Lua string to the device. The string length must be less than or
        equal to `max_lua_payload()`.

        If `await_print=True`, the function will block until a Lua print()
        occurs, or a timeout.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(string.encode(), show_me=show_me)

        if await_print:
            self._awaiting_print_response = True
            countdown = 5000

            while self._awaiting_print_response:
                await asyncio.sleep(0.001)
                if countdown == 0:
                    raise Exception("device didn't respond")
                countdown -= 1

            return self._print_response

    async def send_data(self, data: bytearray, show_me=False, await_data=False):
        """
        Sends raw data to the device. The payload length must be less than or
        equal to `max_data_payload()`.

        If `await_data=True`, the function will block until a data response
        occurs, or a timeout.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(bytearray(b"\x01") + data, show_me=show_me)

        if await_data:
            self._awaiting_data_response = True
            countdown = 5000

            while self._awaiting_data_response:
                await asyncio.sleep(0.001)
                if countdown == 0:
                    raise Exception("device didn't respond")
                countdown -= 1

            return self._data_response

    async def send_reset_signal(self, show_me=False):
        """
        Sends a reset signal to the device which will reset the Lua virtual
        machine.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(bytearray(b"\x04"), show_me=show_me)

    async def send_break_signal(self, show_me=False):
        """
        Sends a break signal to the device which will break any currently
        executing Lua script.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(bytearray(b"\x03"), show_me=show_me)
