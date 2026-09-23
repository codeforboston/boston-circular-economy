from typing import Literal

from contracts.domain import Activity, Address, ItemCategory
from pydantic import BaseModel, Field


class LocationResponse(BaseModel):
    name: str
    lat: float
    lon: float
    address: Address

class SearchResult(BaseModel):
    location: LocationResponse
    item: ItemCategory
    activity: Activity

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
