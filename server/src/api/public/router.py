from config import DATA_DIR
from data_store import LocalDataStore
from fastapi import APIRouter, status

from .schema import FeedbackInput, SearchResponse, SearchResult

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/search", response_model=SearchResponse)
async def search():
    data_store = LocalDataStore(DATA_DIR)
    locations = data_store.read_output_locations()
    output = [SearchResult(**location.model_dump()) for location in locations]

    return SearchResponse(results=output)


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_user_feedback(feedback: FeedbackInput):
    # TODO: Implement logic for submitting user feedback, after confirming data store
    pass
