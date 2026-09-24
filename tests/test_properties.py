"""Tests for the property record tools."""

import pytest
from conftest import call_tool
from mcp.server.fastmcp.exceptions import ToolError

RECORDS = [{"id": "5500-Grand-Lake-Dr,-San-Antonio,-TX-78244"}, {"id": "2"}]


async def test_search_properties_sends_filters_in_rentcast_syntax(rentcast):
    rentcast.json("/properties", RECORDS, **{"X-Limit": "2", "X-Offset": "0"})

    await call_tool(
        "search_properties",
        {
            "city": "Austin",
            "state": "TX",
            "property_type": "Condo|Townhouse",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "square_footage": "1000:*",
            "lot_size": "*:8000",
            "year_built": "2000:2010",
            "sale_date_range": 270,
            "limit": 2,
        },
    )

    assert rentcast.last.url.path == "/v1/properties"
    assert rentcast.last_params == {
        "city": "Austin",
        "state": "TX",
        "propertyType": "Condo|Townhouse",
        "bedrooms": "3",
        "bathrooms": "2",
        "squareFootage": "1000:*",
        "lotSize": "*:8000",
        "yearBuilt": "2000:2010",
        "saleDateRange": "270",
        "limit": "2",
    }


async def test_search_properties_by_radius(rentcast):
    rentcast.json("/properties", RECORDS)

    await call_tool(
        "search_properties", {"latitude": 30.27, "longitude": -97.74, "radius": 5}
    )

    assert rentcast.last_params == {"latitude": "30.27", "longitude": "-97.74", "radius": "5.0"}


async def test_search_properties_returns_pagination_envelope(rentcast):
    rentcast.json(
        "/properties",
        RECORDS,
        **{"X-Limit": "2", "X-Offset": "4", "X-Total-Count": "9"},
    )

    result = await call_tool(
        "search_properties",
        {"zip_code": "78704", "limit": 2, "offset": 4, "include_total_count": True},
    )

    assert rentcast.last_params["includeTotalCount"] == "true"
    assert result == {
        "count": 2,
        "limit": 2,
        "offset": 4,
        "hasMore": True,
        "results": RECORDS,
        "totalCount": 9,
    }


async def test_search_properties_last_page_has_no_more(rentcast):
    rentcast.json("/properties", RECORDS)

    result = await call_tool("search_properties", {"zip_code": "78704"})

    assert result["limit"] == 50
    assert result["hasMore"] is False
    assert "totalCount" not in result


async def test_search_properties_no_matches_is_empty_not_an_error(rentcast):
    rentcast.error("/properties", 404, "No properties found")

    result = await call_tool(
        "search_properties", {"zip_code": "00000", "include_total_count": True}
    )

    assert result["results"] == []
    assert result["count"] == 0
    assert result["totalCount"] == 0


async def test_search_properties_rejects_limit_over_500(rentcast):
    with pytest.raises(ToolError, match="less than or equal to 500"):
        await call_tool("search_properties", {"zip_code": "78704", "limit": 501})
    assert rentcast.requests == []


async def test_get_random_properties_only_sends_limit(rentcast):
    rentcast.json("/properties/random", RECORDS)

    result = await call_tool("get_random_properties", {"limit": 2})

    assert rentcast.last_params == {"limit": "2"}
    assert result == {"count": 2, "results": RECORDS}


async def test_get_property_by_id(rentcast):
    rentcast.json("/properties/5500-Grand-Lake-Dr,-San-Antonio,-TX-78244", RECORDS[0])

    result = await call_tool(
        "get_property", {"property_id": "5500-Grand-Lake-Dr,-San-Antonio,-TX-78244"}
    )

    assert result == RECORDS[0]


async def test_get_property_not_found_reports_rentcast_message(rentcast):
    rentcast.error("/properties/missing", 404, "Property record not found")

    with pytest.raises(ToolError, match="RentCast API error 404: Property record not found"):
        await call_tool("get_property", {"property_id": "missing"})
