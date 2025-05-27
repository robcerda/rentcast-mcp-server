# RentCast MCP Server

Model Context Protocol (MCP) server for connecting Claude with the RentCast API. It provides tools for accessing property data, valuations, and market statistics through the RentCast API.

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
git clone https://github.com/yourusername/rentcast-mcp-server.git
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

* **`get_property_data`**: Get detailed property data for a specific property ID
* **`get_property_valuation`**: Get property value estimates
* **`get_rent_estimate`**: Get rent estimates for a property
* **`get_market_statistics`**: Get market statistics for a ZIP code area
* **`get_property_listings`**: Get active property listings in a ZIP code area

**Example queries to try with Claude:**
- "Get market statistics for ZIP code 90210"
- "Show property listings in ZIP code 10001"
- "What are the market trends in ZIP code 02101?"

## Development and testing

Install development dependencies and run the test suite with:

```bash
uv sync --all-extras
pytest -v tests
```

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
