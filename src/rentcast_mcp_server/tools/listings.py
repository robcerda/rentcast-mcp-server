"""Sale and rental listing tools (/listings)."""

from typing import Annotated, Any, Dict

from pydantic import Field

from rentcast_mcp_server.app import mcp
from rentcast_mcp_server.client import get_json, search
from rentcast_mcp_server.params import (
    Address,
    Bathrooms,
    Bedrooms,
    City,
    DaysOld,
    IncludeTotalCount,
    Latitude,
    Limit,
    ListingStatus,
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
        **location_params(address, city, state, zip_code, latitude, longitude, radius),
        **attribute_params(
            property_type, bedrooms, bathrooms, square_footage, lot_size, year_built
        ),
        "status": status,
        "price": to_range(price),
        "daysOld": to_range(days_old),
        **pagination_params(limit, offset, include_total_count),
    }
    return await search("/listings/sale", params)


@mcp.tool()
async def get_sale_listing(
    listing_id: Annotated[
        str, Field(description="RentCast listing id, e.g. '3821-Hargis-St,-Austin,-TX-78723'.")
    ],
) -> Dict[str, Any]:
    """Get a single sale listing by its RentCast id (the 'id' field from search results)."""
    return await get_json(f"/listings/sale/{listing_id}")


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
        **location_params(address, city, state, zip_code, latitude, longitude, radius),
        **attribute_params(
            property_type, bedrooms, bathrooms, square_footage, lot_size, year_built
        ),
        "status": status,
        "price": to_range(price),
        "daysOld": to_range(days_old),
        **pagination_params(limit, offset, include_total_count),
    }
    return await search("/listings/rental/long-term", params)


@mcp.tool()
async def get_rental_listing(
    listing_id: Annotated[
        str, Field(description="RentCast listing id, e.g. '2005-Arborside-Dr,-Austin,-TX-78754'.")
    ],
) -> Dict[str, Any]:
    """Get a single long-term rental listing by its RentCast id."""
    return await get_json(f"/listings/rental/long-term/{listing_id}")
