"""Tests for the sale and rental listing tools."""

import pytest
from conftest import call_tool

LISTINGS = [{"id": "3821-Hargis-St,-Austin,-TX-78723", "price": 450000}]


@pytest.mark.parametrize(
    "tool, path",
    [
        ("search_sale_listings", "/v1/listings/sale"),
        ("search_rental_listings", "/v1/listings/rental/long-term"),
    ],
)
async def test_search_listings(rentcast, tool, path):
    rentcast.json(path.removeprefix("/v1"), LISTINGS)

    result = await call_tool(
        tool,
        {
            "zip_code": "78704",
            "property_type": "Single Family",
            "bedrooms": "2:4",
            "status": "Active",
            "price": "*:500000",
            "days_old": 30,
            "limit": 10,
            "offset": 20,
        },
    )

    assert rentcast.last.url.path == path
    assert rentcast.last_params == {
        "zipCode": "78704",
        "propertyType": "Single Family",
        "bedrooms": "2:4",
        "status": "Active",
        "price": "*:500000",
        "daysOld": "30",
        "limit": "10",
        "offset": "20",
    }
    assert result["results"] == LISTINGS
    assert result["offset"] == 20


async def test_search_listings_rejects_unknown_status(rentcast):
    from mcp.server.fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        await call_tool("search_sale_listings", {"zip_code": "78704", "status": "Pending"})


@pytest.mark.parametrize(
    "tool, path",
    [
        ("get_sale_listing", "/listings/sale/3821-Hargis-St,-Austin,-TX-78723"),
        ("get_rental_listing", "/listings/rental/long-term/3821-Hargis-St,-Austin,-TX-78723"),
    ],
)
async def test_get_listing_by_id(rentcast, tool, path):
    rentcast.json(path, LISTINGS[0])

    result = await call_tool(tool, {"listing_id": "3821-Hargis-St,-Austin,-TX-78723"})

    assert result == LISTINGS[0]
    assert rentcast.last.url.path == f"/v1{path}"
