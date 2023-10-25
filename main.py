import asyncio
from frameutils import Bluetooth


def disconnect_handler():
    print("Disconnected user callback!")


async def main():
    bluetooth = Bluetooth()
    await bluetooth.connect()

    print(await bluetooth.send_lua("print('hello')"))
    await asyncio.sleep(1)

    print(await bluetooth.send_lua("print('world')"))
    await asyncio.sleep(1)

    print(await bluetooth.send_lua("print(4 + 6)"))
    print(await bluetooth.send_lua("print(6 + 6)"))
    await asyncio.sleep(3)

    await bluetooth.disconnect()


asyncio.run(main())
