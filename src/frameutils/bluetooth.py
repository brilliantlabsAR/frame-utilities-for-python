import asyncio
from typing import Optional, Callable, List, Tuple, Dict, Any

from bleak import BleakClient, BleakScanner, BleakError

_FRAME_DATA_PREFIX = 1
_FRAME_LONG_TEXT_PREFIX = 10
_FRAME_LONG_TEXT_END_PREFIX = 11
_FRAME_LONG_DATA_PREFIX = 1
_FRAME_LONG_DATA_END_PREFIX = 2

class Bluetooth:
    """
    Frame bluetooth class for managing a connection and transferring data to and
    from the device.
    """

    _SERVICE_UUID: str = "7a230001-5475-a6a4-654c-8431f6ad49c4"
    _TX_CHARACTERISTIC_UUID: str = "7a230002-5475-a6a4-654c-8431f6ad49c4"
    _RX_CHARACTERISTIC_UUID: str = "7a230003-5475-a6a4-654c-8431f6ad49c4"
    
    def __init__(self):
        self._client: Optional[BleakClient] = None
        self._print_response: str = ""
        self._ongoing_print_response: Optional[bytearray] = None
        self._ongoing_print_response_chunk_count: Optional[int] = None
        self._ongoing_data_response: Optional[bytearray] = None
        self._ongoing_data_response_chunk_count: Optional[int] = None
        self._data_response: bytearray = bytearray()
        self._tx_characteristic: Optional[Any] = None
        self._user_data_response_handler: Callable[[bytes], None] = lambda _: None
        self._user_disconnect_handler: Callable[[], None] = lambda: None
        self._user_print_response_handler: Callable[[str], None] = lambda _: None
        self._print_debugging: bool = False
        self._default_timeout: float = 10.0
        self._data_response_event: asyncio.Event = asyncio.Event()
        self._print_response_event: asyncio.Event = asyncio.Event()
        self._max_receive_buffer: int = 10 * 1024 * 1024

    def _disconnect_handler(self, _: Any) -> None:
        self._user_disconnect_handler()
        self.__init__()

    async def _notification_handler(self, _: Any, data: bytearray) -> None:
        if data[0] == _FRAME_LONG_TEXT_PREFIX:
            # start of long printed data from prntLng() function
            if self._ongoing_print_response is None or self._ongoing_print_response_chunk_count is None:
                self._ongoing_print_response = bytearray()
                self._ongoing_print_response_chunk_count = 0
                if self._print_debugging:
                    print("starting receiving new long printed data")
            self._ongoing_print_response += data[1:]
            self._ongoing_print_response_chunk_count += 1
            if self._print_debugging:
                print(f"received chunk #{self._ongoing_print_response_chunk_count}: "+data[1:].decode())
            if len(self._ongoing_print_response) > self._max_receive_buffer:
                raise Exception(f"buffered received long printed text is more than {self._max_receive_buffer} bytes")
            
        elif data[0] == _FRAME_LONG_TEXT_END_PREFIX:
            # end of long printed data from prntLng() function
            total_expected_chunk_count_as_string: str = data[1:].decode()
            if len(total_expected_chunk_count_as_string) > 0:
                total_expected_chunk_count: int = int(total_expected_chunk_count_as_string)
                if self._print_debugging:
                    print(f"received final chunk count: {total_expected_chunk_count}")
                if self._ongoing_print_response_chunk_count != total_expected_chunk_count:
                    raise Exception(f"chunk count mismatch in long received data (expected {total_expected_chunk_count}, got {self._ongoing_print_response_chunk_count})")
            self._print_response = self._ongoing_print_response.decode()
            self._print_response_event.set()
            self._ongoing_print_response = None
            self._ongoing_print_response_chunk_count = None
            if self._print_debugging:
                print("finished receiving long printed data: "+self._print_response)
            self._user_print_response_handler(self._print_response)
            
        elif data[0] == _FRAME_DATA_PREFIX and data[1] == _FRAME_LONG_DATA_PREFIX:
            # start of long raw data from frame.bluetooth.send("\001"..data)
            if self._ongoing_data_response is None or self._ongoing_data_response_chunk_count is None:
                self._ongoing_data_response = bytearray()
                self._ongoing_data_response_chunk_count = 0
                self._data_response = None
                if self._print_debugging:
                    print("starting receiving new long raw data")
            self._ongoing_data_response += data[2:]
            self._ongoing_data_response_chunk_count += 1
            if self._print_debugging:
                print(f"received data chunk #{self._ongoing_data_response_chunk_count}: {len(data[2:])} bytes")
            if len(self._ongoing_data_response) > self._max_receive_buffer:
                raise Exception(f"buffered received long raw data is more than {self._max_receive_buffer} bytes")
            
        elif data[0] == _FRAME_DATA_PREFIX and data[1] == _FRAME_LONG_DATA_END_PREFIX:
            # end of long raw data from frame.bluetooth.send("\002"..chunkCount)
            total_expected_chunk_count_as_string: str = data[2:].decode()
            if len(total_expected_chunk_count_as_string) > 0:
                total_expected_chunk_count: int = int(total_expected_chunk_count_as_string)
                if self._print_debugging:
                    print(f"received final data chunk count: {total_expected_chunk_count}")
                if self._ongoing_data_response_chunk_count != total_expected_chunk_count:
                    raise Exception(f"chunk count mismatch in long received data (expected {total_expected_chunk_count}, got {self._ongoing_data_response_chunk_count})")
            self._data_response = self._ongoing_data_response
            self._data_response_event.set()
            self._ongoing_data_response = None
            self._ongoing_data_response_chunk_count = None
            if self._print_debugging:
                if self._data_response is None:
                    print("finished receiving long raw data: No bytes")
                else:
                    print(f"finished receiving long raw data: {len(self._data_response)} bytes)")
            self._user_data_response_handler(self._data_response)
            
        elif data[0] == _FRAME_DATA_PREFIX:
            # received single chunk raw data from frame.bluetooth.send(data)
            if self._print_debugging:
                print(f"received data: {len(data[1:])} bytes")
            self._data_response = data[1:]
            self._data_response_event.set()
            self._user_data_response_handler(data[1:])
            
        else:
            # received single chunk printed text from print()
            self._print_response = data.decode()
            self._print_response_event.set()
            self._user_print_response_handler(data.decode())

    async def connect(
        self,
        print_response_handler: Callable[[str], None] = lambda _: None,
        data_response_handler: Callable[[bytes], None] = lambda _: None,
        disconnect_handler: Callable[[], None] = lambda: None,
    ) -> None:
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

        # returns list of (BLEDevice, AdvertisementData)
        devices: Dict[str, Tuple[Any, Any]] = await BleakScanner.discover(3, return_adv=True)

        filtered_list: List[Tuple[Any, Any]] = []
        for d in devices.values():
            if self._SERVICE_UUID in d[1].service_uuids:
                filtered_list.append(d)

        # connect to closest device
        filtered_list.sort(key=lambda x: x[1].rssi, reverse=True)
        try:
            device: Any = filtered_list[0][0]

        except IndexError:
            raise Exception("No Frame devices found")

        self._client = BleakClient(
            device,
            disconnected_callback=self._disconnect_handler,
        )

        try:
            await self._client.connect()

            await self._client.start_notify(
                self._RX_CHARACTERISTIC_UUID,
                self._notification_handler,
            )
        except BleakError as e:
            raise Exception("Device needs to be re-paired: "+str(e))

        service: Any = self._client.services.get_service(
            self._SERVICE_UUID,
        )

        self._tx_characteristic = service.get_characteristic(
            self._TX_CHARACTERISTIC_UUID,
        )

    async def disconnect(self) -> None:
        """
        Disconnects from the device.
        """
        await self._client.disconnect()
        self._disconnect_handler(None)

    def is_connected(self) -> bool:
        """
        Returns `True` if the device is connected. `False` otherwise.
        """
        try:
            return self._client.is_connected
        except AttributeError:
            return False

    def max_lua_payload(self) -> int:
        """
        Returns the maximum length of a Lua string which may be transmitted.
        """
        try:
            return self._client.mtu_size - 3
        except AttributeError:
            return 0

    def max_data_payload(self) -> int:
        """
        Returns the maximum length of a raw bytearray which may be transmitted.
        """
        try:
            return self._client.mtu_size - 4
        except AttributeError:
            return 0
    
    @property
    def default_timeout(self) -> float:
        """
        Gets the default timeout value in seconds
        """
        return self._default_timeout

    @default_timeout.setter
    def default_timeout(self, value: float) -> None:
        """
        Sets the default timeout value in seconds
        """
        if value < 0:
            raise ValueError("default_timeout must be a non-negative float")
        self._default_timeout = value
    
    def set_print_debugging(self, value: bool) -> None:
        """
        Sets whether to print debugging information when sending data.
        """
        self._print_debugging = value

    async def _transmit(self, data: bytearray, show_me: bool = False) -> None:
        if show_me or self._print_debugging:
            print(data)  # TODO make this print nicer

        if len(data) > self._client.mtu_size - 3:
            raise Exception("payload length is too large")

        await self._client.write_gatt_char(self._tx_characteristic, data)

    async def send_lua(self, string: str, show_me: bool = False, await_print: bool = False, timeout: Optional[float] = None) -> Optional[str]:
        """
        Sends a Lua string to the device. The string length must be less than or
        equal to `max_lua_payload()`.

        If `await_print=True`, the function will block until a Lua print()
        occurs, or a timeout.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(string.encode(), show_me=show_me)

        if await_print:
            return await self.wait_for_print(timeout)
        
    async def wait_for_print(self, timeout: Optional[float] = None) -> str:
        """
        Waits until a Lua print() occurs, with a max timeout in seconds
        """
        if timeout is None:
            timeout = self._default_timeout

        self._print_response_event.clear()

        try:
            await asyncio.wait_for(self._print_response_event.wait(), timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Frame didn't respond with printed data (from print() or prntLng()) within {timeout} seconds")

        return self._print_response
    
    async def wait_for_data(self, timeout: Optional[float] = None) -> bytes:
        """
        Waits until data has been received from the device, with a max timeout in seconds
        """
        if timeout is None:
            timeout = self._default_timeout

        self._data_response_event.clear()

        try:
            await asyncio.wait_for(self._data_response_event.wait(), timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Frame didn't respond with data (from frame.bluetooth.send(data)) within {timeout} seconds")
        return bytes(self._data_response)

    async def send_data(self, data: bytearray, show_me: bool = False, await_data: bool = False) -> Optional[bytes]:
        """
        Sends raw data to the device. The payload length must be less than or
        equal to `max_data_payload()`.

        If `await_data=True`, the function will block until a data response
        occurs, or a timeout.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        await self._transmit(bytearray(b"\x01") + data, show_me=show_me)

        if await_data:
            return await self.wait_for_data()

    async def send_reset_signal(self, show_me: bool = False) -> None:
        """
        Sends a reset signal to the device which will reset the Lua virtual
        machine.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        if not self.is_connected():
            await self.connect()
        await self._transmit(bytearray(b"\x04"), show_me=show_me)

    async def send_break_signal(self, show_me: bool = False) -> None:
        """
        Sends a break signal to the device which will break any currently
        executing Lua script.

        If `show_me=True`, the exact bytes send to the device will be printed.
        """
        if not self.is_connected():
            await self.connect()
        await self._transmit(bytearray(b"\x03"), show_me=show_me)