import asyncio
from typing import Optional
from .bluetooth import Bluetooth
from .files import FrameFileSystem
import random
import re

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

    async def evaluate(self, lua_expression: str) -> str:
        """Evaluates a lua expression on the device and return the result."""
        
        return await self.run_lua(f"prntLng({lua_expression})", await_print=True)

    async def run_lua(self, lua_string: str, await_print: bool = False) -> Optional[str]:
        """Run a Lua string on the device, automatically determining the appropriate method based on length."""
        
        # replace any print() calls with prntLng() calls
        # TODO: this is a dirty hack and instead we should fix the implementation of print() in the Frame
        lua_string = re.sub(r'\bprint\(', 'prntLng(', lua_string)
        
        if len(lua_string) <= self.bluetooth.max_lua_payload():
            return await self.bluetooth.send_lua(lua_string, await_print=await_print)
        else:
            return await self.send_long_lua(lua_string, await_print=await_print)

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
    
    async def inject_library_function(self, name: str, function: str):
        """
        Inject a function into the global environment of the device.
        """
        await self.ensure_connected()
        
        exists = await self.bluetooth.send_lua(f"print({name} ~= nil)", await_print=True)
        if (self.bluetooth._print_debugging):
                print(f"Function {name} exists: {exists}")
        if (exists != "true"):
            # function does not yet exist, so let's see if the file for it does
            exists = await self.files.file_exists(f"/lib/{name}.lua")
            if (self.bluetooth._print_debugging):
                print(f"File /lib/{name}.lua exists: {exists}")

            if (exists):
                response = await self.bluetooth.send_lua(f"require(\"lib/{name}\");print(\"l\")", await_print=True)
                if response == "l":
                    return
            
            if (self.bluetooth._print_debugging):
                print(f"Writing file /lib/{name}.lua")
            await self.files.write_file(f"/lib/{name}.lua", function.encode(), checked=True)
            
            if (self.bluetooth._print_debugging):
                print(f"Requiring lib/{name}")
            response = await self.bluetooth.send_lua(f"require(\"lib/{name}\");print(\"l\")", await_print=True)
            if response != "l":
                raise Exception("Error injecting library function")
            
    async def inject_all_library_functions(self):
        """
        Inject all library functions into the global environment of the device.
        """
        from .library_functions import library_print_long
        
        await self.ensure_connected()
        response = await self.bluetooth.send_lua("frame.file.mkdir(\"lib\");print(\"c\")", await_print=True)
        if response == "c":
            if (self.bluetooth._print_debugging):
                print("Created lib directory")
        else:
            if (self.bluetooth._print_debugging):
                print("Did not create lib directory: "+response)
        await self.inject_library_function("prntLng", library_print_long)