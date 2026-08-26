"""Shared fixtures. Everything runs offline against the FakeModel — no key, no net.

If the bundled database is missing (fresh clone), build it once for the session so
the query_database tests have data to read.
"""

from __future__ import annotations

import pytest

from tool_agent.agent import Agent
from tool_agent.fake_model import FakeModel
from tool_agent.tools import DB_PATH


@pytest.fixture(scope="session", autouse=True)
def _ensure_database():
    if not DB_PATH.exists():
        import generate_data

        generate_data.main()


@pytest.fixture
def agent() -> Agent:
    """An agent driven by the deterministic offline model."""
    return Agent(FakeModel())
