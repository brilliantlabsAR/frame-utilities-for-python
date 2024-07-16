import asyncio

class FrameFileSystem:
    """Helpers for accessing the Frame filesystem."""

    lua_escape_table = {
        b"\\" : b"\\\\",
        b"\n" : b"\\n",
        b"\r" : b"\\r",
        b"\t" : b"\\t",
        b"\"" : b"\\\"",
        b"[" : b"\\[",
        b"]" : b"\\]",
    }
    
    frame_connection = None
    
    def __init__(self, frame_connection):
        self.frame_connection = frame_connection
    
    async def write_file(self, path: str, data: bytes, checked: bool = False):
        """Write a file to the device."""
        for char, escape in self.lua_escape_table.items():
            data = data.replace(char, escape)
        
        response = await self.frame_connection.send_lua(
            f"w=frame.file.open(\"{path}\",\"write\")" +
            (";print(\"o\")" if checked else ""), await_print=checked)
        
        if checked and response != "o":
            raise Exception("Couldn't open file for writing")
        
        current_index = 0
        chunk_index = 0
        while current_index < len(data):
            max_payload = self.frame_connection.max_lua_payload() - len("w:write(\"\")")
            if checked:
                max_payload -= len(f";print({chunk_index})")
            next_chunk_length = min(len(data) - current_index, max_payload)
            if (next_chunk_length == 0):
                break
            
            # offset if on an escape character
            while (data[current_index + next_chunk_length - 1] == b"\\" and next_chunk_length > 0):
                next_chunk_length -= 1
                
            if next_chunk_length <= 0:
                raise Exception("MTU too small to write file, or escape character at end of chunk")
            
            chunk = data[current_index:current_index + next_chunk_length]
            response = await self.frame_connection.send_lua(
                f"w:write(\"{chunk.decode()}\")" +
                (f";print({chunk_index})" if checked else ""), await_print=checked)
            
            if checked and response != str(chunk_index):
                raise Exception("Error writing file in range " + str(current_index) + " to " + str(current_index + next_chunk_length)+". Received: " + response)
    
            
            chunk_index += 1
            current_index += next_chunk_length
            
        response = await self.frame_connection.send_lua("w:close();print(\"c\")", await_print=True)
        if response != "c":
            raise Exception("Error closing file")
        
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists on the device."""
        response_from_opening = await self.frame_connection.send_lua(
            f"r=frame.file.open(\"{path}\",\"read\");print(\"o\");r:close()", await_print=True)
        return response_from_opening == "o"
    
    async def delete_file(self, path: str) -> bool:
        """Delete a file on the device.
        Returns True if the file was deleted, False if it didn't exist or failed to delete."""
        response = await self.frame_connection.send_lua(f"frame.file.remove(\"{path}\");print(\"d\")", await_print=True)
        return response == "d"