from __future__ import annotations
import asyncio
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .frame import Frame

class FrameFileSystem:
    """Helpers for accessing the Frame filesystem."""
    
    frame: "Frame" = None
    
    def __init__(self, frame: "Frame"):
        self.frame = frame
    
    async def write_file(self, path: str, data: bytes, checked: bool = False) -> None:
        """Write a file to the device."""
        
        response = await self.frame.bluetooth.send_lua(
            f"w=frame.file.open(\"{path}\",\"write\")" +
            (";print(\"o\")" if checked else ""), await_print=checked)
        if checked and response != "o":
            raise Exception(f"Couldn't open file \"{path}\" for writing: {response}")
        response = await self.frame.bluetooth.send_lua(
            f"frame.bluetooth.receive_callback((function(d)w:write(d)end))" +
            (";print(\"c\")" if checked else ""), await_print=checked)
        if checked and response != "c":
            raise Exception(f"Couldn't register callback for writing to file \"{path}\": {response}")
        
        current_index = 0
        while current_index < len(data):
            max_payload = self.frame.bluetooth.max_data_payload()-1
            next_chunk_length = min(len(data) - current_index, max_payload)
            if (next_chunk_length == 0):
                break
            
            # offset if on an escape character
            #while (data[current_index + next_chunk_length - 1] == 92 and next_chunk_length > 0):
            #    next_chunk_length -= 1
            
            if next_chunk_length <= 0:
                raise Exception("MTU too small to write file, or escape character at end of chunk")
            
            chunk = data[current_index:current_index + next_chunk_length]
            await self.frame.bluetooth.send_data(chunk)
            
            current_index += next_chunk_length
            if current_index < len(data):
                await asyncio.sleep(0.1)
            
        response = await self.frame.bluetooth.send_lua("w:close();print(\"c\")", await_print=checked)
        if checked and response != "c":
            raise Exception("Error closing file")
        response = await self.frame.bluetooth.send_lua(
            f"frame.bluetooth.receive_callback(nil)" +
            (";print(\"c\")" if checked else ""), await_print=checked)
        if checked and response != "c":
            raise Exception(f"Couldn't remove callback for writing to file \"{path}\"")
        
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists on the device."""
        response_from_opening = await self.frame.bluetooth.send_lua(
            f"r=frame.file.open(\"{path}\",\"read\");print(\"o\");r:close()", await_print=True)
        return response_from_opening == "o"
    
    async def delete_file(self, path: str) -> bool:
        """Delete a file on the device.
        Returns True if the file was deleted, False if it didn't exist or failed to delete."""
        response = await self.frame.bluetooth.send_lua(f"frame.file.remove(\"{path}\");print(\"d\")", await_print=True)
        return response == "d"
    
    async def read_file(self, path: str) -> bytes:
        """Read a file from the device."""
        await self.frame.run_lua(f"printCompleteFile(\"{path}\")")
        result : bytes = await self.frame.bluetooth.wait_for_data()
        return result.strip()
    