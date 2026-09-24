"""
RentCast MCP Server entry point.

This module re-exports every public name so that ``python server.py``,
``mcp run server.py`` and imports like
``from rentcast_mcp_server.server import search_properties`` keep working.
The implementation lives in ``app``, ``client``, ``params`` and ``tools``.
"""

from rentcast_mcp_server.app import app, main, mcp  # noqa: F401
from rentcast_mcp_server.client import RentCastError, get_http_client  # noqa: F401
from rentcast_mcp_server.tools.listings import (  # noqa: F401
    get_rental_listing,
    get_sale_listing,
    search_rental_listings,
    search_sale_listings,
)
from rentcast_mcp_server.tools.markets import get_market_statistics  # noqa: F401
from rentcast_mcp_server.tools.prompts import market_overview, property_analysis  # noqa: F401
from rentcast_mcp_server.tools.properties import (  # noqa: F401
    get_property,
    get_random_properties,
    search_properties,
)
from rentcast_mcp_server.tools.valuations import (  # noqa: F401
    get_rent_estimate,
    get_value_estimate,
)

if __name__ == "__main__":
    main()
