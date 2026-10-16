#!/usr/bin/env python3
"""
Japan Geospatial Open Data MCP Server
=====================================
MCP server exposing Japan's national open geospatial data to AI agents:

- GSI (Geospatial Information Authority) geocoding (msearch.gsi.go.jp)
- GSI tile layers (cyberjapandata.gsi.go.jp XYZ tiles, keyless)
- e-Stat statistics API (api.e-stat.go.jp, requires ESTAT_APP_ID env var)
- MLIT National Geographical Information / school district data (nlftp.mlit.go.jp, keyless)
- Optional: MLIT Real Estate Information Library (reinfolib.mlit.go.jp,
  requires REINFOLIB_API_KEY env var, obtained by application)

No API keys are required for the core tools. Optional env vars:
  ESTAT_APP_ID     e-Stat application ID (free registration at e-stat.go.jp)
  REINFOLIB_API_KEY MLIT Real Estate Information Library key (application required)

Data sources are official open data; reuse is free per GSI / e-Stat / MLIT terms.
"""
import base64
import json
import math
import os
import urllib.parse
import urllib.request

import mcp.types as types
import requests
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions

USER_AGENT = os.environ.get("USER_AGENT", "japan-geospatial-open-data-mcp/1.0 (+https://github.com/atushi1841/japan-geospatial-open-data-mcp)")
TIMEOUT = 20

GSI_GEOCODER_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"
GSI_TILE_URL = "https://cyberjapandata.gsi.go.jp/xyz/{layer}/{z}/{x}/{y}.{ext}"
ESTAT_BASE = "http://api.e-stat.go.jp/rest/3.0/app"
NLFTP_BASE = "https://nlftp.mlit.go.jp/ksj"
REINFOLIB_BASE = "https://www.reinfolib.mlit.go.jp/ex-api/external"

# GSI tile layer catalog (id, name, format, zoom range)
TILE_LAYERS = {
    "std": ("Standard map / Hyochiin map (standard)", "png", (2, 18)),
    "pale": ("Pale map / Hyochiin map (pale)", "png", (2, 18)),
    "seamlessphoto": ("Seamless photo / Zenkoku saishin shashin", "jpg", (2, 18)),
    "nendophoto2024": ("Annual photo 2024", "jpg", (4, 17)),
    "nendophoto2023": ("Annual photo 2023", "jpg", (4, 17)),
    "nendophoto2022": ("Annual photo 2022", "jpg", (4, 17)),
    "optimal_bvmap": ("Optimized vector tile", "pbf", (4, 17)),
    "blank": ("Blank map / Hakuchizu", "png", (2, 14)),
    "english": ("English map", "png", (2, 18)),
    "gazo1": ("Aerial photo 1974-1978", "jpg", (10, 17)),
    "gazo4": ("Aerial photo 1987-1990", "jpg", (10, 17)),
}

# e-Stat common statistical table IDs (freely reusable stats)
ESTAT_TABLES = {
    "population": ("0000080005", "Population of Japan (census 2020, by age/sex)"),
    "population_age": ("0003004079", "Population by age and sex (periodic census)"),
    "vital_stats": ("0003150423", "Vital statistics (births, deaths, marriages)"),
    "household": ("0020170004", "Household count and composition"),
}


def _http_get(url, headers=None, params=None, timeout=TIMEOUT):
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    resp = requests.get(url, headers=h, params=params, timeout=timeout)
    return resp


def geocode_address(address):
    resp = _http_get(GSI_GEOCODER_URL, params={"q": address})
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"No location found for address: {address}")
    results = []
    for feat in data[:10]:
        lon, lat = feat["geometry"]["coordinates"]
        props = feat.get("properties", {})
        results.append({
            "title": props.get("title", ""),
            "lat": lat,
            "lon": lon,
        })
    return results


def latlon_to_tile(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return x, y


def get_tile(layer, lat, lon, z):
    if layer not in TILE_LAYERS:
        raise ValueError(f"Unknown layer '{layer}'. Available: {sorted(TILE_LAYERS)}")
    name, ext, (zmin, zmax) = TILE_LAYERS[layer]
    if not (zmin <= z <= zmax):
        raise ValueError(f"Zoom {z} out of range for layer '{layer}' (allowed {zmin}-{zmax})")
    x, y = latlon_to_tile(lat, lon, z)
    url = GSI_TILE_URL.format(layer=layer, z=z, x=x, y=y, ext=ext)
    resp = _http_get(url)
    if resp.status_code == 404:
        raise ValueError(f"Tile not available at z={z} x={x} y={y} (layer {layer}). Try lower zoom or another layer.")
    resp.raise_for_status()
    b64 = base64.b64encode(resp.content).decode()
    mime = "image/png" if ext == "png" else "image/jpeg" if ext == "jpg" else "application/x-protobuf"
    return {
        "tile_url": url,
        "coordinates": {"x": x, "y": y, "z": z},
        "center": {"lat": lat, "lon": lon},
        "attribution": "Geospatial Information Authority of Japan (GSI)",
        "note": "GSI tiles are free open data; credit 'Geospatial Information Authority of Japan'.",
        "image": b64,
        "mime": mime,
    }


def get_e_stat_data(stats_data_id=None, table_key=None, **filters):
    app_id = os.environ.get("ESTAT_APP_ID", "")
    if not app_id:
        raise ValueError(
            "ESTAT_APP_ID not set. Register a free application ID at "
            "https://www.e-stat.go.jp/api/en and set ESTAT_APP_ID."
        )
    if stats_data_id is None and table_key:
        if table_key not in ESTAT_TABLES:
            raise ValueError(f"Unknown table key '{table_key}'. Available: {sorted(ESTAT_TABLES)}")
        stats_data_id, _ = ESTAT_TABLES[table_key]
    if stats_data_id is None:
        raise ValueError("Provide stats_data_id or table_key.")
    params = {"appId": app_id, "statsDataId": stats_data_id, "lang": "J"}
    params.update({k: v for k, v in filters.items() if v is not None})
    url = f"{ESTAT_BASE}/json/getStatsData"
    resp = _http_get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def get_e_stat_meta(table_key=None, stats_data_id=None):
    if stats_data_id is None and table_key:
        if table_key not in ESTAT_TABLES:
            raise ValueError(f"Unknown table key '{table_key}'. Available: {sorted(ESTAT_TABLES)}")
        stats_data_id, _ = ESTAT_TABLES[table_key]
    if stats_data_id is None:
        raise ValueError("Provide stats_data_id or table_key.")
    return get_e_stat_data(stats_data_id=stats_data_id, metaGetFlg="Y", explanationGetFlg="N", annotationGetFlg="N", cntGetFlg="N")


def list_school_districts(prefecture=None, zoom=14):
    """List school district (A27) GeoJSON files on nlftp.mlit.go.jp."""
    base = f"{NLFTP_BASE}/gml/datalist"
    year = "2023"
    resp = _http_get(f"{base}/KsjTmplt-A27-{year}.html")
    resp.raise_for_status()
    html = resp.text
    # parse file links like A27-23_GML.zip
    import re
    files = re.findall(r'href="([^"]+\.zip)"', html)
    out = []
    for f in files:
        out.append({
            "file": f,
            "url": f"{base}/A27-2023/{f}" if "/" in f else f"{base}/{f}",
        })
    return {"year": year, "source": "MLIT National Geographical Information (Kokuto Suuchi Jhouhou) A27 School Districts", "files": out[:40]}


def get_reinfolib_xkt004(z, x, y, response_format="geojson"):
    key = os.environ.get("REINFOLIB_API_KEY", "")
    if not key:
        raise ValueError(
            "REINFOLIB_API_KEY not set. Apply for the MLIT Real Estate Information "
            "Library API at https://www.reinfolib.mlit.go.jp/ (XKT004 school district GIS)."
        )
    params = {"response_format": response_format, "z": z, "x": x, "y": y}
    resp = _http_get(f"{REINFOLIB_BASE}/XKT004", params=params,
                     headers={"Ocp-Apim-Subscription-Key": key})
    resp.raise_for_status()
    return {"url": f"{REINFOLIB_BASE}/XKT004", "params": params, "data": resp.json()}


def list_data_sources():
    return [
        {"name": "GSI Geocoding API", "url": "https://msearch.gsi.go.jp/address-search/AddressSearch", "key": False, "description": "Japanese address geocoding"},
        {"name": "GSI Tiles (XYZ)", "url": "https://cyberjapandata.gsi.go.jp/xyz/", "key": False, "description": "Standard/pale/blank maps, aerial photos, vector tiles"},
        {"name": "e-Stat API 3.0", "url": "http://api.e-stat.go.jp/rest/3.0/", "key": True, "env": "ESTAT_APP_ID", "description": "National statistics (population, vital stats, households)"},
        {"name": "MLIT National Geographical Information", "url": "https://nlftp.mlit.go.jp/ksj/", "key": False, "description": "School districts (A27), middle schools (A28), GML/GeoJSON nationwide"},
        {"name": "MLIT Real Estate Information Library", "url": "https://www.reinfolib.mlit.go.jp/", "key": True, "env": "REINFOLIB_API_KEY", "description": "School district GIS tiles (XKT004), land prices, zoning, hazard zones"},
        {"name": "GSI Tile Catalog", "url": "https://cyberjapandata.gsi.go.jp/xyz/std/mokuroku.csv.gz", "key": False, "description": "Tile inventory (mokuroku) for bulk discovery"},
    ]
