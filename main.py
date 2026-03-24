from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from database import get_session, init_db
from graph_builder import build_graph
from query_engine import handle_query

def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist when the API starts.
    init_db()
    yield


app = FastAPI(
    title="SAP O2C API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"message": "API is running"}


@app.get("/db-check", tags=["Health"])
def db_check() -> dict[str, str]:
    with get_session() as session:
        session.execute(text("SELECT 1"))
    return {"message": "Database connection OK"}


@app.get("/graph", tags=["Graph"])
def get_graph() -> dict:
    with get_session() as session:
        return build_graph(session)


@app.post("/query", tags=["Query"])
def query_data(user_query: str = Body(..., embed=True), db: Session = Depends(get_db)):
    return handle_query(user_query, db)


@app.get("/test-data", tags=["Health"])
def test_data() -> dict:
    # Uses a simple count of sales orders to determine if the dataset was loaded.
    from models import SalesOrder

    with get_session() as session:
        count = session.scalar(select(func.count()).select_from(SalesOrder)) or 0
    if count <= 0:
        return {"count": int(count), "message": "Data NOT loaded (this is likely your issue)"}
    return {"count": int(count), "message": "data is loaded"}