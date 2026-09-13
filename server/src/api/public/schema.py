from typing import Literal

from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    item_category: str | None = Field(
        default=None, description="The item category, e.g., 'shoes', to search for."
    )  # TODO: to restrict item_category to etl.dtos.ItemCategory
    query: str | None = Field(
        default=None, description="A free-text search query string."
    )


class LocationResponse(BaseModel):
    name: str
    lat: float
    lon: float
    address: str  # TODO: restrict to etl.dtos.Address


class SearchResponse(BaseModel):
    locations: list[LocationResponse] = Field(
        default_factory=list,
        description="A list of locations matching the search criteria.",
    )


class FeedbackInput(BaseModel):
    reaction: Literal["like", "dislike"] = Field(
        ..., description="The user's reaction, either 'like' or 'dislike'."
    )
    message: str | None = Field(
        default=None, description="The feedback message from the user."
    )
