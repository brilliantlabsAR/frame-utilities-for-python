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
from frameutils import Frame


async def main():
    # the with statement handles the connection and disconnection to Frame
    async with Frame() as f:
        # you can access the lower-level bluetooth connection via f.bluetooth, although you shouldn't need to do this often
        print(f"Connected: {f.bluetooth.is_connected()}")

        # let's get the current battery level
        print(f"Frame battery: {await f.get_battery_level()}%")

        # let's write (or overwrite) the file greeting.txt with "Hello world".
        # You can provide a bytes object or convert a string with .encode()
        await f.files.write_file("greeting.txt", b"Hello world")

        # And now we read that file back.
        # Note that we should convert the bytearray to a string via the .decode() method.
        print((await f.files.read_file("greeting.txt")).decode())
        
        # run_lua will automatically handle scripts that are too long for the MTU, so you don't need to worry about it.
        # It will also automatically handle responses that are too long for the MTU automatically.
        await f.run_lua("frame.display.text('Hello world', 50, 100);frame.display.show()")

        # evaluate is equivalent to f.run_lua("print(\"1+2\"), await_print=True)
        # It will also automatically handle responses that are too long for the MTU automatically.
        print(await f.evaluate("1+2"))

        # take a photo and save to disk
        await f.camera.save_photo("frame-test-photo.jpg")

    print("disconnected")



asyncio.run(main())

```

## Tests

To run the unit tests, ensure you have pytest installed:

```sh
pip3 install pytest
```

With an unconnected Frame device in range, run:

```sh
python3 -m pytest tests/test_bluetooth.py
python3 -m pytest tests/test_files.py
```