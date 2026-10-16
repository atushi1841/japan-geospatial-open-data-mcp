#!/usr/bin/env python3
"""MCP server entrypoint for Japan Geospatial Open Data (mcp-sdk 1.29 API)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions

from jpgeospatialmcp.core import (
    geocode_address,
    get_tile,
    get_e_stat_data,
    get_e_stat_meta,
    list_school_districts,
    get_reinfolib_xkt004,
    list_data_sources,
)

TOOLS = [
    types.Tool(
        name="geocode_japan",
        description="Geocode a Japanese address to lat/lon using the official GSI address search API. Returns up to 10 candidate locations.",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Japanese address, e.g. '東京都渋谷区道玄坂'"},
            },
            "required": ["address"],
        },
    ),
    types.Tool(
        name="get_gsi_tile",
        description="Fetch a GSI (Geospatial Information Authority) map tile as a base64 image. Keyless. Layers: std, pale, seamlessphoto, nendophoto2022-2024, optimal_bvmap, blank, english, gazo1/gazo4 (historic aerial). Returns tile URL plus a base64 image.",
        inputSchema={
            "type": "object",
            "properties": {
                "layer": {"type": "string", "description": "Tile layer id (see description)"},
                "lat": {"type": "number", "description": "Center latitude (WGS84)"},
                "lon": {"type": "number", "description": "Center longitude (WGS84)"},
                "z": {"type": "integer", "description": "Zoom level (2-18 depending on layer)"},
            },
            "required": ["layer", "lat", "lon", "z"],
        },
    ),
    types.Tool(
        name="list_data_sources",
        description="List all open data sources this MCP server can access (GSI tiles/geocoder, e-Stat, MLIT national geographical info, MLIT real estate library) and which require API keys.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="get_estat_data",
        description="Fetch statistics from Japan's e-Stat national statistics API (v3.0). Requires ESTAT_APP_ID env var (free registration). Known tables: population, population_age, vital_stats, household; or pass raw stats_data_id.",
        inputSchema={
            "type": "object",
            "properties": {
                "table_key": {"type": "string", "description": "Known table key or omit"},
                "stats_data_id": {"type": "string", "description": "Raw e-Stat stats table ID"},
                "cd_cat01": {"type": "string", "description": "e-Stat narrowing code cat1, e.g. '#A03503'"},
                "cd_cat02": {"type": "string", "description": "e-Stat narrowing code cat2"},
                "cd_cat03": {"type": "string", "description": "e-Stat narrowing code cat3"},
            },
        },
    ),
    types.Tool(
        name="get_estat_meta",
        description="Fetch metadata (aggregation items, region items, classification items) for an e-Stat stats table. Requires ESTAT_APP_ID env var.",
        inputSchema={
            "type": "object",
            "properties": {
                "table_key": {"type": "string", "description": "Known table key or omit"},
                "stats_data_id": {"type": "string", "description": "Raw e-Stat stats table ID"},
            },
        },
    ),
    types.Tool(
        name="list_school_districts",
        description="List nationwide school district (A27 Kokuto Suuchi Jhouhou) GML/GeoJSON files from nlftp.mlit.go.jp (MLIT National Geographical Information, keyless). Used for school-catchment real estate analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "prefecture": {"type": "string", "description": "Optional prefecture code filter (e.g. 13 for Tokyo) - filters file names"},
            },
        },
    ),
    types.Tool(
        name="get_school_district_geojson",
        description="Fetch school district GIS tile (XKT004) from MLIT Real Estate Information Library as GeoJSON. Requires REINFOLIB_API_KEY env var (free application). Tile coords: z=11..15, x/y from XYZ tiling at that zoom.",
        inputSchema={
            "type": "object",
            "properties": {
                "z": {"type": "integer", "description": "Zoom 11-15"},
                "x": {"type": "integer", "description": "Tile X"},
                "y": {"type": "integer", "description": "Tile Y"},
                "administrative_area_code": {"type": "string", "description": "Optional 5-digit admin area code (e.g. 13105 for Shibuya) - comma-separate for multiple"},
            },
            "required": ["z", "x", "y"],
        },
    ),
]


def _text(obj):
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(obj, ensure_ascii=False, indent=2))]
    )


def _error(text):
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps({"error": text}, ensure_ascii=False))],
        is_error=True,
    )


async def on_list_tools(ctx, params):
    return types.ListToolsResult(tools=TOOLS)


async def on_call_tool(ctx, params):
    name = params.name
    arguments = dict(params.arguments or {})
    try:
        if name == "geocode_japan":
            return _text(geocode_address(arguments["address"]))
        if name == "get_gsi_tile":
            res = get_tile(arguments["layer"], float(arguments["lat"]), float(arguments["lon"]), int(arguments["z"]))
            img = types.ImageContent(type="image", data=res.pop("image"), mimeType=res.pop("mime"))
            return types.CallToolResult(
                content=[img, types.TextContent(type="text", text=json.dumps(res, ensure_ascii=False, indent=2))]
            )
        if name == "list_data_sources":
            return _text(list_data_sources())
        if name == "get_estat_data":
            return _text(get_e_stat_data(
                stats_data_id=arguments.get("stats_data_id"),
                table_key=arguments.get("table_key"),
                cdCat01=arguments.get("cd_cat01"),
                cdCat02=arguments.get("cd_cat02"),
                cdCat03=arguments.get("cd_cat03"),
            ))
        if name == "get_estat_meta":
            return _text(get_e_stat_meta(table_key=arguments.get("table_key"), stats_data_id=arguments.get("stats_data_id")))
        if name == "list_school_districts":
            res = list_school_districts(prefecture=arguments.get("prefecture"))
            if arguments.get("prefecture"):
                code = str(arguments["prefecture"]).zfill(2)
                res["files"] = [f for f in res["files"] if code in f["file"]]
            return _text(res)
        if name == "get_school_district_geojson":
            res = get_reinfolib_xkt004(int(arguments["z"]), int(arguments["x"]), int(arguments["y"]), response_format="geojson")
            if arguments.get("administrative_area_code"):
                res["note"] = f"administrative_area_code={arguments['administrative_area_code']} - pass via API param"
            return _text(res)
        return _error(f"Unknown tool: {name}")
    except ValueError as e:
        return _error(str(e))
    except requests.exceptions.RequestException as e:
        return _error(f"HTTP error: {e}")
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


server = Server("japan-geospatial-open-data-mcp", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
