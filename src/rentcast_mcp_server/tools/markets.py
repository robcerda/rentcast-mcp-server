"""Market statistics tools (/markets)."""

from typing import Annotated, Any, Dict, Literal, Optional

from pydantic import Field

from rentcast_mcp_server.app import mcp
from rentcast_mcp_server.client import get_json


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
    return await get_json("/markets", params)
