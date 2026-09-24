"""Tests for the market statistics tool and prompts."""

from conftest import call_tool

from rentcast_mcp_server.app import mcp


async def test_get_market_statistics(rentcast):
    stats = {"zipCode": "78704", "saleData": {}, "rentalData": {}}
    rentcast.json("/markets", stats)

    result = await call_tool(
        "get_market_statistics",
        {"zip_code": "78704", "data_type": "Rental", "history_range": 6},
    )

    assert result == stats
    assert rentcast.last_params == {"zipCode": "78704", "dataType": "Rental", "historyRange": "6"}


async def test_prompts_are_registered():
    prompts = {p.name: p for p in await mcp.list_prompts()}
    assert set(prompts) == {"property_analysis", "market_overview"}

    result = await mcp.get_prompt("market_overview", {"zip_code": "78704"})
    assert "zip code 78704" in result.messages[0].content.text
