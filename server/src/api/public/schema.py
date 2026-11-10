from typing import Literal

from contracts.domain import Address, Availability, Contact, Location, Service
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Opaque application-level location identifier."
        ),
    )
    name: str
    lat: float
    lon: float
    address: Address
    services: list[Service]
    contact: Contact
    availability: Availability
    last_verified: str | None = None

    @classmethod
    def from_location(cls, location: Location) -> "SearchResult":
        return cls(**location.model_dump())

class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(
        default_factory=list,
        description="A list of search results matching the search criteria.",
    )

class FeedbackInput(BaseModel):
    reaction: Literal["like", "dislike"] = Field(
        ..., description="The user's reaction, either 'like' or 'dislike'."
    )
    message: str | None = Field(
        default=None, description="The feedback message from the user."
    )
