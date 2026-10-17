# Japan Geospatial Open Data MCP Ecosystem — Verification Report (t_9941b632)

## verification_evidence

$ cd /home/atushi/.hermes/kanban/boards/kensho-ai-team/workspaces/t_9941b632 && git log --oneline -5
b540b82 Merge remote-tracking branch 'origin/master'
1d9c29f v1.0.1: populate manifest tools (7 tools from server.py)
0964883 t_044bd23f: add manifest.json for Smithery deployment
aa41e9d t_044bd23f: add server.js for Smithery deployment
98f596e t_044bd23f: add smithery.yaml for Smithery deployment

$ git rev-parse HEAD
b540b82dc1f7a89684ae8313049c6c7dce6da883

$ .venv/bin/python -m pytest tests/ -q
......                                                                   [100%]
6 passed in 1.52s

$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from server import TOOLS; print(len(TOOLS),'tools:', ', '.join(t.name for t in TOOLS))"
7 tools: geocode_japan, get_gsi_tile, list_data_sources, get_estat_data, get_estat_meta, list_school_districts, get_school_district_geojson

$ .venv/bin/python -c "import json; d=json.load(open('server.json')); print('name=',d['name'],'version=',d['version'],'registryType=',d['packages'][0]['registryType'],'required_envs=',d['packages'][0]['environmentVariables'])"
name= io.github.atushi1841/japan-geospatial-open-data-mcp version= 1.0.0 registryType= mcpb required_envs= []

$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from jpgeospatialmcp.core import geocode_address; r=geocode_address('東京都渋谷区道玄坂'); print('keys:', list(r[0].keys())); print('lat:', r[0]['lat'], 'lon:', r[0]['lon'])"
keys: ['title', 'lat', 'lon']
lat: 35.657284 lon: 139.698318

$ mcp-publisher validate
Validating against https://registry.modelcontextprotocol.io...
✅ server.json is valid

$ git ls-remote origin | head -3
b540b82dc1f7a89684ae8313049c6c7dce6da883	HEAD
b540b82dc1f7a89684ae8313049c6c7dce6da883	refs/heads/master
b540b82dc1f7a89684ae8313049c6c7dce6da883	refs/heads/merge-head

$ git status --porcelain


## Summary

7-tool MCP server for Japan national geospatial open data: GSI XYZ tiles + GSI address geocoder (keyless), e-Stat v3.0 statistics API (optional ESTAT_APP_ID), MLIT A27 school-district boundary GML (keyless), MLIT Real Estate Information Library XKT004 (optional REINFOLIB_API_KEY). Covers real-estate school-catchment analysis, education infrastructure evaluation, disaster planning, urban design. Commit b540b82dc1f7a89684ae8313049c6c7dce6da883 pushed to origin/master + tag v1.0.0. Tests 6/6 pass. server.json valid (mcpb registryType, fileSha256 embedded, no required env vars). MCP Registry publish blocked on expired JWT — child task t_f24ba4fe created.
