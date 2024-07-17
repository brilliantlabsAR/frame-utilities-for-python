import unittest
import asyncio
import sys

sys.path.append("..")
from src.frameutils import Frame

class TestFiles(unittest.IsolatedAsyncioTestCase):
    async def test_write_long_file(self):
        """
        Test writing a long file to the device.
        """
        async with Frame() as f:
            content = ("Testing:\n"+("test1... " * 200) + "\nTesting 2:\n" + ("test2\n" * 100)).encode()
            await f.files.write_file("test.txt", content, checked=True)
            actual_content = await f.files.read_file("test.txt")
            self.assertEqual(content.decode().strip(), actual_content.decode().strip())
            actual_content = await f.files.read_file("test.txt")
            self.assertEqual(content.strip(), actual_content.strip())
            await f.files.delete_file("test.txt")
            
    async def test_write_raw_file(self):
        """
        Test writing a file with a full spectrum of data to the device.
        """
        async with Frame() as f:
            content = bytearray(range(1,255))
            await f.files.write_file("test.dat", content, checked=True)
            actual_content = await f.files.read_file("test.dat")
            self.assertEqual(content, actual_content)
            actual_content = await f.files.read_file("test.dat")
            self.assertEqual(content, actual_content)
            await f.files.write_file("test.dat", content, checked=True)
            actual_content = await f.files.read_file("test.dat")
            self.assertEqual(content, actual_content)
            actual_content = await f.files.read_file("test.dat")
            self.assertEqual(content, actual_content)
            await f.files.delete_file("test.dat")

if __name__ == "__main__":
    unittest.main()
