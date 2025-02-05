import os
import math
import requests
from concurrent.futures import ThreadPoolExecutor

# Define your bounding box (min_lat, min_lon, max_lat, max_lon)
BOUNDING_BOX = {
    "min_lat": 37.7749,  # Change to your region
    "max_lat": 37.8044,
    "min_lon": -122.4194,
    "max_lon": -122.3890,
}
ZOOM_LEVELS = range(1, 20)  # Zoom levels to download

# Directory where tiles will be saved
OUTPUT_DIR = "tiles"


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
    """Download a tile image given its quadkey."""
    url = f"https://t.ssl.ak.dynamic.tiles.virtualearth.net/comp/ch/{quadkey}?mkt=en-us&it=A,G,L,LA&shading=hill"
    tile_path = os.path.join(OUTPUT_DIR, str(zoom), str(x))
    os.makedirs(tile_path, exist_ok=True)

    output_file = os.path.join(tile_path, f"{y}.jpg")
    if os.path.exists(output_file):  # Skip if already downloaded
        print(f"Skipping {zoom}/{x}/{y}")
        return

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
        BOUNDING_BOX["max_lat"], BOUNDING_BOX["min_lon"], zoom
    )
    max_x, max_y = latlon_to_tile(
        BOUNDING_BOX["min_lat"], BOUNDING_BOX["max_lon"], zoom
    )

    tasks = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                quadkey = tile_to_quadkey(x, y, zoom)
                tasks.append(executor.submit(download_tile, quadkey, zoom, x, y))

    for task in tasks:
        task.result()  # Wait for all tasks to finish


def main():
    """Main function to download tiles for all zoom levels."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for zoom in ZOOM_LEVELS:
        print(f"Processing zoom level {zoom}...")
        process_zoom_level(zoom)


if __name__ == "__main__":
    main()
