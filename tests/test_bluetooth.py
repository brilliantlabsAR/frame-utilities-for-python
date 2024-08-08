import unittest
import asyncio
import sys

sys.path.append("..")
from src.frameutils import Bluetooth


class TestBluetooth(unittest.IsolatedAsyncioTestCase):
    async def test_connect_disconnect(self):
        b = Bluetooth()

        self.assertFalse(b.is_connected())

        device_address = await b.connect()
        self.assertTrue(b.is_connected())

        await b.disconnect()
        self.assertFalse(b.is_connected())

        with self.assertRaises(Exception):
            await b.connect(address="78D97B6B-244B-AC86-047F-BBF72ADEB1F6")

        await b.connect(address=device_address)
        await b.disconnect()

    async def test_send_lua(self):
        b = Bluetooth()
        await b.connect()

        self.assertEqual(await b.send_lua("print('hi')", await_print=True), "hi")

        self.assertIsNone(await b.send_lua("print('hi')"))
        await asyncio.sleep(0.1)

        with self.assertRaises(Exception):
            await b.send_lua("a = 1", await_print=True)

        await b.disconnect()

    async def test_send_data(self):
        b = Bluetooth()
        await b.connect()

        await b.send_lua(
            "frame.bluetooth.receive_callback((function(d)frame.bluetooth.send(d)end))"
        )

        self.assertEqual(await b.send_data(b"test", await_data=True), b"test")

        self.assertIsNone(await b.send_data(b"test"))
        await asyncio.sleep(0.1)

        await b.send_lua("frame.bluetooth.receive_callback(nil)")

        with self.assertRaises(Exception):
            await b.send_data(b"test", await_data=True)

        await b.disconnect()

    async def test_mtu(self):
        b = Bluetooth()
        await b.connect()

        max_lua_length = b.max_lua_payload()
        max_data_length = b.max_data_payload()

        self.assertEqual(max_lua_length, max_data_length + 1)

        with self.assertRaises(Exception):
            await b.send_lua("a" * max_lua_length + 1)

        with self.assertRaises(Exception):
            await b.send_data(bytearray(b"a" * max_data_length + 1))

        await b.disconnect()

    async def test_upload_from_file(self):
        b = Bluetooth()
        await b.connect()

        self.assertIsNone(await b.upload_file("./tests/main.lua", "main.lua"))

        self.assertIsNone(await b.send_lua("require('main')"))
        await asyncio.sleep(1)

        await b.disconnect()

    async def test_upload_from_string(self):
        b = Bluetooth()
        await b.connect()

        lua_file = """
        while true do
            frame.display.text('Hello world!', 10, 10)
            frame.display.show()
            frame.sleep(1)

            frame.display.text('Test was run from string', 10, 10, { color = 'GREEN' })
            frame.display.show()
            frame.sleep(1)
        end
        """

        self.assertIsNone(await b.upload_file(lua_file, "main.lua"))

        self.assertIsNone(await b.send_lua("require('main')"))
        await asyncio.sleep(1)

        await b.disconnect()


if __name__ == "__main__":
    unittest.main()
