# Keep the uv version aligned with .github/workflows/ci.yml.
FROM ghcr.io/astral-sh/uv:0.12.10-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    RENTCAST_MCP_TRANSPORT=streamable-http \
    RENTCAST_MCP_HOST=0.0.0.0 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install locked runtime dependencies separately so source changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md LICENSE ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000
CMD ["rentcast-mcp"]
