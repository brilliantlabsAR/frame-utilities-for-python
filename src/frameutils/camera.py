from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from exif import Image
from datetime import datetime

if TYPE_CHECKING:
    from .frame import Frame

class Camera:
    """Helpers for working with the Frame camera."""

    frame: "Frame" = None
    
    LOW_QUALITY = 10
    MEDIUM_QUALITY = 25
    HIGH_QUALITY = 50
    FULL_QUALITY = 100
    
    AUTOFOCUS_TYPE_SPOT = "SPOT"
    AUTOFOCUS_TYPE_AVERAGE = "AVERAGE"
    AUTOFOCUS_TYPE_CENTER_WEIGHTED = "CENTER_WEIGHTED"
    
    _auto_sleep = True
    _auto_process_photo = True
    
    def __init__(self, frame: "Frame"):
        self.frame = frame
        
    @property
    def auto_sleep(self) -> bool:
        """If true, the camera will automatically sleep after taking a photo."""
        return self._auto_sleep

    @auto_sleep.setter
    def auto_sleep(self, value: bool):
        self._auto_sleep = value
        
    @property
    def auto_process_photo(self) -> bool:
        """If true, the camera will automatically process the photo to correct rotation and add metadata"""
        return self._auto_process_photo
    
    @auto_process_photo.setter
    def auto_process_photo(self, value: bool):
        self._auto_process_photo = value
    
    async def take_photo(self, autofocus_seconds: Optional[int] = 3, quality: int = MEDIUM_QUALITY, autofocus_type: str = AUTOFOCUS_TYPE_AVERAGE) -> bytes:
        """Take a photo with the camera.
        If autofocus_seconds is provided, the camera will attempt to focus for the specified number of seconds.
        Quality is LOW_QUALITY (10), MEDIUM_QUALITY (25), HIGH_QUALITY (50), or FULL_QUALITY (100).
        """
        # TODO: Either camera sleep and wake don't work correctly or they're not properly documented, this doesn't work for now
        #if self.auto_sleep:
        #    await self.frame.bluetooth.send_lua("frame.camera.wake()")
        #    await asyncio.sleep(0.1)
        
        await self.frame.bluetooth.send_lua(f"cameraCaptureAndSend({quality},{autofocus_seconds or 'nil'},{autofocus_type})")
        image_buffer = await self.frame.bluetooth.wait_for_data()
        
        #if self.auto_sleep:
        #    await self.frame.bluetooth.send_lua("frame.camera.sleep()")
        
        if image_buffer is None or len(image_buffer) == 0:
            raise Exception("Failed to get photo")
        
        if self.auto_process_photo:
            image_buffer = self.process_photo(image_buffer, quality, autofocus_type)
        return image_buffer
    
    async def save_photo(self, filename: str, autofocus_seconds: Optional[int] = 3, quality: int = MEDIUM_QUALITY, autofocus_type: str = AUTOFOCUS_TYPE_AVERAGE):
        image_buffer = await self.take_photo(autofocus_seconds, quality, autofocus_type)

        with open(filename, "wb") as f:
            f.write(image_buffer)
            
    def process_photo(self, image_buffer: bytes, quality: int, autofocus_type: str) -> bytes:
        """Process a photo to correct rotation and add metadata"""
        image = Image(image_buffer)
        image.orientation = 8
        image.make = "Brilliant Labs"
        image.model = "Frame"
        image.software = "Frame Python SDK"
        if autofocus_type == self.AUTOFOCUS_TYPE_AVERAGE:
            image.metering_mode = 1
        elif autofocus_type == self.AUTOFOCUS_TYPE_CENTER_WEIGHTED:
            image.metering_mode = 2
        elif autofocus_type == self.AUTOFOCUS_TYPE_SPOT:
            image.metering_mode = 3
        image.datetime_original = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        return image.get_file()