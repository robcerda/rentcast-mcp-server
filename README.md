# RentCast MCP Server

A Model Context Protocol (MCP) server for the [RentCast API](https://developers.rentcast.io/reference). It gives Claude Desktop, Claude Code, and other MCP clients access to US property records, value and rent estimates with comparables, sale and rental listings, and market statistics.

You need a RentCast API key. Create one on your [RentCast API dashboard](https://app.rentcast.io/app/api).

## 🚀 Quick Start

There are three ways to run the server:

1. **[Claude Desktop extension](#1-claude-desktop-extension)**: one file, no terminal needed.
2. **[Local installation](#2-local-installation)**: clone the repo and point Claude Desktop or Claude Code at it.
3. **[Containerized deployment](#containerized-deployment)**: run it as an HTTP server with Docker.

### 1. Claude Desktop Extension

1. Build the extension (or download `rentcast-mcp.mcpb` from a release):
   ```bash
   npx @anthropic-ai/mcpb pack . rentcast-mcp.mcpb
   ```
2. Double-click `rentcast-mcp.mcpb`, or drag it into Claude Desktop's **Settings > Extensions**.
3. Enter your RentCast API key when prompted. Claude Desktop stores it as a sensitive setting.

The extension uses the MCPB `uv` server type: Claude Desktop installs the pinned dependencies from `uv.lock` on first launch, so you do not need Python installed yourself.

### 2. Local Installation

1. **Install uv** (recommended):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone this repository**:
   ```bash
   git clone https://github.com/robcerda/rentcast-mcp-server.git
   cd rentcast-mcp-server
   ```

3. **Install dependencies**:

   **Using `uv`** (recommended):
   ```bash
   uv sync --locked
   ```

   `--locked` installs exactly what `uv.lock` pins, verified against the hashes it records, and refuses to re-resolve.

   **Using `pip`**:
   ```bash
   pip install -r requirements-lock.txt --require-hashes
   pip install -e . --no-deps
   ```

   `requirements-lock.txt` is generated from `uv.lock` and pins every dependency with hashes, so the pip path installs the same set as the uv one. `pip install -r requirements.txt` still works and installs exactly the same set.

4. **Set your API key**. Create a `.env` file in the project root:
   ```bash
   RENTCAST_API_KEY=your_api_key_here
   ```
   Or pass it in the `env` block of the client configuration below.

5. **Configure Claude Desktop**:
   Add this to your Claude Desktop configuration file:

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "RentCast": {
         "command": "/opt/homebrew/bin/uv",
         "args": [
           "run",
           "--locked",
           "--project",
           "/path/to/your/rentcast-mcp-server",
           "rentcast-mcp"
         ],
         "env": {
           "RENTCAST_API_KEY": "your_api_key_here"
         }
       }
     }
   }
   ```

   **Important**: Replace `/path/to/your/rentcast-mcp-server` with your actual path, and `/opt/homebrew/bin/uv` with the output of `which uv`.

   Restart Claude Desktop after saving the configuration.

   **OR configure Claude Code**:
   ```bash
   claude mcp add rentcast -e RENTCAST_API_KEY=your_api_key_here -- \
     uv run --locked --project /path/to/your/rentcast-mcp-server rentcast-mcp
   ```

   **If installed via `pip`** instead of `uv`, use:
   ```json
   {
     "command": "python",
     "args": ["/path/to/your/rentcast-mcp-server/src/rentcast_mcp_server/server.py"]
   }
   ```

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `RENTCAST_API_KEY` | Yes | Your RentCast API key |
| `RENTCAST_SUPPRESS_LOGGING` | No | `true` asks RentCast not to log your queries and query parameters |
| `RENTCAST_MCP_TRANSPORT` | No | `stdio` (default), `streamable-http`, or `http` |
| `RENTCAST_MCP_HOST` | No | HTTP bind address (default `127.0.0.1`) |
| `RENTCAST_MCP_PORT` | No | HTTP port (default `8000`) |
| `RENTCAST_MCP_ALLOWED_HOSTS` | No | Extra `Host` values to accept over HTTP, comma-separated |
| `RENTCAST_MCP_ALLOWED_ORIGINS` | No | Extra browser `Origin` values to accept over HTTP, comma-separated |

Each HTTP setting also has a command line flag: `rentcast-mcp --help`.

## Containerized Deployment

```bash
docker build -t rentcast-mcp .
docker run --rm -p 8000:8000 -e RENTCAST_API_KEY=your_api_key_here rentcast-mcp
```

The image serves streamable HTTP on port 8000 at `/mcp`. Host and Origin validation stay on even when bound to `0.0.0.0`, so a client reaching it by a public name needs that name allowed:

```bash
docker run --rm -p 8000:8000 \
  -e RENTCAST_API_KEY=your_api_key_here \
  -e RENTCAST_MCP_ALLOWED_HOSTS=mcp.example.com \
  rentcast-mcp
```

The HTTP transport has no authentication of its own. Anyone who can reach the port can spend your RentCast quota, so put it behind a VPN or an authenticating reverse proxy if it is reachable from outside your machine.

## ✨ Features

### 🏠 Property Records
Public records for 150M+ US properties: attributes, owner, tax assessments, sale history, and features. Look up one address, or search by city, state, zip code, or a radius around a point.

### 💰 Value and Rent Estimates
RentCast's automated valuation model returns a value or long-term rent estimate with a range and the comparable listings used to calculate it. Tune the comps with `comp_count`, `max_radius` and `days_old`, or override the subject property's attributes.

### 📋 Sale and Rental Listings
Active and inactive for-sale and long-term rental listings, with price, listing dates, agent and office details, and listing history.

### 📈 Market Statistics
Sale and rental statistics for any zip code: average, median, min and max price and rent, price per square foot, days on market, listing counts, breakdowns by property type and bedrooms, and monthly history.

### 🔍 Search Queries
Search tools accept RentCast's [query syntax](https://developers.rentcast.io/reference/search-queries):

* Multiple values with `|`: `property_type="Condo|Townhouse"`, `bedrooms="2|3"`
* Inclusive ranges with `:` and `*` for an open end: `bedrooms="2:4"`, `price="*:500000"`, `year_built="2000:*"`
* Up to 500 results per request, paged with `limit` and `offset`. Set `include_total_count` to get the total number of matches.

## 🛠️ Available Tools

| Tool | Description | RentCast endpoint |
| --- | --- | --- |
| `search_properties` | Search property records | `/properties` |
| `get_random_properties` | Random sample of property records | `/properties/random` |
| `get_property` | One property record by id | `/properties/{id}` |
| `get_value_estimate` | Value estimate with comparable sales | `/avm/value` |
| `get_rent_estimate` | Long-term rent estimate with comparable rentals | `/avm/rent/long-term` |
| `search_sale_listings` | Search for-sale listings | `/listings/sale` |
| `get_sale_listing` | One sale listing by id | `/listings/sale/{id}` |
| `search_rental_listings` | Search long-term rental listings | `/listings/rental/long-term` |
| `get_rental_listing` | One rental listing by id | `/listings/rental/long-term/{id}` |
| `get_market_statistics` | Market statistics and history for a zip code | `/markets` |

Search tools return `{count, limit, offset, hasMore, results}`, plus `totalCount` when requested.

**Prompts**: `property_analysis` (value, rent, comps and market for an address) and `market_overview` (a zip code's sale and rental market).

## 📝 Usage Examples

### Value and Rent for an Address
```
What is 5500 Grand Lake Dr, San Antonio, TX 78244 worth, and what would it rent for?
```

### Find Listings
```
Find 3 bedroom houses for sale under $500k in 78704 listed in the last 30 days
```

### Rental Market Trends
```
Show rental market trends in ZIP code 90210 over the last year
```

### Investment Analysis
```
Compare the gross rental yield of condos and single family homes for sale in 33131
```

## 🔧 Troubleshooting

### `RentCast API error 401`
The API key is missing or invalid. Check `RENTCAST_API_KEY`, or re-enter the key in the extension settings.

### `RentCast API error 403`
The key is restricted to other endpoints or IP addresses, or there is a billing issue. Check your [API dashboard](https://app.rentcast.io/app/api).

### `RentCast API error 429`
RentCast allows 20 requests per second per key. The server retries rate limited requests with backoff before reporting this.

### Empty search results
RentCast reports "no results" as an empty `results` list. `city` and `state` are case-sensitive, and `property_type` must match exactly, e.g. `Single Family`.

### Server disconnects on startup
Check the client's MCP logs. The most common cause is a missing `RENTCAST_API_KEY`, which makes the server exit immediately.

## Development

```bash
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
```

The tests run against a fake RentCast API and never make real requests.

### Running the server locally

```bash
uv run rentcast-mcp
```

To use the MCP Inspector:

```bash
uv run mcp dev src/rentcast_mcp_server/server.py
```

### Updating dependencies

```bash
uv lock --upgrade-package <name>
uv export --frozen --no-emit-project --no-editable --no-dev \
  --format requirements-txt --output-file requirements-lock.txt
```

CI fails if `uv.lock`, `requirements-lock.txt`, and `requirements.txt` drift apart.

### Building the extension

```bash
npx @anthropic-ai/mcpb validate manifest.json
npx @anthropic-ai/mcpb pack . rentcast-mcp.mcpb
```

`.mcpbignore` keeps tests, CI files and local environments out of the bundle. When you add or rename a tool, update the `tools` list in `manifest.json`; a test checks that it matches the server.

## License

MIT
