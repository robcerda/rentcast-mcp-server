"""FastMCP application instance and entry point."""

import argparse
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

# Log to stderr: stdout carries the MCP protocol in stdio mode.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# httpx logs every request URL at INFO, including the addresses being looked up.
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize FastMCP server
mcp = FastMCP("rentcast-mcp")

# Import tools package to trigger @mcp.tool() registration
import rentcast_mcp_server.tools  # noqa: E402, F401
from rentcast_mcp_server.client import RentCastError, api_key  # noqa: E402

# Export for `mcp run`
app = mcp


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("port must be an integer") from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _env_list(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="RentCast MCP Server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "http"),
        default=os.environ.get("RENTCAST_MCP_TRANSPORT", "stdio"),
        help="MCP transport (env: RENTCAST_MCP_TRANSPORT; default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("RENTCAST_MCP_HOST", "127.0.0.1"),
        help="HTTP bind address (env: RENTCAST_MCP_HOST; default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=_port,
        default=os.environ.get("RENTCAST_MCP_PORT", "8000"),
        help="HTTP port (env: RENTCAST_MCP_PORT; default: 8000)",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=None,
        help="Additional HTTP Host value, e.g. mcp.example.com (repeatable; "
        "env: RENTCAST_MCP_ALLOWED_HOSTS, comma-separated)",
    )
    parser.add_argument(
        "--allowed-origin",
        action="append",
        default=None,
        help="Additional browser Origin, e.g. https://client.example.com (repeatable; "
        "env: RENTCAST_MCP_ALLOWED_ORIGINS, comma-separated)",
    )
    args = parser.parse_args(argv)
    # argparse does not check choices for defaults supplied by the environment.
    if args.transport not in ("stdio", "streamable-http", "http"):
        parser.error("RENTCAST_MCP_TRANSPORT must be stdio, streamable-http, or http")
    if not args.host.strip():
        parser.error("HTTP host must not be empty")

    try:
        credential = api_key()
    except RentCastError as e:
        logger.error("%s", e)
        sys.exit(1)
    if not credential:
        logger.error("No RentCast credential: set RENTCAST_SURROGATE_KEY or RENTCAST_API_KEY")
        sys.exit(1)

    if args.transport != "stdio":
        from mcp.server.transport_security import TransportSecuritySettings

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        # Listening on all interfaces must not disable Host/Origin validation.
        # Remote clients explicitly allow their public hostname (including port).
        mcp.settings.transport_security = TransportSecuritySettings(
            allowed_hosts=[
                "localhost",
                "localhost:*",
                "127.0.0.1",
                "127.0.0.1:*",
                "[::1]",
                "[::1]:*",
                *(
                    args.allowed_host
                    if args.allowed_host is not None
                    else _env_list("RENTCAST_MCP_ALLOWED_HOSTS")
                ),
            ],
            allowed_origins=[
                "http://localhost",
                "http://localhost:*",
                "http://127.0.0.1",
                "http://127.0.0.1:*",
                "http://[::1]",
                "http://[::1]:*",
                *(
                    args.allowed_origin
                    if args.allowed_origin is not None
                    else _env_list("RENTCAST_MCP_ALLOWED_ORIGINS")
                ),
            ],
        )

    logger.info("Starting RentCast MCP Server (%s)...", args.transport)
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
