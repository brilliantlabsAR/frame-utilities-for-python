from PIL import Image
from sklearn.cluster import KMeans
import math
import numpy as np
import os
import re


class FontMetadata:
    def __init__(self, utf8_codepoint, width, height, color_mode, size):
        self.utf8_codepoint = utf8_codepoint
        self.width = width
        self.height = height
        self.color_mode = color_mode
        self._size = size
        self.offset = 0


class DataTable:
    def __init__(self):
        self.data = []
        self.metadata = []
        self.current_offset = 0

    def add(self, metadata, data):
        self.data.extend(data)
        metadata.offset = self.current_offset
        self.metadata.append(metadata)
        self.current_offset += metadata._size

    def generate_header(self, filename):
        with open(filename, "w") as f:
            f.write("#include <stddef.h>\n")
            f.write("#include <stdint.h>\n\n")

            f.write("typedef enum sprite_colors_t\n")
            f.write("{\n")
            f.write("    SPRITE_2_COLORS = 2,\n")
            f.write("    SPRITE_4_COLORS = 4,\n")
            f.write("    SPRITE_16_COLORS = 16,\n")
            f.write("} sprite_colors_t;\n\n")

            f.write("typedef struct sprite_metadata_t\n")
            f.write("{\n")
            f.write("    uint32_t utf8_codepoint;\n")
            f.write("    uint16_t width;\n")
            f.write("    uint16_t height;\n")
            f.write("    sprite_colors_t colors;\n")
            f.write("    size_t data_offset;\n")
            f.write("} sprite_metadata_t;\n\n")

            f.write("const sprite_metadata_t sprite_metadata")
            f.write("[] = {\n")

            for idx, row in enumerate(self.metadata):
                f.write("    {")
                f.write("0x{:06X}".format(row.utf8_codepoint) + ", ")
                f.write(str(row.width) + ", ")
                f.write(str(row.height) + ", ")
                f.write(row.color_mode + ", ")
                f.write("0x{:08X}".format(row.offset) + "},\n")
            f.write("};\n\n")

            f.write("const uint8_t sprite_data[] = {")
            for idx, value in enumerate(self.data):
                if idx % 12 == 0:
                    f.write("\n    ")
                f.write("0x{:02X}".format(value))
                if idx != len(self.data) - 1:
                    f.write(", ")
            f.write("};")


def parse_file(image_path, utf8_codepoint, colors):
    img = np.array(Image.open(image_path))

    # img[:,:,:3] is img without alpha channel
    shape = img.shape
    flat_image = img[:, :, :3].reshape((shape[0] * shape[1], 3))

    # If space character, skip clustering, return all zeros
    if utf8_codepoint == 0x20:
        byte_list = [0] * (shape[0] * shape[1])

        color_mode = "SPRITE_" + str(colors) + "_COLORS"

        return (
            FontMetadata(
                utf8_codepoint,
                shape[1],
                shape[0],
                color_mode,
                len(byte_list),
            ),
            byte_list,
        )

    kmeans = KMeans(n_clusters=colors, random_state=0, n_init="auto").fit(flat_image)

    palleted_img = kmeans.predict(flat_image).astype(np.uint8)

    # if black is not at index 0, swap it
    black_code = kmeans.predict(np.array([0, 0, 0]).reshape(1, -1))[0]

    if black_code != 0:
        masked_black_code = palleted_img == black_code
        masked_0 = palleted_img == 0
        palleted_img[masked_black_code] = 0
        palleted_img[masked_0] = black_code

    # debug = palleted_img.reshape((shape[0], shape[1]))
    # print("\n".join(["".join(["{:2}".format(item) for item in row]) for row in debug]))

    bits_per_pixel = int(math.sqrt(colors))

    byte_list = []
    pixels_per_byte = int(8 / bits_per_pixel)
    current_byte = 0
    pixels_left_in_byte = pixels_per_byte
    mask = colors - 1

    for idx, pixel in enumerate(palleted_img):
        masked_value = pixel & mask
        if pixels_left_in_byte > 0:
            current_byte += masked_value << ((pixels_left_in_byte - 1) * bits_per_pixel)
            pixels_left_in_byte -= 1
            if idx == len(palleted_img) - 1:
                byte_list.append(current_byte)
        else:
            pixels_left_in_byte = pixels_per_byte
            byte_list.append(current_byte)
            current_byte = masked_value << ((pixels_left_in_byte - 1) * bits_per_pixel)
            pixels_left_in_byte -= 1

    # write last byte if necessary
    if pixels_left_in_byte > 0:
        byte_list.append(current_byte)

    color_mode = "SPRITE_" + str(colors) + "_COLORS"

    return (
        FontMetadata(
            utf8_codepoint,
            shape[1],
            shape[0],
            color_mode,
            len(byte_list),
        ),
        byte_list,
    )


def create_sprite_file(image_directory, output_filename, colors, as_header):
    data_table = DataTable()

    for filename in os.listdir(image_directory):
        if re.search(r"[uU]\+[a-fA-F\d]{4,6}\.png", filename):
            print("Parsing " + filename)
            metadata, data = parse_file(
                image_directory + "/" + filename,
                int(filename[2:-4], 16),
                colors,
            )
            data_table.add(metadata, data)

    if as_header:
        data_table.generate_header(output_filename)

    else:
        raise NotImplementedError("TODO")
