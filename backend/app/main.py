import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_db_and_tables, run_migrations
from app.routes.tasks import router as tasks_router
from app.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    run_migrations()
    yield


app = FastAPI(title="Todo API", lifespan=lifespan)

cors_origins = [
    "http://localhost:3000",
    "http://taskflow.local",
]
extra_origin = os.environ.get("CORS_ORIGIN", "")
if extra_origin:
    cors_origins.append(extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"name": "Todo API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
