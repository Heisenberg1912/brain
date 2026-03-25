"""FastAPI dependency injection for database sessions."""
from collections.abc import Generator

from sqlalchemy.orm import Session

from brain.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session that auto-closes after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
