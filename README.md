# japan-geospatial-open-data-mcp

日本全国規模のジオスパティアル・オープンデータを AI エージェントに届ける MCP Server。
GSI 地理院タイル・地理院住所検索・e-Stat 統計 API・国土数値情報（小学校区）・不動産情報ライブラリを 1 つの MCP でまとめて公開する。

> **Context:** FOSS4G Hiroshima 2026 発表「Building an MCP Server Ecosystem on Japan's National-Scale Geospatial Open Data Platform」(Mami Enomoto, MLIT) が示した方向性に追従するエコシステム構築タスク。
> **Needs:** 不動産分析（学区・用途地域）・教育インフラ評価・防災・都市計画。
> **TOS:** GSI/e-Stat/国土数値情報は公式オープンデータ・再利用自由。

## Tools (7)

| Tool | Description | Key required |
| --- | --- | --- |
| `geocode_japan` | 住所 → 緯度経度（GSI 住所検索 API, msearch.gsi.go.jp） | No |
| `get_gsi_tile` | 地理院 XYZ タイル（std/pale/blank/aerial/vector）を base64 画像で取得 | No |
| `list_data_sources` | アクセス可能な全データソース一覧と鍵要件 | No |
| `get_estat_data` | e-Stat 統計データ取得（人口・人口動態・世帯 etc.） | `ESTAT_APP_ID` |
| `get_estat_meta` | e-Stat 統計表メタ情報取得 | `ESTAT_APP_ID` |
| `list_school_districts` | 全国小学校区 (A27) GML/GeoJSON ファイル一覧（国土数値情報, nlftp.mlit.go.jp） | No |
| `get_school_district_geojson` | 小学校区 GIS タイル (XKT004) GeoJSON 取得（不動産情報ライブラリ） | `REINFOLIB_API_KEY` |

### Environment variables (optional)

- `ESTAT_APP_ID` — e-Stat application ID (free: https://www.e-stat.go.jp/api/)
- `REINFOLIB_API_KEY` — MLIT Real Estate Information Library API key (application: https://www.reinfolib.mlit.go.jp/)
- `USER_AGENT` — override default User-Agent string

**No keys → core GSI + school district listing still works out of the box.**

## Install

```bash
git clone https://github.com/atushi1841/japan-geospatial-open-data-mcp
cd japan-geospatial-open-data-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "japan-geospatial-open-data": {
      "command": "/path/to/japan-geospatial-open-data-mcp/.venv/bin/python",
      "args": ["/path/to/japan-geospatial-open-data-mcp/src/server.py"],
      "env": {
        "ESTAT_APP_ID": "your-e-stat-app-id",
        "REINFOLIB_API_KEY": "your-reinfolib-key"
      }
    }
  }
}
```

## Example queries

- 「東京都渋谷区の小学校区はどれか」 → `geocode_japan("東京都渋谷区")` → `list_school_districts`
- 「渋谷区の航空写真 2024 年をズーム 15 で表示」 → `get_gsi_tile(layer="nendophoto2024", lat=35.657, lon=139.698, z=15)`
- 「日本の 2020 年人口（年齢別）」 → `get_estat_data(table_key="population")`
- 「地価公示ポイントの GeoJSON」 → (future: `get_reinfolib_xkt004` 系)

## Data sources & licensing

| Source | URL | License |
| --- | --- | --- |
| GSI tiles & geocoder | https://maps.gsi.go.jp/ | GSI tile terms (free, credit required) |
| e-Stat API | https://www.e-stat.go.jp/api/ | Open statistics (free, key registration) |
| MLIT Kokuto Suuchi Jhouhou | https://nlftp.mlit.go.jp/ksj/ | MLIT open data (free) |
| MLIT Real Estate Information Library | https://www.reinfolib.mlit.go.jp/ | MLIT open data (free, application) |

**Credit requirement:** when using GSI tiles, include "Geospatial Information Authority of Japan" in your output.

## MCP Registry

Publishing to the official [MCP Registry](https://registry.modelcontextprotocol.io/) is a follow-up task.
The `mcp-publisher` CLI (GitHub auth, `io.github.atushi1841/japan-geospatial-open-data-mcp` namespace) is the standard flow.

## Roadmap / future tools

- 用途地域 (zoning) GeoJSON from reinfolib
- 洪水浸水想定区域 / 土砂災害警戒区域 hazard layers (reinfolib)
- 地価公示 point API
- e-Stat 250m mesh population for density analysis
- 中学校区 (A28) listing
- Bulk GeoJSON download helper for nlftp files (A27 prefecture-level GML)
