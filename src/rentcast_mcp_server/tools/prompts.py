"""Prompt templates for common RentCast workflows."""

from rentcast_mcp_server.app import mcp

PROPERTY_ANALYSIS = (
    "Please analyze the property at {address}. Include:\n"
    "1. The property record (attributes, last sale, tax assessment)\n"
    "2. Current value estimate and rent estimate, with their comparables\n"
    "3. Market statistics for the property's zip code\n"
    "4. Estimated gross rental yield and price to rent ratio\n\n"
    "Provide insights on whether this is a good investment opportunity."
)

MARKET_OVERVIEW = (
    "Provide a comprehensive market overview for zip code {zip_code}. Include:\n"
    "1. Sale and rental market statistics (average and median price, rent, price per sq ft)\n"
    "2. Trends over the last 12 months\n"
    "3. A sample of current active sale and rental listings\n"
    "4. Key insights for buyers, renters, and investors"
)


@mcp.prompt()
def property_analysis(address: str) -> str:
    """Analyze a property's value, rent, comparables, and local market."""
    return PROPERTY_ANALYSIS.format(address=address)


@mcp.prompt()
def market_overview(zip_code: str) -> str:
    """Get a comprehensive market overview for a zip code."""
    return MARKET_OVERVIEW.format(zip_code=zip_code)
