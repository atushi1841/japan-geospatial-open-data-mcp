"""Tests for japan-geospatial-open-data-mcp core module."""
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jpgeospatialmcp.core import (
    geocode_address,
    latlon_to_tile,
    get_tile,
    list_data_sources,
    TILE_LAYERS,
    ESTAT_TABLES,
)


def test_latlon_to_tile():
    x, y = latlon_to_tile(35.6812, 139.7671, 13)
    assert isinstance(x, int) and isinstance(y, int)
    assert 0 <= x < 2**13
    assert 0 <= y < 2**13


def test_tile_layers_catalog():
    assert "std" in TILE_LAYERS
    assert "seamlessphoto" in TILE_LAYERS
    for k, (name, ext, (zmin, zmax)) in TILE_LAYERS.items():
        assert zmin <= zmax
        assert ext in ("png", "jpg", "pbf")


def test_estat_tables_known():
    assert "population" in ESTAT_TABLES
    assert "vital_stats" in ESTAT_TABLES


def test_list_data_sources():
    srcs = list_data_sources()
    assert isinstance(srcs, list) and len(srcs) >= 5
    names = [s["name"] for s in srcs]
    assert any("GSI" in n for n in names)
    assert any("e-Stat" in n for n in names)
    # keyless sources exist
    assert any(not s["key"] for s in srcs)


def test_geocode_japan_live():
    res = geocode_address("渋谷区道玄坂")
    assert isinstance(res, list) and len(res) >= 1
    assert abs(res[0]["lat"] - 35.657) < 0.01
    assert abs(res[0]["lon"] - 139.698) < 0.01


def test_get_gsi_tile_live():
    res = get_tile("std", 35.6812, 139.7671, 13)
    assert res["image"]
    assert res["mime"] in ("image/png", "image/jpeg", "application/x-protobuf")
    assert res["attribution"].startswith("Geospatial Information Authority of Japan")
