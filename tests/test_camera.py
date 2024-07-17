import os
import unittest
import asyncio
import sys
import time

sys.path.append("..")
from src.frameutils import Frame

class TestCamera(unittest.IsolatedAsyncioTestCase):
    async def test_get_photo(self):
        """
        Test taking a photo
        """
        async with Frame() as f:
            photo = await f.camera.take_photo()
            self.assertGreater(len(photo), 2000)
            
    async def test_save_photo_to_disk(self):
        """
        Test saving a photo to disk
        """
        async with Frame() as f:
            await f.camera.save_photo("test_photo.jpg")
            self.assertTrue(os.path.exists("test_photo.jpg"))
            self.assertGreater(os.path.getsize("test_photo.jpg"), 2000)
            os.remove("test_photo.jpg")
            
    async def test_photo_with_autofocus_options(self):
        """
        Test taking a photo with various autofocus options
        """
        async with Frame() as f:

            startTime = time.time()
            photo = await f.camera.take_photo(autofocus_seconds=None)
            endTime = time.time()
            self.assertGreater(len(photo), 2000)
            timeToTakePhotoWithoutAutoFocus = endTime - startTime

            startTime = time.time()
            photo = await f.camera.take_photo(autofocus_seconds=1, autofocus_type=f.camera.AUTOFOCUS_TYPE_SPOT)
            endTime = time.time()
            self.assertGreater(len(photo), 2000)
            timeToTakePhotoWithAutoFocus1Sec = endTime - startTime

            self.assertGreater(timeToTakePhotoWithAutoFocus1Sec, timeToTakePhotoWithoutAutoFocus)
            
            startTime = time.time()
            photo = await f.camera.take_photo(autofocus_seconds=3, autofocus_type=f.camera.AUTOFOCUS_TYPE_CENTER_WEIGHTED)
            endTime = time.time()
            self.assertGreater(len(photo), 2000)
            timeToTakePhotoWithAutoFocus3Sec = endTime - startTime

            self.assertGreater(timeToTakePhotoWithAutoFocus3Sec, timeToTakePhotoWithAutoFocus1Sec)

    async def test_photo_with_quality_options(self):
        """
        Test taking a photo with various quality options
        """
        async with Frame() as f:
            photo = await f.camera.take_photo(quality=f.camera.LOW_QUALITY)
            low_quality_size = len(photo)
            self.assertGreater(low_quality_size, 2000)

            photo = await f.camera.take_photo(quality=f.camera.MEDIUM_QUALITY)
            medium_quality_size = len(photo)
            self.assertGreater(medium_quality_size, low_quality_size)
            
            photo = await f.camera.take_photo(quality=f.camera.HIGH_QUALITY)
            high_quality_size = len(photo)
            self.assertGreater(high_quality_size, medium_quality_size)

            photo = await f.camera.take_photo(quality=f.camera.FULL_QUALITY)
            full_quality_size = len(photo)
            self.assertGreater(full_quality_size, high_quality_size)


if __name__ == "__main__":
    unittest.main()
