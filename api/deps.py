"""FastAPI dependency injection for database sessions."""
from collections.abc import Generator

from sqlalchemy.orm import Session

from brain.database import session_context


def get_db() -> Generator[Session, None, None]:
    """Yield a database session that auto-closes after the request."""
    with session_context() as db:
        yield db
