# Frame Utilities – for Python

Useful utilities for your Brilliant Frame such as a Bluetooth communication library, and font generation tools.

## Install

```sh
pip3 install frameutils
```

## Bluetooth communication library

As simple as:

```python
import asyncio
from frameutils import Bluetooth


async def main():
    bluetooth = Bluetooth()
    await bluetooth.connect()

    print(await bluetooth.send_lua("print('hello world')", wait=True))
    print(await bluetooth.send_lua("print(1 + 2)", wait=True))

    await bluetooth.disconnect()


asyncio.run(main())

```