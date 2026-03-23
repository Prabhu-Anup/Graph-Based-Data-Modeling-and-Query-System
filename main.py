from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import func, select, text

from database import get_session, init_db
from graph_builder import build_graph
from query_service import run_nl_query

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


class QueryRequest(BaseModel):
    query: str


@app.post("/query", tags=["Query"])
def query_data(request: QueryRequest) -> dict:
    with get_session() as session:
        result = run_nl_query(session=session, user_query=request.query)
    return result.to_dict()


@app.get("/test-data", tags=["Health"])
def test_data() -> dict:
    # Uses a simple count of sales orders to determine if the dataset was loaded.
    from models import SalesOrder

    with get_session() as session:
        count = session.scalar(select(func.count()).select_from(SalesOrder)) or 0
    if count <= 0:
        return {"count": int(count), "message": "Data NOT loaded (this is likely your issue)"}
    return {"count": int(count), "message": "data is loaded"}