from __future__ import annotations
import asyncio
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .frame import Frame

char_width_mapping = {
    0x000020: 13,
    0x000021: 5,
    0x000022: 13,
    0x000023: 19,
    0x000024: 17,
    0x000025: 34,
    0x000026: 20,
    0x000027: 5,
    0x000028: 10,
    0x000029: 11,
    0x00002A: 21,
    0x00002B: 19,
    0x00002C: 8,
    0x00002D: 17,
    0x00002E: 6,
    0x000030: 18,
    0x000031: 16,
    0x000032: 16,
    0x000033: 15,
    0x000034: 18,
    0x000035: 15,
    0x000036: 17,
    0x000037: 15,
    0x000038: 18,
    0x000039: 17,
    0x00003A: 6,
    0x00003B: 8,
    0x00003C: 19,
    0x00003D: 19,
    0x00003E: 19,
    0x00003F: 14,
    0x000040: 31,
    0x000041: 22,
    0x000042: 18,
    0x000043: 16,
    0x000044: 19,
    0x000045: 17,
    0x000046: 17,
    0x000047: 18,
    0x000048: 19,
    0x000049: 12,
    0x00004A: 14,
    0x00004B: 19,
    0x00004C: 16,
    0x00004D: 23,
    0x00004E: 19,
    0x00004F: 20,
    0x000050: 18,
    0x000051: 22,
    0x000052: 20,
    0x000053: 17,
    0x000054: 20,
    0x000055: 19,
    0x000056: 21,
    0x000057: 23,
    0x000058: 21,
    0x000059: 23,
    0x00005A: 17,
    0x00005B: 9,
    0x00005C: 15,
    0x00005D: 10,
    0x00005E: 20,
    0x00005F: 25,
    0x000060: 11,
    0x000061: 19,
    0x000062: 18,
    0x000063: 13,
    0x000064: 18,
    0x000065: 16,
    0x000066: 15,
    0x000067: 20,
    0x000068: 18,
    0x000069: 5,
    0x00006A: 11,
    0x00006B: 18,
    0x00006C: 8,
    0x00006D: 28,
    0x00006E: 18,
    0x00006F: 18,
    0x000070: 18,
    0x000071: 18,
    0x000072: 11,
    0x000073: 15,
    0x000074: 14,
    0x000075: 17,
    0x000076: 19,
    0x000077: 30,
    0x000078: 20,
    0x000079: 20,
    0x00007A: 16,
    0x00007B: 12,
    0x00007C: 5,
    0x00007D: 12,
    0x00007E: 17,
    0x0000A1: 6,
    0x0000A2: 14,
    0x0000A3: 18,
    0x0000A5: 22,
    0x0000A9: 28,
    0x0000AB: 17,
    0x0000AE: 29,
    0x0000B0: 15,
    0x0000B1: 20,
    0x0000B5: 17,
    0x0000B7: 6,
    0x0000BB: 17,
    0x0000BF: 14,
    0x0000C0: 22,
    0x0000C1: 23,
    0x0000C2: 23,
    0x0000C3: 23,
    0x0000C4: 23,
    0x0000C5: 23,
    0x0000C6: 32,
    0x0000C7: 16,
    0x0000C8: 17,
    0x0000C9: 16,
    0x0000CA: 17,
    0x0000CB: 17,
    0x0000CC: 12,
    0x0000CD: 11,
    0x0000CE: 16,
    0x0000CF: 15,
    0x0000D0: 22,
    0x0000D1: 19,
    0x0000D2: 20,
    0x0000D3: 20,
    0x0000D4: 20,
    0x0000D5: 20,
    0x0000D6: 20,
    0x0000D7: 18,
    0x0000D8: 20,
    0x0000D9: 19,
    0x0000DA: 19,
    0x0000DB: 19,
    0x0000DC: 19,
    0x0000DD: 22,
    0x0000DE: 18,
    0x0000DF: 19,
    0x0000E0: 19,
    0x0000E1: 19,
    0x0000E2: 19,
    0x0000E3: 19,
    0x0000E4: 19,
    0x0000E5: 19,
    0x0000E6: 29,
    0x0000E7: 14,
    0x0000E8: 17,
    0x0000E9: 16,
    0x0000EA: 17,
    0x0000EB: 17,
    0x0000EC: 11,
    0x0000ED: 11,
    0x0000EE: 16,
    0x0000EF: 15,
    0x0000F0: 18,
    0x0000F1: 16,
    0x0000F2: 18,
    0x0000F3: 18,
    0x0000F4: 18,
    0x0000F5: 17,
    0x0000F6: 18,
    0x0000F7: 19,
    0x0000F8: 18,
    0x0000F9: 17,
    0x0000FA: 17,
    0x0000FB: 16,
    0x0000FC: 17,
    0x0000FD: 20,
    0x0000FE: 18,
    0x0000FF: 20,
    0x000131: 5,
    0x000141: 19,
    0x000142: 10,
    0x000152: 30,
    0x000153: 30,
    0x000160: 17,
    0x000161: 15,
    0x000178: 22,
    0x00017D: 18,
    0x00017E: 17,
    0x000192: 16,
    0x0020AC: 18,
    0x0F0000: 70,
    0x0F0001: 70,
    0x0F0002: 70,
    0x0F0003: 70,
    0x0F0004: 91,
    0x0F0005: 70,
    0x0F0006: 70,
    0x0F0007: 70,
    0x0F0008: 70,
    0x0F0009: 70,
    0x0F000A: 70,
    0x0F000B: 70,
    0x0F000C: 70,
    0x0F000D: 70,
    0x0F000E: 77,
    0x0F000F: 76,
    0x0F0010: 70
}

char_spacing = 4


class Display:
    """Helpers for displaying text and graphics on the Frame display."""

    frame: "Frame" = None

    palette = [
        (0, 0, 0),
        (157, 157, 157),
        (255, 255, 255),
        (190, 38, 51),
        (224, 111, 139),
        (73, 60, 43),
        (164, 100, 34),
        (235, 137, 49),
        (247, 226, 107),
        (47, 72, 78),
        (68, 137, 26),
        (163, 206, 39),
        (27, 38, 50),
        (0, 87, 132),
        (49, 162, 242),
        (178, 220, 239),
    ]

    _line_height = 60

    @property
    def line_height(self):
        return self._line_height

    @line_height.setter
    def line_height(self, value):
        if value < 0:
            raise ValueError("line_height must be a non-negative integer")
        self._line_height = value

    def __init__(self, frame: "Frame"):
        self.frame = frame

    async def show_text(self, text: str, x: int = 1, y: int = 1, max_width: Optional[int] = 640):
        await self.write_text(text, x, y, max_width)
        await self.show()

    async def write_text(self, text: str, x: int = 1, y: int = 1, max_width: Optional[int] = 640, max_height: Optional[int] = None):
        if max_width is not None:
            text = self.wrap_text(text, max_width)

        for line in text.split("\n"):
            await self.frame.run_lua(f"frame.display.text(\"{self.frame.escape_lua_string(line)}\",{x},{y})", checked=True)
            y += self.line_height
            if max_height is not None and y > max_height:
                break
            
    async def scroll_text(self, text: str, lines_per_frame: int = 5, delay: float = 0.12):
        margin = self.line_height
        text = self.wrap_text(text, 640)
        total_height = self.get_text_height(text)
        print(f"timeout: {total_height/lines_per_frame*(delay+0.05)+5}")
        await self.frame.run_lua(f"scrollText(\"{self.frame.escape_lua_string(text)}\",{self.line_height},{total_height},{lines_per_frame},{delay})",checked=True,timeout=total_height/lines_per_frame*(delay+0.1)+5)

    def wrap_text(self, text: str, max_width: int):
        lines = text.split("\n")
        output = ""
        for line in lines:
            if self.get_text_width(line) <= max_width:
                output += line+"\n"
            else:
                this_line = ""
                words = line.split(" ")
                for word in words:
                    if self.get_text_width(this_line+" "+word) > max_width:
                        output += this_line+"\n"
                        this_line = word
                    elif len(this_line) == 0:
                        this_line = word
                    else:
                        this_line += " "+word
                if len(this_line) > 0:
                    output += this_line+"\n"
        return output.rstrip("\n")

    def get_text_height(self, text: str):
        num_lines = text.count("\n") + 1
        return num_lines * (self.line_height)

    def get_text_width(self, text: str):
        width = 0
        for char in text:
            width += char_width_mapping.get(ord(char), 25) + char_spacing
        return width

    async def show(self):
        """Swaps the buffer to show the changes."""
        await self.frame.run_lua("frame.display.show()", checked=True)

    async def clear(self):
        await self.frame.run_lua("frame.display.bitmap(1,1,4,2,15,\"\\xFF\")")
        await self.show()

    async def set_palette(self, index: int, color: tuple[int, int, int]):
        raise NotImplementedError(
            "assign_color is not yet working in the Frame firmware")
        if index == 16:
            index = 0
        if index < 0 or index > 15:
            raise ValueError("Index out of range, must be between 0 and 15")
        self.palette[index] = color
        await self.frame.run_lua(f"frame.display.assign_color({index+1},{color[0]},{color[1]},{color[2]})", checked=True)

    async def draw_rect(self, x: int, y: int, w: int, h: int, color: int):
        w = w // 8 * 8
        await self.frame.run_lua(f"frame.display.bitmap({x},{y},{w},2,{color},string.rep(\"\\xFF\",{(w//8)*h}))")

    async def draw_rect_filled(self, x: int, y: int, w: int, h: int, border_width: int, border_color: int, fill_color: int):
        w = w // 8 * 8
        if border_width > 0:
            border_width = border_width // 8 * 8
            if border_width == 0:
                border_width = 8
        else:
            await self.draw_rect(x, y, w, h, fill_color)
            return

        # draw entire rectangle as border color
        await self.draw_rect(x, y, w, h, border_color)
        # draw the inside rectangle
        await self.draw_rect(x+border_width, y+border_width, w-border_width*2, h-border_width*2, fill_color)
