"""Tests for the value and rent estimate tools."""

import pytest
from conftest import call_tool
from mcp.server.fastmcp.exceptions import ToolError

ESTIMATE = {"price": 250000, "priceRangeLow": 230000, "priceRangeHigh": 270000, "comparables": []}


@pytest.mark.parametrize(
    "tool, path",
    [("get_value_estimate", "/v1/avm/value"), ("get_rent_estimate", "/v1/avm/rent/long-term")],
)
async def test_estimate_by_address(rentcast, tool, path):
    rentcast.json(path.removeprefix("/v1"), ESTIMATE)

    result = await call_tool(
        tool,
        {
            "address": "5500 Grand Lake Dr, San Antonio, TX, 78244",
            "property_type": "Single Family",
            "bedrooms": 3,
            "bathrooms": 2.5,
            "square_footage": 1878,
            "max_radius": 2,
            "days_old": 180,
            "comp_count": 10,
            "lookup_subject_attributes": False,
        },
    )

    assert result == ESTIMATE
    assert rentcast.last.url.path == path
    assert rentcast.last_params == {
        "address": "5500 Grand Lake Dr, San Antonio, TX, 78244",
        "propertyType": "Single Family",
        "bedrooms": "3",
        "bathrooms": "2.5",
        "squareFootage": "1878",
        "maxRadius": "2.0",
        "daysOld": "180",
        "compCount": "10",
        "lookupSubjectAttributes": "false",
    }


async def test_estimate_by_coordinates(rentcast):
    rentcast.json("/avm/value", ESTIMATE)

    await call_tool("get_value_estimate", {"latitude": 29.47, "longitude": -98.35})

    assert rentcast.last_params == {"latitude": "29.47", "longitude": "-98.35"}


@pytest.mark.parametrize("arguments", [{}, {"latitude": 29.47}])
async def test_estimate_requires_a_location(rentcast, arguments):
    with pytest.raises(ToolError, match="address or both latitude and longitude"):
        await call_tool("get_value_estimate", arguments)
    assert rentcast.requests == []


async def test_estimate_comp_count_bounds(rentcast):
    with pytest.raises(ToolError, match="greater than or equal to 5"):
        await call_tool("get_rent_estimate", {"address": "x", "comp_count": 3})


async def test_rent_estimate_does_not_accept_land(rentcast):
    with pytest.raises(ToolError):
        await call_tool("get_rent_estimate", {"address": "x", "property_type": "Land"})


async def test_unparseable_address_reports_rentcast_message(rentcast):
    rentcast.error("/avm/value", 400, "The provided address '1234 Main St' could not be parsed")

    with pytest.raises(ToolError, match="400: The provided address '1234 Main St'"):
        await call_tool("get_value_estimate", {"address": "1234 Main St"})
