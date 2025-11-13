from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from db.connection import get_session


def get_db_session() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()
