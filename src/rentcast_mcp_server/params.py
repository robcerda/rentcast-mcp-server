"""Shared tool parameter types and query builders.

Range parameters accept a single value ("3"), multiple values separated by "|"
("2|3"), or an inclusive range separated by ":" with "*" for an open end
("2:4", "1500:*"). See https://developers.rentcast.io/reference/search-queries
"""

from typing import Annotated, Any, Dict, Literal, Optional, Union

from pydantic import Field

RangeValue = Optional[Union[str, int, float]]

PROPERTY_TYPES = (
    "Single Family",
    "Condo",
    "Townhouse",
    "Manufactured",
    "Multi-Family",
    "Apartment",
    "Land",
)

# Search parameters

Address = Annotated[
    Optional[str],
    Field(description="Full property address in the format 'Street, City, State, Zip'."),
]
City = Annotated[Optional[str], Field(description="City name (case-sensitive), e.g. 'Austin'.")]
State = Annotated[Optional[str], Field(description="2-letter state abbreviation, e.g. 'TX'.")]
ZipCode = Annotated[Optional[str], Field(description="5-digit zip code.")]
Latitude = Annotated[Optional[float], Field(description="Latitude of the search center.")]
Longitude = Annotated[Optional[float], Field(description="Longitude of the search center.")]
Radius = Annotated[
    Optional[float],
    Field(description="Search radius in miles (max 100). Use with address or latitude/longitude."),
]
PropertyType = Annotated[
    Optional[str],
    Field(
        description=(
            "Case-sensitive property type: 'Single Family', 'Condo', 'Townhouse', 'Manufactured', "
            "'Multi-Family' (2-4 units), 'Apartment' (5+ units), 'Land'. "
            "Separate multiple types with '|', e.g. 'Condo|Townhouse'."
        )
    ),
]
Bedrooms = Annotated[
    RangeValue,
    Field(description="Bedrooms, 0 for studio. Supports '2|3' or ranges like '2:4', '3:*'."),
]
Bathrooms = Annotated[
    RangeValue,
    Field(description="Bathrooms, fractions allowed. Supports '1|2' or ranges like '1.5:*'."),
]
SquareFootage = Annotated[
    RangeValue, Field(description="Living area in sq ft. Supports ranges like '1000:2000'.")
]
LotSize = Annotated[
    RangeValue, Field(description="Lot size in sq ft. Supports ranges like '5000:*'.")
]
YearBuilt = Annotated[
    RangeValue, Field(description="Year built. Supports ranges like '2000:*' or '1950:1980'.")
]
Limit = Annotated[
    Optional[int], Field(ge=1, le=500, description="Results per page, 1-500. Defaults to 50.")
]
Offset = Annotated[
    Optional[int],
    Field(ge=0, description="Index of the first result, for pagination. Use multiples of limit."),
]
IncludeTotalCount = Annotated[
    Optional[bool],
    Field(description="Return the total number of matches as totalCount. Slower, use sparingly."),
]
ListingStatus = Annotated[
    Optional[Literal["Active", "Inactive"]],
    Field(description="Listing status. Defaults to 'Active'."),
]
DaysOld = Annotated[
    RangeValue,
    Field(
        description=(
            "Days since the property was listed. A single value is a maximum; "
            "ranges like '30:90' are also supported."
        )
    ),
]

# Valuation parameters

EstimateAddress = Annotated[
    Optional[str],
    Field(description="Full address 'Street, City, State, Zip'. Required unless lat/long given."),
]
EstimateLatitude = Annotated[Optional[float], Field(description="Property latitude.")]
EstimateLongitude = Annotated[Optional[float], Field(description="Property longitude.")]
EstimateBedrooms = Annotated[
    Optional[float], Field(description="Override bedrooms of the subject property, 0 for studio.")
]
EstimateBathrooms = Annotated[
    Optional[float], Field(description="Override bathrooms of the subject property.")
]
EstimateSquareFootage = Annotated[
    Optional[float], Field(description="Override living area of the subject property in sq ft.")
]
MaxRadius = Annotated[
    Optional[float], Field(description="Maximum distance in miles between comps and the property.")
]
CompDaysOld = Annotated[
    Optional[int],
    Field(ge=1, description="Maximum days since comparable listings were last on the market."),
]
CompCount = Annotated[
    Optional[int],
    Field(ge=5, le=25, description="Number of comparables to use, 5-25. Defaults to 15."),
]
LookupSubjectAttributes = Annotated[
    Optional[bool],
    Field(
        description=(
            "Look up the subject property's attributes automatically. Defaults to true; "
            "explicit attribute arguments override the looked up values."
        )
    ),
]


def to_range(value: RangeValue) -> Optional[str]:
    """Convert a range parameter to the string form the API expects."""
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def location_params(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    radius: Optional[float],
) -> Dict[str, Any]:
    return {
        "address": address,
        "city": city,
        "state": state,
        "zipCode": zip_code,
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
    }


def attribute_params(
    property_type: Optional[str],
    bedrooms: RangeValue,
    bathrooms: RangeValue,
    square_footage: RangeValue,
    lot_size: RangeValue,
    year_built: RangeValue,
) -> Dict[str, Any]:
    return {
        "propertyType": property_type,
        "bedrooms": to_range(bedrooms),
        "bathrooms": to_range(bathrooms),
        "squareFootage": to_range(square_footage),
        "lotSize": to_range(lot_size),
        "yearBuilt": to_range(year_built),
    }


def pagination_params(
    limit: Optional[int], offset: Optional[int], include_total_count: Optional[bool]
) -> Dict[str, Any]:
    return {"limit": limit, "offset": offset, "includeTotalCount": include_total_count or None}
