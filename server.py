from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import geopandas as gpd
from shapely.geometry import shape
import rasterio
from rasterio.mask import mask
import requests

app = Flask(__name__)
CORS(app)

# Define directories
SAVE_DIRECTORY = r'D:\Trabalho\_MATERIAL DE APOIO\SCRIPTS\Eartbenders_v1\data'
TILES_DIRECTORY = os.path.join(SAVE_DIRECTORY, 'nasadem_tiles')

# Ensure necessary directories exist
os.makedirs(SAVE_DIRECTORY, exist_ok=True)
os.makedirs(TILES_DIRECTORY, exist_ok=True)

# NASA Earthdata credentials
EARTHDATA_USERNAME = 'earthbenders'
EARTHDATA_PASSWORD = 'Earthbenders2024!'

class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and \
               redirect_parsed.hostname != self.AUTH_HOST and \
               original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']

        return

# Create a session with authentication
session = SessionWithHeaderRedirection(EARTHDATA_USERNAME, EARTHDATA_PASSWORD)

@app.route('/save_polygon', methods=['POST'])
def save_polygon():
    try:
        data = request.json
        polygon_geojson = data['data']
        filename = data['filename']
        save_path = os.path.join(SAVE_DIRECTORY, filename)

        # Convert GeoJSON to a GeoDataFrame and save it
        gdf = gpd.GeoDataFrame.from_features([polygon_geojson])
        gdf.to_file(save_path, driver='GeoJSON')

        return jsonify({"message": f"Polygon saved successfully at {save_path}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clip_srtm', methods=['POST'])
def clip_srtm():
    try:
        data = request.json
        polygon_geojson = data['polygon']
        bbox = data['bbox']

        polygon = shape(polygon_geojson['geometry'])
        intersecting_tiles = get_intersecting_tiles(bbox)

        clipped_file = os.path.join(SAVE_DIRECTORY, 'clipped_nasadem.tif')
        for tile in intersecting_tiles:
            download_tile(tile)
            raster_path = os.path.join(TILES_DIRECTORY, f"{tile}.SRTMGL1.hgt.zip")
            if os.path.exists(raster_path):
                clip_raster_to_polygon(raster_path, polygon, clipped_file)

        return jsonify({"message": "Clipping completed!", "output_file": clipped_file}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def download_tile(tile_name):
    """Download a specific NASADEM tile with NASA Earthdata authentication."""
    tile_url = f"https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/{tile_name}.SRTMGL1.hgt.zip"
    local_path = os.path.join(TILES_DIRECTORY, f"{tile_name}.SRTMGL1.hgt.zip")

    try:
        response = session.get(tile_url, stream=True)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

        print(f"Downloaded {tile_name} successfully!")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error while downloading {tile_name}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {tile_name}. Error: {e}")

def get_intersecting_tiles(bbox):
    lat_min, lon_min = bbox[0]
    lat_max, lon_max = bbox[1]

    tiles = []
    for lat in range(int(lat_min), int(lat_max) + 1):
        for lon in range(int(lon_min), int(lon_max) + 1):
            lat_prefix = 'N' if lat >= 0 else 'S'
            lon_prefix = 'E' if lon >= 0 else 'W'
            lat_str = f"{abs(lat):02d}"
            lon_str = f"{abs(lon):03d}"
            tile_name = f"{lat_prefix}{lat_str}{lon_prefix}{lon_str}"
            tiles.append(tile_name)
    
    return tiles

def clip_raster_to_polygon(raster_path, polygon, output_path):
    """Clip a raster to the boundary of a polygon and save the result."""
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, [polygon], crop=True)
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
        print(f"Clipped raster saved to: {output_path}")

@app.route('/serve_srtm/<filename>', methods=['GET'])
def serve_srtm(filename):
    """Serve SRTM file for display on the map."""
    return send_from_directory(SAVE_DIRECTORY, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
