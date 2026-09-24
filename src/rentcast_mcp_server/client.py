"""HTTP client for the RentCast API (https://developers.rentcast.io/reference)."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

BASE_URL = "https://api.rentcast.io/v1"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30.0

_client: Optional[httpx.AsyncClient] = None


class RentCastError(Exception):
    """Raised when a RentCast request fails. The message is shown to the model."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def api_key() -> Optional[str]:
    return os.environ.get("RENTCAST_API_KEY") or None


def suppress_logging() -> bool:
    """Whether to ask RentCast not to log query parameters."""
    value = os.environ.get("RENTCAST_SUPPRESS_LOGGING", "")
    return value.strip().lower() in ("1", "true", "yes", "on")


def get_http_client() -> httpx.AsyncClient:
    """Get the shared HTTP client, creating it on first use."""
    global _client
    key = api_key()
    if not key:
        raise RentCastError(
            "RENTCAST_API_KEY environment variable is not set. "
            "Get a key at https://app.rentcast.io/app/api"
        )
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"X-Api-Key": key, "Accept": "application/json"},
            timeout=TIMEOUT_SECONDS,
        )
    return _client


def error_message(response: httpx.Response) -> str:
    """Build a readable error from a RentCast error response."""
    try:
        body = response.json()
        detail = body.get("message") or body.get("error") or response.text
    except (ValueError, AttributeError):
        detail = response.text or response.reason_phrase
    hints = {
        401: "Check that RENTCAST_API_KEY is valid.",
        403: "The API key is restricted, or the subscription or billing is inactive.",
        429: "Rate limit of 20 requests per second exceeded.",
    }
    message = f"RentCast API error {response.status_code}: {detail}"
    hint = hints.get(response.status_code)
    return f"{message} ({hint})" if hint else message


async def rentcast_get(path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
    """
    Perform a GET request against the RentCast API.

    None values are dropped from params. Rate limited requests (429) are retried
    with backoff. Any other non-2xx response raises RentCastError with the API's message.
    """
    client = get_http_client()
    query = {k: v for k, v in (params or {}).items() if v is not None}
    if suppress_logging():
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
            logger.warning("Rate limited on %s, retrying in %ss", path, delay)
            await asyncio.sleep(delay)
            continue
        break

    if response.is_success:
        return response
    logger.error("GET %s failed with %s", path, response.status_code)
    raise RentCastError(error_message(response), response.status_code)


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


async def get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """GET a single resource and return its JSON body."""
    response = await rentcast_get(path, params)
    return response.json()
