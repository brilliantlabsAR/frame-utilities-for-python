import asyncio
import time
from frameutils import Bluetooth


def disconnect_handler():
    print("Disconnected!")


def data_received_handler(data: bytearray):
    print(data.decode(), end="", flush=True)


async def main():
    bluetooth = Bluetooth()
    await bluetooth.connect(disconnect_handler, data_received_handler)
    await bluetooth.send_lua("print('hi')")
    time.sleep(1)
    await bluetooth.send_lua("print(5+6)")
    time.sleep(1)

    while True:
        pass

    await bluetooth.disconnect()


asyncio.run(main())
