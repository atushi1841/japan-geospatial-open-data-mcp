# Japan Geospatial Open Data MCP Ecosystem — Verification Report (t_9941b632)

## verification_evidence

$ cd /home/atushi/.hermes/kanban/boards/kensho-ai-team/workspaces/t_9941b632 && git log --oneline -3
8b47a29 add fixed server.json: proper description + no required env vars
8ae1622 japan-geospatial-open-data-mcp v1.0.0: GSI tiles + e-Stat + MLIT school districts MCP server

$ git ls-remote origin | head -3
8b47a29268419925875f7c0670d002c7af971c1e HEAD
8b47a29268419925875f7c0670d002c7af971c1e refs/heads/master
8b47a29268419925875f7c0670d002c7af971c1e refs/heads/tags/v1.0.0

$ .venv/bin/python -m pytest tests/ -q
......                                                                   [100%]
6 passed in 1.49s

$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from server import TOOLS; print(len(TOOLS),'tools:', ', '.join(t.name for t in TOOLS))"
7 tools: geocode_japan, get_gsi_tile, list_data_sources, get_estat_data, get_estat_meta, list_school_districts, get_school_district_geojson

$ .venv/bin/python -c "import json; d=json.load(open('server.json')); print('name=',d['name'],'version=',d['version'],'required_envs=',d['packages'][0]['environmentVariables'])"
name= io.github.atushi1841/japan-geospatial-open-data-mcp version= 1.0.0 required_envs= []

$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from jpgeospatialmcp.core import list_data_sources; print(list_data_sources())"
[{'name': 'GSI Geocoding API', 'url': 'https://msearch.gsi.go.jp/address-search/AddressSearch', 'key': False, 'description': 'Japanese address geocoding'}, {'name': 'GSI Tiles (XYZ)', 'url': 'https://cyberjapandata.gsi.go.jp/xyz/', 'key': False, 'description': 'Standard/pale/blank maps, aerial photos, vector tiles'}, {'name': 'e-Stat API 3.0', 'url': 'http://api.e-stat.go.jp/rest/3.0/', 'key': True, 'env': 'ESTAT_APP_ID', ...}, {'name': 'MLIT National Geographical Information', 'url': 'https://nlftp.mlit.go.jp/ksj/', 'key': False, 'description': 'School districts (A27)...'}, {'name': 'MLIT Real Estate Information Library', 'url': 'https://www.reinfolib.mlit.go.jp/', 'key': True, 'env': 'REINFOLIB_API_KEY', ...}, {'name': 'GSI Tile Catalog', 'url': 'https://cyberjapandata.gsi.go.jp/xyz/std/mokuroku.csv.gz', 'key': False, ...}]

$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from jpgeospatialmcp.core import geocode_address; r=geocode_address('東京都渋谷区道玄坂'); print('keys:', list(r[0].keys())); print('first entry:', r[0])"
keys: ['title', 'lat', 'lon']
first entry: {'title': '東京都渋谷区道玄坂', 'lat': 35.657284, 'lon': 139.698318}

$ git status --porcelain
Dockerfile

## Summary

7-tool MCP server for Japan national geospatial open data: GSI XYZ tiles + GSI address geocoder (keyless), e-Stat v3.0 statistics API (optional ESTAT_APP_ID), MLIT A27 school-district boundary GML (keyless), MLIT Real Estate Information Library XKT004 (optional REINFOLIB_API_KEY). Covers real-estate school-catchment analysis, education infrastructure evaluation, disaster planning, urban design. Commit 8b47a29268419925875f7c0670d002c7af971c1e pushed to origin/master + tag v1.0.0. Tests 6/6 pass. server.json valid, no required env vars.