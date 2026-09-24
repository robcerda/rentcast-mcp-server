"""
RentCast MCP Server

This module implements a Model Context Protocol (MCP) server for connecting
Claude with the RentCast API (https://developers.rentcast.io/reference).
It covers every RentCast API v1 endpoint: property records, value and rent
estimates (with comparables), sale and rental listings, and market statistics.

Usage:
    This server is designed to be run as a standalone script and exposes several MCP tools
    for use with Claude Desktop or other MCP-compatible clients. The server loads configuration
    from environment variables (optionally via a .env file) and communicates with the RentCast API.

    To run the server:
        $ python src/rentcast_mcp_server/server.py

    MCP tools provided:
        - search_properties                /properties
        - get_random_properties            /properties/random
        - get_property                     /properties/{id}
        - get_value_estimate               /avm/value
        - get_rent_estimate                /avm/rent/long-term
        - search_sale_listings             /listings/sale
        - get_sale_listing                 /listings/sale/{id}
        - search_rental_listings           /listings/rental/long-term
        - get_rental_listing               /listings/rental/long-term/{id}
        - get_market_statistics            /markets

    Environment variables:
        RENTCAST_API_KEY            required, your RentCast API key
        RENTCAST_SUPPRESS_LOGGING   optional, "true" asks RentCast not to log query parameters

    See the README for more details on configuration and usage.
"""

import asyncio
import logging
import os
import sys
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Configure logging to stderr (stdout is reserved for the MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("rentcast_mcp_server")

# Load environment variables
load_dotenv()

RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
SUPPRESS_LOGGING = os.getenv("RENTCAST_SUPPRESS_LOGGING", "").lower() in ("1", "true", "yes")
BASE_URL = "https://api.rentcast.io/v1"
MAX_RETRIES = 3

# Initialize FastMCP server
mcp = FastMCP("rentcast-mcp")

_client: Optional[httpx.AsyncClient] = None


class RentCastError(Exception):
    """Raised when the RentCast API returns an error. The message is shown to the model."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def get_http_client() -> httpx.AsyncClient:
    """Get the shared HTTP client, creating it on first use."""
    global _client
    if not RENTCAST_API_KEY:
        raise RentCastError(
            "RENTCAST_API_KEY environment variable is not set. "
            "Get a key at https://app.rentcast.io/app/api"
        )
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"X-Api-Key": RENTCAST_API_KEY, "Accept": "application/json"},
            timeout=30.0,
        )
    return _client


def _error_message(response: httpx.Response) -> str:
    """Build a readable error from a RentCast error response."""
    try:
        body = response.json()
        detail = body.get("message") or body.get("error") or response.text
    except ValueError:
        detail = response.text or response.reason_phrase
    hints = {
        401: "Check that RENTCAST_API_KEY is valid.",
        403: "The API key is restricted, or the subscription or billing is inactive.",
        429: "Rate limit of 20 requests per second exceeded.",
    }
    hint = hints.get(response.status_code)
    message = f"RentCast API error {response.status_code}: {detail}"
    return f"{message} ({hint})" if hint else message


async def rentcast_get(path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
    """
    Perform a GET request against the RentCast API.

    None values are dropped from params. Rate limited requests (429) are retried
    with backoff. Any other non-2xx response raises RentCastError with the API's message.
    """
    client = get_http_client()
    query = {k: v for k, v in (params or {}).items() if v is not None}
    if SUPPRESS_LOGGING:
        query["suppressLogging"] = True

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.get(path, params=query)
        except httpx.TimeoutException as e:
            raise RentCastError(f"Request to RentCast timed out: {path}") from e
        except httpx.HTTPError as e:
            raise RentCastError(f"Could not reach RentCast: {e}") from e

        if response.status_code == 429 and attempt < MAX_RETRIES:
            delay = 2**attempt
            logger.warning(f"Rate limited on {path}, retrying in {delay}s")
            await asyncio.sleep(delay)
            continue
        break

    if response.is_success:
        return response
    logger.error(f"GET {path} failed with {response.status_code}")
    raise RentCastError(_error_message(response), response.status_code)


async def search(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a paginated search query and wrap the results with pagination info.

    RentCast returns 404 when nothing matches, which is reported as an empty result set.
    """
    try:
        response: Optional[httpx.Response] = await rentcast_get(path, params)
    except RentCastError as e:
        if e.status_code != 404:
            raise
        response = None

    results: List[Dict[str, Any]] = response.json() if response is not None else []
    headers = response.headers if response is not None else {}
    limit = int(headers.get("X-Limit", params.get("limit") or 50))
    data: Dict[str, Any] = {
        "count": len(results),
        "limit": limit,
        "offset": int(headers.get("X-Offset", params.get("offset") or 0)),
        "hasMore": len(results) >= limit,
        "results": results,
    }
    if "X-Total-Count" in headers:
        data["totalCount"] = int(headers["X-Total-Count"])
    elif params.get("includeTotalCount"):
        data["totalCount"] = 0
    return data


async def get_by_id(path: str) -> Dict[str, Any]:
    """Fetch a single record by its RentCast id."""
    response = await rentcast_get(path)
    return response.json()


# Reusable parameter types. Range parameters accept a single value ("3"),
# multiple values separated by "|" ("2|3"), or an inclusive range separated
# by ":" with "*" for an open end ("2:4", "1500:*").
RangeValue = Optional[Union[str, int, float]]

Address = Annotated[
    Optional[str],
    Field(description="Full property address in the format 'Street, City, State, Zip'."),
]
City = Annotated[Optional[str], Field(description="City name (case-sensitive), e.g. 'Austin'.")]
State = Annotated[Optional[str], Field(description="2-letter state abbreviation, e.g. 'TX'.")]
ZipCode = Annotated[Optional[str], Field(description="5-digit zip code.")]
Latitude = Annotated[Optional[float], Field(description="Latitude of the search center.")]
Longitude = Annotated[Optional[float], Field(description="Longitude of the search center.")]
Radius = Annotated[
    Optional[float],
    Field(description="Search radius in miles (max 100). Use with address or latitude/longitude."),
]
PropertyType = Annotated[
    Optional[str],
    Field(
        description=(
            "Case-sensitive property type: 'Single Family', 'Condo', 'Townhouse', 'Manufactured', "
            "'Multi-Family' (2-4 units), 'Apartment' (5+ units), 'Land'. "
            "Separate multiple types with '|', e.g. 'Condo|Townhouse'."
        )
    ),
]
Bedrooms = Annotated[
    RangeValue,
    Field(description="Bedrooms, 0 for studio. Supports '2|3' or ranges like '2:4', '3:*'."),
]
Bathrooms = Annotated[
    RangeValue,
    Field(description="Bathrooms, fractions allowed. Supports '1|2' or ranges like '1.5:*'."),
]
SquareFootage = Annotated[
    RangeValue, Field(description="Living area in sq ft. Supports ranges like '1000:2000'.")
]
LotSize = Annotated[
    RangeValue, Field(description="Lot size in sq ft. Supports ranges like '5000:*'.")
]
YearBuilt = Annotated[
    RangeValue, Field(description="Year built. Supports ranges like '2000:*' or '1950:1980'.")
]
Limit = Annotated[
    Optional[int], Field(ge=1, le=500, description="Results per page, 1-500. Defaults to 50.")
]
Offset = Annotated[
    Optional[int],
    Field(ge=0, description="Index of the first result, for pagination. Use multiples of limit."),
]
IncludeTotalCount = Annotated[
    Optional[bool],
    Field(description="Return the total number of matches as totalCount. Slower, use sparingly."),
]
ListingStatus = Annotated[
    Optional[Literal["Active", "Inactive"]],
    Field(description="Listing status. Defaults to 'Active'."),
]
DaysOld = Annotated[
    RangeValue,
    Field(
        description=(
            "Days since the property was listed. A single value is a maximum; "
            "ranges like '30:90' are also supported."
        )
    ),
]


def _range(value: RangeValue) -> Optional[str]:
    """Convert a range parameter to the string form the API expects."""
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _location(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    radius: Optional[float],
) -> Dict[str, Any]:
    return {
        "address": address,
        "city": city,
        "state": state,
        "zipCode": zip_code,
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
    }


def _attributes(
    property_type: Optional[str],
    bedrooms: RangeValue,
    bathrooms: RangeValue,
    square_footage: RangeValue,
    lot_size: RangeValue,
    year_built: RangeValue,
) -> Dict[str, Any]:
    return {
        "propertyType": property_type,
        "bedrooms": _range(bedrooms),
        "bathrooms": _range(bathrooms),
        "squareFootage": _range(square_footage),
        "lotSize": _range(lot_size),
        "yearBuilt": _range(year_built),
    }


def _pagination(
    limit: Optional[int], offset: Optional[int], include_total_count: Optional[bool]
) -> Dict[str, Any]:
    return {"limit": limit, "offset": offset, "includeTotalCount": include_total_count or None}


# Property records


@mcp.tool()
async def search_properties(
    address: Address = None,
    city: City = None,
    state: State = None,
    zip_code: ZipCode = None,
    latitude: Latitude = None,
    longitude: Longitude = None,
    radius: Radius = None,
    property_type: PropertyType = None,
    bedrooms: Bedrooms = None,
    bathrooms: Bathrooms = None,
    square_footage: SquareFootage = None,
    lot_size: LotSize = None,
    year_built: YearBuilt = None,
    sale_date_range: Annotated[
        RangeValue,
        Field(
            description=(
                "Days since the property last sold. A single value is a maximum "
                "(e.g. 270 means sold in the last 270 days); ranges like '180:270' also work."
            )
        ),
    ] = None,
    limit: Limit = None,
    offset: Offset = None,
    include_total_count: IncludeTotalCount = None,
) -> Dict[str, Any]:
    """
    Search public property records (owner, tax assessments, sale history, features).

    Provide only an address to look up one property. For bulk searches use city/state,
    zip_code, or latitude/longitude (or address) with radius, plus optional filters.
    Results are paginated; use limit and offset to page through them.
    """
    params = {
        **_location(address, city, state, zip_code, latitude, longitude, radius),
        **_attributes(property_type, bedrooms, bathrooms, square_footage, lot_size, year_built),
        "saleDateRange": _range(sale_date_range),
        **_pagination(limit, offset, include_total_count),
    }
    return await search("/properties", params)


@mcp.tool()
async def get_random_properties(limit: Limit = None) -> Dict[str, Any]:
    """Get a random sample of property records from across the US (no filters supported)."""
    response = await rentcast_get("/properties/random", {"limit": limit})
    results = response.json()
    return {"count": len(results), "results": results}


@mcp.tool()
async def get_property(
    property_id: Annotated[
        str,
        Field(description="RentCast property id, e.g. '5500-Grand-Lake-Dr,-San-Antonio,-TX-78244'"),
    ],
) -> Dict[str, Any]:
    """Get a single property record by its RentCast id (the 'id' field from search results)."""
    return await get_by_id(f"/properties/{property_id}")


# Valuations


async def _estimate(
    path: str,
    address: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    property_type: Optional[str],
    bedrooms: Optional[float],
    bathrooms: Optional[float],
    square_footage: Optional[float],
    max_radius: Optional[float],
    days_old: Optional[int],
    comp_count: Optional[int],
    lookup_subject_attributes: Optional[bool],
) -> Dict[str, Any]:
    if not address and (latitude is None or longitude is None):
        raise RentCastError("Provide either an address or both latitude and longitude.")
    params = {
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "propertyType": property_type,
        "bedrooms": _range(bedrooms),
        "bathrooms": _range(bathrooms),
        "squareFootage": _range(square_footage),
        "maxRadius": max_radius,
        "daysOld": days_old,
        "compCount": comp_count,
        "lookupSubjectAttributes": lookup_subject_attributes,
    }
    response = await rentcast_get(path, params)
    return response.json()


EstimateAddress = Annotated[
    Optional[str],
    Field(description="Full address 'Street, City, State, Zip'. Required unless lat/long given."),
]
EstimateLatitude = Annotated[Optional[float], Field(description="Property latitude.")]
EstimateLongitude = Annotated[Optional[float], Field(description="Property longitude.")]
EstimateBedrooms = Annotated[
    Optional[float], Field(description="Override bedrooms of the subject property, 0 for studio.")
]
EstimateBathrooms = Annotated[
    Optional[float], Field(description="Override bathrooms of the subject property.")
]
EstimateSquareFootage = Annotated[
    Optional[float], Field(description="Override living area of the subject property in sq ft.")
]
MaxRadius = Annotated[
    Optional[float], Field(description="Maximum distance in miles between comps and the property.")
]
CompDaysOld = Annotated[
    Optional[int],
    Field(ge=1, description="Maximum days since comparable listings were last on the market."),
]
CompCount = Annotated[
    Optional[int],
    Field(ge=5, le=25, description="Number of comparables to use, 5-25. Defaults to 15."),
]
LookupSubjectAttributes = Annotated[
    Optional[bool],
    Field(
        description=(
            "Look up the subject property's attributes automatically. Defaults to true; "
            "explicit attribute arguments override the looked up values."
        )
    ),
]


@mcp.tool()
async def get_value_estimate(
    address: EstimateAddress = None,
    latitude: EstimateLatitude = None,
    longitude: EstimateLongitude = None,
    property_type: Annotated[
        Optional[
            Literal[
                "Single Family", "Condo", "Townhouse", "Manufactured", "Multi-Family",
                "Apartment", "Land",
            ]
        ],
        Field(description="Override the subject property type."),
    ] = None,
    bedrooms: EstimateBedrooms = None,
    bathrooms: EstimateBathrooms = None,
    square_footage: EstimateSquareFootage = None,
    max_radius: MaxRadius = None,
    days_old: CompDaysOld = None,
    comp_count: CompCount = None,
    lookup_subject_attributes: LookupSubjectAttributes = None,
) -> Dict[str, Any]:
    """
    Get the estimated market value (AVM) of a property, with a value range and the
    comparable sale listings used to calculate it.
    """
    return await _estimate(
        "/avm/value", address, latitude, longitude, property_type, bedrooms, bathrooms,
        square_footage, max_radius, days_old, comp_count, lookup_subject_attributes,
    )


@mcp.tool()
async def get_rent_estimate(
    address: EstimateAddress = None,
    latitude: EstimateLatitude = None,
    longitude: EstimateLongitude = None,
    property_type: Annotated[
        Optional[
            Literal[
                "Single Family", "Condo", "Townhouse", "Manufactured", "Multi-Family", "Apartment",
            ]
        ],
        Field(description="Override the subject property type."),
    ] = None,
    bedrooms: EstimateBedrooms = None,
    bathrooms: EstimateBathrooms = None,
    square_footage: EstimateSquareFootage = None,
    max_radius: MaxRadius = None,
    days_old: CompDaysOld = None,
    comp_count: CompCount = None,
    lookup_subject_attributes: LookupSubjectAttributes = None,
) -> Dict[str, Any]:
    """
    Get the estimated long-term monthly rent of a property, with a rent range and the
    comparable rental listings used to calculate it.
    """
    return await _estimate(
        "/avm/rent/long-term", address, latitude, longitude, property_type, bedrooms, bathrooms,
        square_footage, max_radius, days_old, comp_count, lookup_subject_attributes,
    )


# Listings


@mcp.tool()
async def search_sale_listings(
    address: Address = None,
    city: City = None,
    state: State = None,
    zip_code: ZipCode = None,
    latitude: Latitude = None,
    longitude: Longitude = None,
    radius: Radius = None,
    property_type: PropertyType = None,
    bedrooms: Bedrooms = None,
    bathrooms: Bathrooms = None,
    square_footage: SquareFootage = None,
    lot_size: LotSize = None,
    year_built: YearBuilt = None,
    status: ListingStatus = None,
    price: Annotated[
        RangeValue,
        Field(description="Listed price. Supports ranges like '300000:500000' or '*:400000'."),
    ] = None,
    days_old: DaysOld = None,
    limit: Limit = None,
    offset: Offset = None,
    include_total_count: IncludeTotalCount = None,
) -> Dict[str, Any]:
    """
    Search for-sale listings (price, listing dates, agent and office, listing history).

    Provide only an address to look up one listing. For bulk searches use city/state,
    zip_code, or latitude/longitude (or address) with radius, plus optional filters.
    Results are paginated; use limit and offset to page through them.
    """
    params = {
        **_location(address, city, state, zip_code, latitude, longitude, radius),
        **_attributes(property_type, bedrooms, bathrooms, square_footage, lot_size, year_built),
        "status": status,
        "price": _range(price),
        "daysOld": _range(days_old),
        **_pagination(limit, offset, include_total_count),
    }
    return await search("/listings/sale", params)


@mcp.tool()
async def get_sale_listing(
    listing_id: Annotated[
        str, Field(description="RentCast listing id, e.g. '3821-Hargis-St,-Austin,-TX-78723'.")
    ],
) -> Dict[str, Any]:
    """Get a single sale listing by its RentCast id (the 'id' field from search results)."""
    return await get_by_id(f"/listings/sale/{listing_id}")


@mcp.tool()
async def search_rental_listings(
    address: Address = None,
    city: City = None,
    state: State = None,
    zip_code: ZipCode = None,
    latitude: Latitude = None,
    longitude: Longitude = None,
    radius: Radius = None,
    property_type: PropertyType = None,
    bedrooms: Bedrooms = None,
    bathrooms: Bathrooms = None,
    square_footage: SquareFootage = None,
    lot_size: LotSize = None,
    year_built: YearBuilt = None,
    status: ListingStatus = None,
    price: Annotated[
        RangeValue,
        Field(description="Monthly rent. Supports ranges like '1500:2500' or '1200:*'."),
    ] = None,
    days_old: DaysOld = None,
    limit: Limit = None,
    offset: Offset = None,
    include_total_count: IncludeTotalCount = None,
) -> Dict[str, Any]:
    """
    Search long-term rental listings (rent, listing dates, agent and office, listing history).

    Provide only an address to look up one listing. For bulk searches use city/state,
    zip_code, or latitude/longitude (or address) with radius, plus optional filters.
    Results are paginated; use limit and offset to page through them.
    """
    params = {
        **_location(address, city, state, zip_code, latitude, longitude, radius),
        **_attributes(property_type, bedrooms, bathrooms, square_footage, lot_size, year_built),
        "status": status,
        "price": _range(price),
        "daysOld": _range(days_old),
        **_pagination(limit, offset, include_total_count),
    }
    return await search("/listings/rental/long-term", params)


@mcp.tool()
async def get_rental_listing(
    listing_id: Annotated[
        str, Field(description="RentCast listing id, e.g. '2005-Arborside-Dr,-Austin,-TX-78754'.")
    ],
) -> Dict[str, Any]:
    """Get a single long-term rental listing by its RentCast id."""
    return await get_by_id(f"/listings/rental/long-term/{listing_id}")


# Market data


@mcp.tool()
async def get_market_statistics(
    zip_code: Annotated[str, Field(description="5-digit US zip code.")],
    data_type: Annotated[
        Optional[Literal["All", "Sale", "Rental"]],
        Field(description="Which statistics to return. Defaults to 'All'."),
    ] = None,
    history_range: Annotated[
        Optional[int],
        Field(ge=1, description="Months of monthly history to include. Defaults to 12."),
    ] = None,
) -> Dict[str, Any]:
    """
    Get aggregate sale and rental market statistics for a zip code: average, median, min
    and max price and rent, price per sq ft, days on market, listing counts, breakdowns by
    property type and bedrooms, and monthly history.
    """
    params = {"zipCode": zip_code, "dataType": data_type, "historyRange": history_range}
    response = await rentcast_get("/markets", params)
    return response.json()


# Prompts


@mcp.prompt()
def property_analysis(address: str) -> str:
    """Analyze a property's value, rent, comparables, and local market."""
    return (
        f"Please analyze the property at {address}. Include:\n"
        "1. The property record (attributes, last sale, tax assessment)\n"
        "2. Current value estimate and rent estimate, with their comparables\n"
        "3. Market statistics for the property's zip code\n"
        "4. Estimated gross rental yield and price to rent ratio\n\n"
        "Provide insights on whether this is a good investment opportunity."
    )


@mcp.prompt()
def market_overview(zip_code: str) -> str:
    """Get a comprehensive market overview for a zip code."""
    return (
        f"Provide a comprehensive market overview for zip code {zip_code}. Include:\n"
        "1. Sale and rental market statistics (average and median price, rent, price per sq ft)\n"
        "2. Trends over the last 12 months\n"
        "3. A sample of current active sale and rental listings\n"
        "4. Key insights for buyers, renters, and investors"
    )


def main():
    """Main entry point for the MCP server."""
    if not RENTCAST_API_KEY:
        logger.error("RENTCAST_API_KEY environment variable is not set")
        sys.exit(1)
    logger.info("Starting RentCast MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
