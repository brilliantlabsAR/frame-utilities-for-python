from src.frameutils import Frame
import unittest
import asyncio
import sys
import time

sys.path.append("..")


class TestDisplay(unittest.IsolatedAsyncioTestCase):
    async def test_write_text(self):
        async with Frame() as f:
            await f.display.show_text("Lorem \"ipsum\" [dolor] 'sit' amet,    consectetur\nadipiscing elit.")
            await f.display.show_text("Lorem \"ipsum\" [dolor] 'sit' amet,    consectetur\nadipiscing elit." * 100)
            await f.display.show_text("Done")
            await f.display.clear()

    async def test_word_wrap(self):
        async with Frame() as f:
            wrapped400 = f.display.wrap_text("Hi bob " * 100, 400)
            wrapped800 = f.display.wrap_text("Hi bob " * 100, 800)
            self.assertEqual(wrapped400.count("!"), wrapped800.count("!"))
            self.assertAlmostEqual(wrapped400.count("\n"), wrapped800.count("\n") * 2, delta=3)
            self.assertAlmostEqual(f.display.get_text_height(wrapped400), f.display.get_text_height(wrapped800) * 2, delta=100)

    async def test_line_height(self):
        async with Frame() as f:
            self.assertEqual(f.display.line_height,f.display.get_text_height("hello world!  123Qgjp@"))
            heightOfTwoLines = f.display.get_text_height("hello\nworldj")
            f.display.line_height += 20
            self.assertEqual(heightOfTwoLines + 40, f.display.get_text_height("hello p\nworld j"))

    async def test_draw_rectangles(self):
        async with Frame() as f:
            await f.display.draw_rect(1,1,640,400,5)
            await f.display.draw_rect(300,300,10,10,2)
            await f.display.draw_rect_filled(50,50,300,300,25,7,14)
            await f.display.show()
            await f.display.clear()
            
    async def test_scroll_text(self):
        async with Frame() as f:
            start_time = time.time()
            await f.display.scroll_text("Lorem \"ipsum\" [dolor] 'sit' amet,    consectetur adipiscing elit.\nNulla nec nunc euismod, consectetur nunc eu, aliquam nunc.\nNulla lorem nec nunc euismod, ipsum consectetur nunc eu, aliquam nunc.")
            end_time = time.time()
            elapsed_time_1 = end_time - start_time
            self.assertGreaterEqual(elapsed_time_1, 5)
            self.assertLess(elapsed_time_1, 20)
            
            start_time = time.time()
            await f.display.scroll_text("Lorem \"ipsum\" [dolor] 'sit' amet,    consectetur adipiscing elit.\nNulla nec nunc euismod, consectetur nunc eu, aliquam nunc.\nNulla lorem nec nunc euismod, ipsum consectetur nunc eu, aliquam nunc.\n" * 3)
            end_time = time.time()
            elapsed_time_2 = end_time - start_time
            self.assertAlmostEqual(elapsed_time_1*3, elapsed_time_2, delta=8)

            
if __name__ == "__main__":
    unittest.main()
