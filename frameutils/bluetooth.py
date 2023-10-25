import asyncio
import sys

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

SERVICE_UUID = "7a230001-5475-a6a4-654c-8431f6ad49c4"
TX_CHARACTERISTIC_UUID = "7a230002-5475-a6a4-654c-8431f6ad49c4"
RX_CHARACTERISTIC_UUID = "7a230003-5475-a6a4-654c-8431f6ad49c4"


class Bluetooth:
    def _service_filter(self, _: BLEDevice, adv: AdvertisementData):
        return SERVICE_UUID in adv.service_uuids

    def _disconnect_handler(self, _: BleakClient):
        self._user_disconnect_handler()

    def _data_received_handler(self, _: BleakGATTCharacteristic, data: bytearray):
        self._user_data_received_handler(data)

    async def send_lua(self, string: str):
        await self._client.write_gatt_char(
            self._transmit_characteristic, string.encode()
        )

    async def send_data(self, bytes: bytearray):
        pass

    async def disconnect(self):
        await self._client.disconnect()

    async def connect(
        self, user_disconnect_handler: callable, user_data_received_handler: callable
    ):
        self._user_disconnect_handler = user_disconnect_handler
        self._user_data_received_handler = user_data_received_handler

        device = await BleakScanner.find_device_by_filter(self._service_filter)
        if device is None:
            return None

        self._client = BleakClient(
            device, disconnected_callback=self._disconnect_handler
        )

        await self._client.connect()

        await self._client.start_notify(
            RX_CHARACTERISTIC_UUID, self._data_received_handler
        )

        service = self._client.services.get_service(SERVICE_UUID)

        self._transmit_characteristic = service.get_characteristic(
            TX_CHARACTERISTIC_UUID
        )
