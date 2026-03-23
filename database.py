from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sap_o2c.db")

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_session() -> Session:
    return SessionLocal()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

