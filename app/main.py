import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth import require_subject
from app.bedrock import generate_response
from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fail early if required runtime configuration is absent.
    get_settings()
    yield


app = FastAPI(title="AI Agent API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health/live", include_in_schema=False)
def liveness():
    return {"status": "ok"}


@app.get("/health/ready", include_in_schema=False)
def readiness():
    get_settings()
    return {"status": "ready"}


@app.post("/v1/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit)
def chat(
    request: Request,
    payload: ChatRequest,
    subject: Annotated[str, Depends(require_subject)],
):
    del subject  # Authentication is required; the subject is not logged.
    try:
        payload.validate_prompt_size()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    return ChatResponse(
        response=generate_response(payload),
        model_id=settings.bedrock_model_id,
    )
