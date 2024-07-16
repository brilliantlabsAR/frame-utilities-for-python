import asyncio
from typing import Optional
from .bluetooth import Bluetooth
from .files import FrameFileSystem
import random

class Frame:
    """Entrypoint to the Frame SDK"""
    
    bluetooth = None
    files = None
    
    def __init__(self):
        self.bluetooth = Bluetooth()
        self.files = FrameFileSystem(self.bluetooth)
        
    async def ensure_connected(self):
        """Ensure the Frame is connected."""
        if not self.bluetooth.is_connected():
            await self.bluetooth.connect()

    async def send_long_lua(self, string: str, await_print: bool = False) -> Optional[str]:
        """
        Sends a Lua string to the device that is longer that the MTU limit and thus
        must be sent via writing to a file and requiring that file.
        
        If `await_print=True`, the function will block until a Lua print()
        occurs, or a timeout.
        """
        
        await self.ensure_connected()
        
        # we use a random name here since require() only works once per file.
        # TODO: confirm that the Frame implementation of Lua actually works this way.  If not, we don't need to randomize the name.
        random_name = ''.join(chr(ord('a')+random.randint(0,25)) for _ in range(4))
        
        await self.files.write_file(f"/{random_name}.lua", string.encode(), checked=True)
        if await_print:
            response = await self.bluetooth.send_lua(f"require(\"{random_name}\")", await_print=True)
        else:
            response = await self.bluetooth.send_lua(f"require(\"{random_name}\");print('done')", await_print=True)
            if response != "done":
                raise Exception("require() did not return 'done'")
            response = None
        await self.files.delete_file(f"/{random_name}.lua")
        return response
    
    