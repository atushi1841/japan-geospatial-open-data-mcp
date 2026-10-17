# Japan Geospatial Open Data MCP Server
# Containerized MCP server exposing GSI tiles/geocoding, e-Stat statistics,
# and MLIT school district GIS to any MCP client.
FROM python:3.12-slim

# Registry ownership is declared via the LABEL below; the Official MCP Registry
# validates the image manifest against this annotation on publish.
LABEL io.modelcontextprotocol.server.name="io.github.atushi1841/japan-geospatial-open-data-mcp"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/jpgeospatialmcp/ ./jpgeospatialmcp/
COPY src/server.py ./server.py

ENV PYTHONPATH=/app
ENV USER_AGENT="japan-geospatial-open-data-mcp/1.0 (+https://github.com/atushi1841/japan-geospatial-open-data-mcp)"

ENTRYPOINT ["python", "/app/server.py"]