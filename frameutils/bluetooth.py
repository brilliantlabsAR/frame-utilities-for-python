import asyncio
import sys
import os

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.uuids import register_uuids


class Bluetooth:
    _SERVICE_UUID = "7a230001-5475-a6a4-654c-8431f6ad49c4"
    _TX_CHARACTERISTIC_UUID = "7a230002-5475-a6a4-654c-8431f6ad49c4"
    _RX_CHARACTERISTIC_UUID = "7a230003-5475-a6a4-654c-8431f6ad49c4"

    def __init__(self):
        self._awaiting_response = False
        self._response_data = bytearray()

    def _filter_uuid(self, _: BLEDevice, adv: AdvertisementData):
        return self._SERVICE_UUID in adv.service_uuids

    def _disconnect_handler(self, _: BleakClient):
        self._user_disconnect_handler()

    async def _notification_handler(self, _: BleakGATTCharacteristic, data: bytearray):
        self._awaiting_response = False
        self._response_data = data

    async def connect(self, disconnect_handler: callable = lambda: None):
        self._user_disconnect_handler = disconnect_handler

        device = await BleakScanner.find_device_by_filter(self._filter_uuid)

        if device is None:
            raise Exception("no Frame devices found")

        self._client = BleakClient(
            device,
            disconnected_callback=self._disconnect_handler,
        )

        await self._client.connect()

        await self._client.start_notify(
            self._RX_CHARACTERISTIC_UUID,
            self._notification_handler,
        )

        service = self._client.services.get_service(self._SERVICE_UUID)

        self._tx_characteristic = service.get_characteristic(
            self._TX_CHARACTERISTIC_UUID
        )

    async def send_lua(self, string: str):
        await self._client.write_gatt_char(self._tx_characteristic, string.encode())

        self._awaiting_response = True
        countdown = 1000

        while self._awaiting_response:
            await asyncio.sleep(0.001)
            if countdown == 0:
                raise Exception("Frame device didn't respond")
            countdown -= 1

        return self._response_data.decode()

    async def disconnect(self):
        await self._client.disconnect()
