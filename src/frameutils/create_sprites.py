from sklearn.cluster import KMeans
import math
import numpy as np
import os
import re
import cv2


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


def file_to_sprite(image_path, utf8_codepoint, colors, color_table_rgb):
    image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2LAB)

    # image[:,:,:3] is image without alpha channel
    shape = image.shape
    flat_image = image.reshape((shape[0] * shape[1], 3))

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

    color_table_lab = cv2.cvtColor(color_table_rgb.reshape(1, colors, 3), cv2.COLOR_RGB2LAB).reshape(colors, 3)
    
    # Work around: fit to color table for scipy kmeans to work properly
    kmeans = KMeans(n_clusters=colors, n_init="auto", random_state=0).fit(color_table_lab)
    kmeans.cluster_centers_ = np.array(color_table_lab, np.double)

    palleted_image = kmeans.predict(flat_image)

    # debug = palleted_image.reshape((shape[0], shape[1]))
    # print("\n".join(["".join(["{:2}".format(item) for item in row]) for row in debug]))

    bits_per_pixel = int(math.sqrt(colors))

    byte_list = []
    pixels_per_byte = int(8 / bits_per_pixel)
    current_byte = 0
    pixels_left_in_byte = pixels_per_byte
    mask = colors - 1

    for pixel in palleted_image:
        if pixels_left_in_byte > 0:
            current_byte += ((pixel & mask) << ((pixels_left_in_byte - 1) * bits_per_pixel))
            pixels_left_in_byte -= 1

        else:
            byte_list.append(current_byte)
            pixels_left_in_byte = pixels_per_byte
            current_byte = ((pixel & mask) << ((pixels_left_in_byte - 1) * bits_per_pixel))
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

def _rms(x0, x1, x2):
    return math.sqrt(x0**2 + x1**2 + x2**2)

def _print_rgb(text, rgb):
    print(f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m {text}\x1b[0m")

def create_colour_table(image_directory, colors, color_table_lua):
    flat_image_list = []
    for filename in os.listdir(image_directory):
        if re.search(r"[uU]\+[a-fA-F\d]{4,6}\.png", filename):
            image = cv2.cvtColor(cv2.imread(image_directory + "/" + filename), cv2.COLOR_BGR2LAB)
            flat_image_list.extend(image)

    flat_image_list = np.concatenate(flat_image_list)
    kmeans = KMeans(n_clusters=colors, n_init="auto", random_state=0)
    kmeans.fit(flat_image_list)

    color_table = np.array(kmeans.cluster_centers_, np.uint8).reshape(1, colors, 3)
    color_table_rgb = cv2.cvtColor(color_table, cv2.COLOR_LAB2RGB).reshape(colors, 3)

    # Sort the table to go from dark to light
    color_table_rgb = np.array(sorted(color_table_rgb, key=lambda x: _rms(x[0], x[1], x[2])))
    
    # Set table[1] == white (brightest colour)
    color_table_rgb[[1, colors-1]] = color_table_rgb[[colors-1, 1]]

    for i in color_table_rgb:
        _print_rgb(str(i), i)

    if color_table_lua:
        print("#########")
        for idx, val in enumerate(color_table_rgb):
            print(f"frame.display.assign_color({idx+1},{val[0]},{val[1]},{val[2]})")
        print("#########")
    
    return color_table_rgb

def create_sprite_file(image_directory, output_filename, colors, color_table, as_header):
    data_table = DataTable()

    for filename in os.listdir(image_directory):
        if re.search(r"[uU]\+[a-fA-F\d]{4,6}\.png", filename):
            print("Parsing " + filename)
            metadata, data = file_to_sprite(
                image_directory + "/" + filename,
                int(filename[2:-4], 16),
                colors,
                color_table
            )
            data_table.add(metadata, data)

    if as_header:
        data_table.generate_header(output_filename)

    else:
        raise NotImplementedError("TODO")
