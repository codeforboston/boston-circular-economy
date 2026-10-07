from typing import Literal

from contracts.domain import Address, Contact, Service
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    name: str
    address: Address
    services: list[Service]
    contact: Contact

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
