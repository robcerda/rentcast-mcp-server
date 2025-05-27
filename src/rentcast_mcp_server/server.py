"""
RentCast MCP Server

This module implements a Model Context Protocol (MCP) server for connecting
Claude with the RentCast API. It provides tools for retrieving property
data, valuations, and market statistics.

Main Features:
    - Property data retrieval
    - Property valuations
    - Rent estimates
    - Market statistics
    - Error handling with user-friendly messages
    - Configurable parameters with environment variable support

Usage:
    This server is designed to be run as a standalone script and exposes several MCP tools
    for use with Claude Desktop or other MCP-compatible clients. The server loads configuration
    from environment variables (optionally via a .env file) and communicates with the RentCast API.

    To run the server:
        $ python src/rentcast_mcp_server/server.py

    MCP tools provided:
        - get_property_data
        - get_property_valuation
        - get_rent_estimate
        - get_market_statistics
        - get_property_listings

    See the README for more details on configuration and usage.
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import httpx

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("rentcast_mcp_server")

# Load environment variables
load_dotenv()

# Get API key from environment
RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
if not RENTCAST_API_KEY:
    raise ValueError("RENTCAST_API_KEY environment variable is required")

# Initialize FastMCP server
mcp = FastMCP("rentcast-mcp")

# HTTP client will be initialized in main

async def get_http_client():
    """Get or create HTTP client with proper headers."""
    return httpx.AsyncClient(
        base_url="https://api.rentcast.io/v1",
        headers={"X-Api-Key": RENTCAST_API_KEY},
        timeout=30.0
    )

@mcp.tool()
async def get_property_data(property_id: str) -> Dict:
    """Get detailed information about a specific property."""
    async with await get_http_client() as client:
        try:
            response = await client.get(f"/properties/{property_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting property {property_id}: {str(e)}")
            raise

@mcp.tool()
async def get_property_valuation(property_id: str) -> Dict:
    """Get valuation data for a specific property."""
    async with await get_http_client() as client:
        try:
            response = await client.get(f"/properties/{property_id}/valuation")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting valuation for property {property_id}: {str(e)}")
            raise

@mcp.tool()
async def get_rent_estimate(property_id: str) -> Dict:
    """Get rent estimate for a specific property."""
    async with await get_http_client() as client:
        try:
            response = await client.get(f"/properties/{property_id}/rent-estimate")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting rent estimate for property {property_id}: {str(e)}")
            raise

@mcp.tool()
async def get_market_statistics(
    zip_code: str,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None
) -> Dict:
    """Get market statistics for a specific area."""
    async with await get_http_client() as client:
        try:
            params = {
                "zipCode": zip_code,
                "propertyType": property_type,
                "bedrooms": bedrooms
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get("/market-statistics", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting market statistics: {str(e)}")
            raise

@mcp.tool()
async def get_property_listings(
    zip_code: str,
    property_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    bedrooms: Optional[int] = None
) -> Dict:
    """Get property listings for a specific area."""
    async with await get_http_client() as client:
        try:
            params = {
                "zipCode": zip_code,
                "propertyType": property_type,
                "minPrice": min_price,
                "maxPrice": max_price,
                "bedrooms": bedrooms
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get("/properties", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting property listings: {str(e)}")
            raise

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting RentCast MCP Server...")
    try:
        # API key check before starting the server
        if not RENTCAST_API_KEY:
            logger.error("RENTCAST_API_KEY environment variable is not set")
            print("RENTCAST_API_KEY environment variable is not set", file=sys.stderr)
            sys.exit(1)
            
        logger.info("API key found. Starting server...")
        mcp.run()
    except Exception as e:
        print(f"Failed to run server: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main() 