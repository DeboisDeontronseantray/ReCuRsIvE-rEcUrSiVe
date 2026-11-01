from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.novels.router import router as novels_router
# Story Bot: /novels API retained; prefer CLI `python -m app.cli` (seasons/episodes).


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(novels_router)


@app.get("/health")
def health():
    return {"status": "ok"}
