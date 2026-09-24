"""Value and rent estimate tools (/avm)."""

from typing import Annotated, Any, Dict, Literal, Optional

from pydantic import Field

from rentcast_mcp_server.app import mcp
from rentcast_mcp_server.client import RentCastError, get_json
from rentcast_mcp_server.params import (
    CompCount,
    CompDaysOld,
    EstimateAddress,
    EstimateBathrooms,
    EstimateBedrooms,
    EstimateLatitude,
    EstimateLongitude,
    EstimateSquareFootage,
    LookupSubjectAttributes,
    MaxRadius,
    to_range,
)


async def _estimate(
    path: str,
    address: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    property_type: Optional[str],
    bedrooms: Optional[float],
    bathrooms: Optional[float],
    square_footage: Optional[float],
    max_radius: Optional[float],
    days_old: Optional[int],
    comp_count: Optional[int],
    lookup_subject_attributes: Optional[bool],
) -> Dict[str, Any]:
    if not address and (latitude is None or longitude is None):
        raise RentCastError("Provide either an address or both latitude and longitude.")
    params = {
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "propertyType": property_type,
        "bedrooms": to_range(bedrooms),
        "bathrooms": to_range(bathrooms),
        "squareFootage": to_range(square_footage),
        "maxRadius": max_radius,
        "daysOld": days_old,
        "compCount": comp_count,
        "lookupSubjectAttributes": lookup_subject_attributes,
    }
    return await get_json(path, params)


@mcp.tool()
async def get_value_estimate(
    address: EstimateAddress = None,
    latitude: EstimateLatitude = None,
    longitude: EstimateLongitude = None,
    property_type: Annotated[
        Optional[
            Literal[
                "Single Family", "Condo", "Townhouse", "Manufactured", "Multi-Family",
                "Apartment", "Land",
            ]
        ],
        Field(description="Override the subject property type."),
    ] = None,
    bedrooms: EstimateBedrooms = None,
    bathrooms: EstimateBathrooms = None,
    square_footage: EstimateSquareFootage = None,
    max_radius: MaxRadius = None,
    days_old: CompDaysOld = None,
    comp_count: CompCount = None,
    lookup_subject_attributes: LookupSubjectAttributes = None,
) -> Dict[str, Any]:
    """
    Get the estimated market value (AVM) of a property, with a value range and the
    comparable sale listings used to calculate it.
    """
    return await _estimate(
        "/avm/value", address, latitude, longitude, property_type, bedrooms, bathrooms,
        square_footage, max_radius, days_old, comp_count, lookup_subject_attributes,
    )


@mcp.tool()
async def get_rent_estimate(
    address: EstimateAddress = None,
    latitude: EstimateLatitude = None,
    longitude: EstimateLongitude = None,
    property_type: Annotated[
        Optional[
            Literal[
                "Single Family", "Condo", "Townhouse", "Manufactured", "Multi-Family", "Apartment",
            ]
        ],
        Field(description="Override the subject property type."),
    ] = None,
    bedrooms: EstimateBedrooms = None,
    bathrooms: EstimateBathrooms = None,
    square_footage: EstimateSquareFootage = None,
    max_radius: MaxRadius = None,
    days_old: CompDaysOld = None,
    comp_count: CompCount = None,
    lookup_subject_attributes: LookupSubjectAttributes = None,
) -> Dict[str, Any]:
    """
    Get the estimated long-term monthly rent of a property, with a rent range and the
    comparable rental listings used to calculate it.
    """
    return await _estimate(
        "/avm/rent/long-term", address, latitude, longitude, property_type, bedrooms, bathrooms,
        square_footage, max_radius, days_old, comp_count, lookup_subject_attributes,
    )
