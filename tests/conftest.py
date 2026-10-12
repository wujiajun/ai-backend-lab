import os
from pathlib import Path
from typing import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from ai_backend_lab.config import load_settings
from alembic import command


def _upgrade_test_database(
    database_url: str,
) -> None:
    original_database_url = os.environ.get("DATABASE_URL")

    try:
        os.environ["DATABASE_URL"] = database_url

        cache_clear = getattr(
            load_settings,
            "cache_clear",
            None,
        )

        if cache_clear is not None:
            cache_clear()

        project_root = Path(__file__).resolve().parent.parent

        alembic_config = Config(project_root / "alembic.ini")

        command.upgrade(
            alembic_config,
            "head",
        )

    finally:
        if original_database_url is None:
            os.environ.pop(
                "DATABASE_URL",
                None,
            )
        else:
            os.environ["DATABASE_URL"] = original_database_url

        cache_clear = getattr(
            load_settings,
            "cache_clear",
            None,
        )

        if cache_clear is not None:
            cache_clear()


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    database_url = os.environ["TEST_DATABASE_URL"]

    url = make_url(database_url)

    if url.database != "ai_backend_lab_test":
        raise RuntimeError("Integration tests must use ai_backend_lab_test.")

    _upgrade_test_database(database_url)

    engine = create_engine(database_url, pool_pre_ping=True)

    yield engine

    engine.dispose


@pytest.fixture
def uow_session_factory():
    database_url = os.environ["TEST_DATABASE_URL"]

    if not database_url.endswith("/ai_backend_lab_test"):
        raise RuntimeError("Integration tests must use ai_backend_lab_test.")

    engine = create_engine(database_url, pool_pre_ping=True)

    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    yield factory

    engine.dispose
