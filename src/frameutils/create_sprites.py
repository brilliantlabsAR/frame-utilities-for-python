from PIL import Image
from sklearn.cluster import KMeans
import math
import numpy as np
import os
import re


class FontMetadata:
    def __init__(self, utf8_code, width, height, color_mode, size):
        self.utf8_code = utf8_code
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
            f.write("    SPRITE_2_COLORS,\n")
            f.write("    SPRITE_4_COLORS,\n")
            f.write("    SPRITE_16_COLORS,\n")
            f.write("} sprite_colors_t;\n\n")

            f.write("typedef struct sprite_metadata_t\n")
            f.write("{\n")
            f.write("    uint16_t utf8_code;\n")
            f.write("    uint16_t height;\n")
            f.write("    uint16_t width;\n")
            f.write("    sprite_colors_t colors;\n")
            f.write("    size_t data_offset;\n")
            f.write("} sprite_metadata_t;\n\n")

            f.write("sprite_metadata_t sprite_metadata")
            f.write("[" + str(len(self.metadata)) + "] = {\n")

            for idx, row in enumerate(self.metadata):
                f.write("    {")
                f.write("0x{:04X}".format(row.utf8_code) + ", ")
                f.write(str(row.width) + ", ")
                f.write(str(row.height) + ", ")
                f.write(row.color_mode + ", ")
                f.write("0x{:08X}".format(row.offset) + "},\n")
            f.write("};\n\n")

            f.write("uint8_t font_data[" + str(len(self.data)) + "] = {")
            for idx, value in enumerate(self.data):
                if idx % 12 == 0:
                    f.write("\n    ")
                f.write("0x{:02X}".format(value))
                if idx != len(self.data) - 1:
                    f.write(", ")
            f.write("};")


def parse_file(image_path, colors):
    utf8_code = int(image_path[-8:-4], 16)
    img = np.array(Image.open(image_path))

    # img[:,:,:3] is img without alpha channel
    shape = img.shape
    flat_image = img[:, :, :3].reshape((shape[0] * shape[1], 3))

    kmeans = KMeans(n_clusters=colors, random_state=0, n_init="auto").fit(flat_image)

    palleted_img = kmeans.predict(flat_image).astype(np.uint8)

    # if black is not at index 0, swap it
    black_code = kmeans.predict(np.array([255, 255, 255]).reshape(1, -1))
    if black_code != 0:
        np.put(palleted_img, [0, 1], [1, 0])

    # debug = palleted_img.reshape((shape[0], shape[1]))
    # print('\n'.join([''.join(['{:2}'.format(item) for item in row])
    #     for row in debug]))

    bits_per_pixel = int(math.sqrt(colors))

    byte_list = []
    pixels_per_byte = int(8 / bits_per_pixel)
    current_byte = 0
    pixels_left_in_byte = pixels_per_byte
    mask = colors - 1

    for pixel in palleted_img:
        masked_value = pixel & mask
        if pixels_left_in_byte > 0:
            current_byte += masked_value << ((pixels_left_in_byte - 1) * bits_per_pixel)
            pixels_left_in_byte -= 1
        else:
            pixels_left_in_byte = pixels_per_byte - 1
            byte_list.append(current_byte)
            current_byte = masked_value << ((pixels_left_in_byte - 1) * bits_per_pixel)

    # write last byte if necessary
    if pixels_left_in_byte > 0:
        byte_list.append(current_byte)

    color_mode = "SPRITE_" + str(colors) + "_COLORS"

    return (
        FontMetadata(
            utf8_code,
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
        if re.search(r"[uU]\+[a-fA-F\d]+\.png", filename):
            print("Parsing " + filename)
            metadata, data = parse_file(image_directory + "/" + filename, colors)
            data_table.add(metadata, data)

    if as_header:
        data_table.generate_header(output_filename)

    else:
        raise NotImplementedError("TODO")
