from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_session, init_db
from graph_builder import build_graph
from query_engine import handle_query

# ✅ Load environment variables
load_dotenv()

# ✅ Dependency for DB session
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

# ✅ Lifespan event (runs on startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting FastAPI app...")

    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB INIT ERROR:", e)

    yield

    print("🛑 Shutting down app...")

# ✅ Create FastAPI app (ONLY ONCE)
app = FastAPI(
    title="SAP O2C API",
    version="1.0.0",
    lifespan=lifespan,
)

# ✅ CORS (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo (restrict later)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTES
# =========================

@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"message": "API is running"}

@app.get("/db-check", tags=["Health"])
def db_check() -> dict[str, str]:
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return {"message": "Database connection OK"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/graph", tags=["Graph"])
def get_graph() -> dict:
    try:
        with get_session() as session:
            return build_graph(session)
    except Exception as e:
        return {"error": str(e)}

@app.post("/query", tags=["Query"])
def query_data(
    user_query: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    try:
        return handle_query(user_query, db)
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-data", tags=["Health"])
def test_data() -> dict:
    from models import SalesOrder

    try:
        with get_session() as session:
            count = session.scalar(
                select(func.count()).select_from(SalesOrder)
            ) or 0

        if count <= 0:
            return {
                "count": int(count),
                "message": "Data NOT loaded (this is likely your issue)"
            }

        return {
            "count": int(count),
            "message": "Data is loaded"
        }

    except Exception as e:
        return {"error": str(e)}