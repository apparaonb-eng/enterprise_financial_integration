"""
core/database.py
-----------------
Central database setup. Uses SQLite for this base project (zero
external setup required) — swap DATABASE_URL for Postgres/MySQL/etc.
in a real enterprise deployment; the rest of the code doesn't change
since it goes through SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'integration.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def reset_db():
    """Drop and recreate all tables — useful for demos/tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
