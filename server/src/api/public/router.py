from fastapi import APIRouter, status

from .schema import FeedbackInput, SearchResponse

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/search", response_model=SearchResponse)
async def search():
    # TODO: return tuples[location, item, activity]
    return SearchResponse()


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_user_feedback(feedback: FeedbackInput):
    # TODO: Implement the logic for submitting user feedback
    pass
