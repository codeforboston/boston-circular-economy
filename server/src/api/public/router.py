from typing import Annotated

from fastapi import APIRouter, Depends, status

from .schema import FeedbackInput, SearchInput, SearchResponse

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/search", response_model=SearchResponse)
async def search_location(search_input: Annotated[SearchInput, Depends()]):
    # TODO: Implement the logic for searching items by category or query
    return SearchResponse()


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_user_feedback(feedback: FeedbackInput):
    # TODO: Implement the logic for submitting user feedback
    pass
