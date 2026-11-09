# Runs the server on Linux for MCP introspection checks (e.g. Glama).
# Window capture itself needs macOS; on Linux those tools return a clear error.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY . .
RUN uv pip install --system --no-cache .
ENV SHOTLOG_DIR=/data
CMD ["shotlog-mcp"]
