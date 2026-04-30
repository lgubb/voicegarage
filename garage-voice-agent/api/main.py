from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_api_settings
from api.routes.sessions import router as sessions_router

settings = get_api_settings()

app = FastAPI(
    title="Auto Voice Agent API",
    version="0.1.0",
    description="API minimale pour demo commerciale LiveKit garage.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sessions_router)
