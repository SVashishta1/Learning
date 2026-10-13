"""Database setup. The ONLY thing that changes between SQLite and PostgreSQL is DATABASE_URL."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default: a file called todos.db next to this script. For Postgres, set e.g.
#   DATABASE_URL=postgresql+psycopg://todo:todo@localhost:5432/todos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 'dependency': opens a DB session per request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
