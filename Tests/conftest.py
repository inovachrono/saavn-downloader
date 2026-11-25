import os

import pytest

from scripts.download_manager import Manager
from scripts.helper import create_session

LIVE = os.environ.get("SAAVN_LIVE") == "1"


def pytest_configure(config):
    config.addinivalue_line("markers", "live: calls the real JioSaavn API (set SAAVN_LIVE=1 to run)")


def pytest_collection_modifyitems(config, items):
    if LIVE:
        return
    skip = pytest.mark.skip(reason="live API test; set SAAVN_LIVE=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def session():
    return create_session()


@pytest.fixture
def manager(session, tmp_path):
    return Manager(session, out_folder=str(tmp_path))
