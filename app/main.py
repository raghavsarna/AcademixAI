"""AcademixAI API. The website is the Next.js app in web/, which calls this API."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal
from app.llm import LLMError
from app.routers import auth, editions, papers
from app.services import jobs
from app.services.analysis import AnalysisError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("academixai")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    interrupted = jobs.fail_interrupted()
    if interrupted:
        logger.warning("Marked %d unfinished upload jobs as interrupted", interrupted)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="AcademixAI API",
    description="What changed in AI research today, and every paper explained at your level.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(editions.router)
app.include_router(papers.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "AcademixAI API", "docs": "/docs", "health": "/api/health"}


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.exception_handler(LLMError)
async def llm_error_handler(_: Request, exc: LLMError) -> JSONResponse:
    logger.error("Model error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The AI service is unavailable right now. Please try again in a minute."},
    )


@app.exception_handler(AnalysisError)
async def analysis_error_handler(_: Request, exc: AnalysisError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "The AI couldn't analyse this paper. Please try again or try another PDF."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong on our side."},
    )
