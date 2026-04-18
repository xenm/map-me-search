"""Shared fixtures for the test suite.

Centralises the postgres:16-alpine testcontainer so both
``test_persistence.py`` and ``test_integration.py`` can exercise the real
preferences store without paying the start-up cost twice.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_PG_IMAGE = "postgres:16-alpine"


@pytest.fixture(scope="session")
def postgres_asyncpg_url():
    """Spin up a postgres:16-alpine container for the whole test session and
    yield an asyncpg-compatible URL."""
    PostgresContainer = pytest.importorskip(
        "testcontainers.postgres", reason="testcontainers not installed"
    ).PostgresContainer
    with PostgresContainer(_PG_IMAGE) as pg:
        url = pg.get_connection_url()
        asyncpg_url = url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        ).replace("postgresql://", "postgresql+asyncpg://", 1)
        yield asyncpg_url
