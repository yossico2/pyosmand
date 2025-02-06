import os
import signal
import sys
import math
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor


def signal_handler(sig, frame):
    print("\n")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Define your bounding box (min_lat, min_lon, max_lat, max_lon)
BOUNDING_BOX = {
    "min_lat": 37.7749,  # south
    "max_lat": 37.8044,  # north
    "min_lon": -122.4194,  # west
    "max_lon": -122.3890,  # east
}

ZOOM_LEVELS = range(1, 20)  # Zoom levels to download

# Directory where tiles will be saved
OUTPUT_DIR = "tiles"


PRINT_DOTS = False


def latlon_to_tile(lat, lon, zoom):
    """Convert latitude and longitude to tile coordinates (x, y) at a given zoom level."""
    n = 2**zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (
            1.0
            - math.log(
                math.tan(math.radians(lat)) + (1.0 / math.cos(math.radians(lat)))
            )
            / math.pi
        )
        / 2.0
        * n
    )
    return x, y


def tile_to_quadkey(x, y, zoom):
    """Convert tile coordinates to a Bing Maps quadkey."""
    quadkey = ""
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (x & mask) != 0:
            digit += 1
        if (y & mask) != 0:
            digit += 2
        quadkey += str(digit)
    return quadkey


def download_tile(quadkey, zoom, x, y):
    global PRINT_DOTS

    """Download a tile image given its quadkey."""
    url = f"https://t.ssl.ak.dynamic.tiles.virtualearth.net/comp/ch/{quadkey}?mkt=en-us&it=A,G,L&shading=hill"
    tile_path = os.path.join(OUTPUT_DIR, str(zoom), str(x))
    os.makedirs(tile_path, exist_ok=True)

    output_file = os.path.join(tile_path, f"{y}.jpg")
    if os.path.exists(output_file):  # Skip if already downloaded
        # print(f"Skipping {zoom}/{x}/{y}")
        if PRINT_DOTS:
            print(".", end="")
        else:
            print("Skipping existing files ", end="")
            PRINT_DOTS = True
        return

    if PRINT_DOTS:
        PRINT_DOTS = False
        print()

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded {zoom}/{x}/{y}")
    else:
        print(f"Failed to download {zoom}/{x}/{y} (Quadkey: {quadkey})")


def process_zoom_level(zoom):
    """Process all tiles in the bounding box for a given zoom level."""
    min_x, min_y = latlon_to_tile(
        BOUNDING_BOX["max_lat"],
        BOUNDING_BOX["min_lon"],
        zoom,
    )
    max_x, max_y = latlon_to_tile(
        BOUNDING_BOX["min_lat"],
        BOUNDING_BOX["max_lon"],
        zoom,
    )

    tasks = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                quadkey = tile_to_quadkey(x, y, zoom)
                tasks.append(executor.submit(download_tile, quadkey, zoom, x, y))

    for task in tasks:
        task.result()  # Wait for all tasks to finish
    
    global PRINT_DOTS
    if PRINT_DOTS:
        PRINT_DOTS = False
        print()


def parse_command_line_args():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Processcommand-line arguments.")

    # Add arguments
    parser.add_argument(
        "-o",
        "--output",
        help="output directory path (created if not exists)",
    )

    parser.add_argument(
        "--south",
        type=float,
        help="south (min_lat)",
    )

    parser.add_argument(
        "--north",
        type=float,
        help="north (max_lat)",
    )

    parser.add_argument(
        "--west",
        type=float,
        help="west (min_lon)",
    )

    parser.add_argument(
        "--east",
        type=float,
        help="east (max_lon)",
    )

    # Add a zoom tuple argument (two numbers separated by a comma)
    parser.add_argument(
        "-z",
        "--zoom-levels",
        type=lambda s: tuple(map(int, s.split(","))),
        help="zoom level range (e.g., 10,20)",
    )

    # Parse arguments
    args = parser.parse_args()

    # OUTPUT_DIR
    while args.output is None:
        user_input = input("Enter output directory: ")
        output = user_input if user_input is not None and len(user_input) > 0 else None
        if output and not os.path.exists(output):
            while True:
                user_input = input("output path not exists. create ? [y|n]")
                if "y" == user_input:
                    break
                if "n" == user_input:
                    exit(0)
            args.output = output

    # ZOOM_LEVELS
    if args.zoom_levels:
        zoom_levels_len = len(args.zoom_levels)
        if 1 != zoom_levels_len and 2 != zoom_levels_len:
            args.zoom_levels = None
    while args.zoom_levels is None:
        user_input = input("Enter zoom levels to download (e.g., 10 or 10,20): ")
        if user_input:
            args.zoom_levels = tuple(map(int, user_input.split(",")))
            zoom_levels_len = len(args.zoom_levels)
            if 1 != zoom_levels_len and 2 != zoom_levels_len:
                args.zoom_levels = None

    # BOUNDING_BOX
    if (
        args.south is None
        or args.north is None
        or args.west is None
        or args.east is None
    ):
        print("Enter bounding-box")

    while args.south is None:
        user_input = input("south: ")
        try:
            args.south = float(user_input)
        except:
            continue
    while args.north is None:
        user_input = input("north: ")
        try:
            args.north = float(user_input)
        except:
            continue
    while args.west is None:
        user_input = input("west: ")
        try:
            args.west = float(user_input)
        except:
            continue
    while args.east is None:
        user_input = input("east: ")
        try:
            args.east = float(user_input)
        except:
            continue

    # confirm selection
    print(f"output directory path: {args.output}")

    print(
        f"bounding-box: (south: {args.south}, north: {args.north}, west: {args.west}, east: {args.east})"
    )

    if 1 == zoom_levels_len:
        print(f"zoom-level: {args.zoom_levels[0]}")
    elif 2 == zoom_levels_len:
        print(f"zoom-levels: {args.zoom_levels[0]}-{args.zoom_levels[1]}")

    while True:
        user_input = input("Confirm [y|n]")
        if "y" == user_input:
            global BOUNDING_BOX
            BOUNDING_BOX = {
                "min_lat": args.south,
                "max_lat": args.north,
                "min_lon": args.west,
                "max_lon": args.east,
            }

            # Zoom levels to download
            global ZOOM_LEVELS
            if len(args.zoom_levels) == 1:
                args.zoom_levels = (args.zoom_levels[0], args.zoom_levels[0])
            ZOOM_LEVELS = range(args.zoom_levels[0], args.zoom_levels[1])

            global OUTPUT_DIR
            OUTPUT_DIR = args.output
            break
        if "n" == user_input:
            print("Canceled.")
            exit(0)


def main():
    """Main function to download tiles for all zoom levels."""
    global PRINT_DOTS
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for zoom in ZOOM_LEVELS:
        if PRINT_DOTS:
            PRINT_DOTS = False
            print()
        print(f"Processing zoom level {zoom}...")
        process_zoom_level(zoom)


if __name__ == "__main__":
    parse_command_line_args()
    main()
