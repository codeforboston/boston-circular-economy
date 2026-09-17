from api.public.router import router as public_router
from fastapi import FastAPI

app = FastAPI(
    title="Boston Circular Economy API",
    description="API for interacting with server-side functionalities",
    version="0.1.0",
)
app.include_router(
    public_router,
    prefix="/api/v1",
    tags=["public"],
)
