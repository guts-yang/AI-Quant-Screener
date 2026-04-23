from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models import ApiTokens


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    db_file = tmp_path / "unit_test.db"
    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_api_token(db_session: Session) -> ApiTokens:
    token = ApiTokens(
        access_token="seeded-access-token",
        refresh_token="seeded-refresh-token",
        expire_time=datetime.utcnow(),
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token
