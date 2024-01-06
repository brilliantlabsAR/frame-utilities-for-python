import sys
import argparse
from importlib.metadata import version

if __name__ == "__main__":
    sys.path.append("src.frameutils")
    from create_sprites import create_sprite_file
else:
    from .create_sprites import create_sprite_file


def main():
    parser = argparse.ArgumentParser(
        prog="frameutils",
        description="Useful utilities for Frame",
        epilog="For detailed instructions, visit: https://docs.brilliant.xyz",
    )

    parser.add_argument("-v", "--version", action="version")
    parser.version = version("frameutils")

    # Create sprites subcommand
    create_sprites_subparser = parser.add_subparsers(dest="create_sprites").add_parser(
        "create_sprites",
        help="create a sprite pack from a folder of images",
    )

    create_sprites_subparser.add_argument(
        "image_directory",
        type=str,
        help="directory containing images files to include in sprite pack",
    )
    create_sprites_subparser.add_argument(
        "output_filename",
        type=str,
        help="output filename",
    )
    create_sprites_subparser.add_argument(
        "-c",
        dest="colors",
        type=int,
        choices=[2, 4, 16],
        default=16,
        help="maximum range of colors to index",
    )
    create_sprites_subparser.add_argument(
        "--header",
        dest="as_header",
        action="store_true",
        help="output as a c header file",
    )

    # Parse
    args = parser.parse_args()

    if args.create_sprites:
        create_sprite_file(
            args.image_directory,
            args.output_filename,
            args.colors,
            args.as_header,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
