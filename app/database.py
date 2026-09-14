"""Database engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    """Yields a session and always closes it. FastAPI will use this as a
    dependency from day 2 onward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()