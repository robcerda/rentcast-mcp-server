# RentCast MCP Server

Model Context Protocol (MCP) server for connecting Claude with the RentCast API. It provides tools for every [RentCast API](https://developers.rentcast.io/reference) endpoint: property records, value and rent estimates with comparables, sale and rental listings, and market statistics.

## Requirements

* Python 3.12 or higher
* Model Context Protocol (MCP) Python SDK
* httpx
* python-dotenv

## Setup

### 1. Install uv (recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone this repository

```bash
git clone https://github.com/robcerda/rentcast-mcp-server.git
cd rentcast-mcp-server
```

### 3. Create and activate a virtual environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
# Option 1: Using uv (recommended)
uv sync

# Option 2: Using pip with requirements.txt
pip install -r requirements.txt

# Option 3: Install as editable package
uv pip install -e .
```

### 5. Set up environment variables

Create a `.env` file in the project root with your RentCast API key:

```bash
RENTCAST_API_KEY=your_api_key_here
```

Optionally, set `RENTCAST_SUPPRESS_LOGGING=true` to ask RentCast not to log your queries.

## Usage

### 1. Configure Claude Desktop

First, install the MCP CLI globally:

```bash
uv tool install "mcp[cli]"
```

Then add this server to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "RentCast": {
      "command": "/Users/<USERNAME>/.local/share/uv/tools/mcp/bin/mcp",
      "args": ["run", "/full/path/to/rentcast-mcp-server/src/rentcast_mcp_server/server.py"]
    }
  }
}
```

**Important**: Replace `/full/path/to/` with the actual absolute path to your `rentcast-mcp-server` directory.

Restart Claude Desktop after saving the configuration.

### 2. Use the MCP server with Claude

Once configured, Claude Desktop will have access to these RentCast tools:

* **`search_properties`**: Search property records (owner, tax assessments, sale history) by address, city, state, zip code, or radius
* **`get_random_properties`**: Get a random sample of property records
* **`get_property`**: Get a single property record by id
* **`get_value_estimate`**: Get a property value estimate with comparable sales
* **`get_rent_estimate`**: Get a long-term rent estimate with comparable rentals
* **`search_sale_listings`**: Search for-sale listings
* **`get_sale_listing`**: Get a single sale listing by id
* **`search_rental_listings`**: Search long-term rental listings
* **`get_rental_listing`**: Get a single rental listing by id
* **`get_market_statistics`**: Get sale and rental market statistics and history for a zip code

The search tools accept RentCast's [query syntax](https://developers.rentcast.io/reference/search-queries): multiple values with `|` (`Condo|Townhouse`) and ranges with `:` (`bedrooms=2:4`, `price=*:500000`). Results are paginated up to 500 at a time with `limit` and `offset`.

It also provides two prompts, `property_analysis` and `market_overview`.

**Example queries to try with Claude:**
- "What is 5500 Grand Lake Dr, San Antonio, TX 78244 worth, and what would it rent for?"
- "Find 3 bedroom houses for sale under $500k in 78704 listed in the last 30 days"
- "Show rental market trends in ZIP code 90210 over the last year"

## Development

### Running the server locally

To start the server manually (useful when developing or testing), run:

```bash
rentcast-mcp
```

Alternatively, you can run it directly with:

```bash
uv run python src/rentcast_mcp_server/server.py
```

### Installing MCP CLI globally

If you want to use `mcp run` commands, install the MCP CLI globally:

```bash
uv tool install "mcp[cli]"
```

Then you can run:

```bash
mcp run src/rentcast_mcp_server/server.py
```

## License

MIT
