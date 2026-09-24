"""Property record tools (/properties)."""

from typing import Annotated, Any, Dict

from pydantic import Field

from rentcast_mcp_server.app import mcp
from rentcast_mcp_server.client import get_json, search
from rentcast_mcp_server.params import (
    Address,
    Bathrooms,
    Bedrooms,
    City,
    IncludeTotalCount,
    Latitude,
    Limit,
    Longitude,
    LotSize,
    Offset,
    PropertyType,
    Radius,
    RangeValue,
    SquareFootage,
    State,
    YearBuilt,
    ZipCode,
    attribute_params,
    location_params,
    pagination_params,
    to_range,
)


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
        **location_params(address, city, state, zip_code, latitude, longitude, radius),
        **attribute_params(
            property_type, bedrooms, bathrooms, square_footage, lot_size, year_built
        ),
        "saleDateRange": to_range(sale_date_range),
        **pagination_params(limit, offset, include_total_count),
    }
    return await search("/properties", params)


@mcp.tool()
async def get_random_properties(limit: Limit = None) -> Dict[str, Any]:
    """Get a random sample of property records from across the US (no filters supported)."""
    results = await get_json("/properties/random", {"limit": limit})
    return {"count": len(results), "results": results}


@mcp.tool()
async def get_property(
    property_id: Annotated[
        str,
        Field(description="RentCast property id, e.g. '5500-Grand-Lake-Dr,-San-Antonio,-TX-78244'"),
    ],
) -> Dict[str, Any]:
    """Get a single property record by its RentCast id (the 'id' field from search results)."""
    return await get_json(f"/properties/{property_id}")
