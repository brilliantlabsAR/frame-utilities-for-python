import asyncio

from frameutils import Bluetooth


def disconnect_handler():
    print("Disconnected user callback!")


def lua_response_handler(string):
    print(f"Response: {string}")


def data_response_handler(data):
    print(f"Response: {data}")


async def main():
    bluetooth = Bluetooth()

    print(bluetooth.is_connected())

    await bluetooth.connect(
        lua_response_handler,
        data_response_handler,
    )

    print(bluetooth.is_connected())
    print(bluetooth.max_lua_payload())
    print(bluetooth.max_data_payload())

    print(await bluetooth.send_lua("print('hello')", show_me=True, wait=True))
    await asyncio.sleep(1)

    print(await bluetooth.send_lua("print('world')", wait=True))
    await asyncio.sleep(1)

    await bluetooth.send_lua("a = 5")
    await asyncio.sleep(1)

    print(await bluetooth.send_lua("print(a + 6)", wait=True))
    print(await bluetooth.send_lua("print(6 + 6)", wait=True))
    await asyncio.sleep(3)

    await bluetooth.disconnect()

    print(bluetooth.is_connected())
    await bluetooth.connect()

    print(await bluetooth.send_lua("print('hi again')", show_me=True, wait=True))
    await asyncio.sleep(1)

    await bluetooth.send_data(bytearray(b"abc"), show_me=True)
    await asyncio.sleep(1)

    await bluetooth.disconnect()

    bluetooth = Bluetooth()
    await bluetooth.connect()

    print(await bluetooth.send_lua("print('hello world')", wait=True))
    print(await bluetooth.send_lua("print(1 + 2)", wait=False))
    await asyncio.sleep(1)

    await bluetooth.disconnect()


asyncio.run(main())
