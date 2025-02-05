import os
import math
import requests


def latlon_to_tile(lat, lon, zoom):
    n = 2.0**zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (
            1.0
            - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat)))
            / math.pi
        )
        / 2.0
        * n
    )
    return x, y


def tile_to_quadkey(x, y, zoom):
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


def download_tile(quadkey, output_dir):
    url = f"https://t.ssl.ak.dynamic.tiles.virtualearth.net/comp/ch/{quadkey}?mkt=en-us&it=A,G,L,LA&shading=hill"
    output_path = os.path.join(output_dir, f"{quadkey}.jpg")

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded {quadkey}.jpg")
    else:
        print(f"Failed to download {quadkey}")


if __name__ == "__main__":
    output_folder = "tiles"
    os.makedirs(output_folder, exist_ok=True)
    quadkey = tile_to_quadkey(x=5, y=10, zoom=7)  # Example tile at zoom level 7
    download_tile(quadkey, output_folder)
