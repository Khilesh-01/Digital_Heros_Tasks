import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False mirrors real deployment behaviour, where
    # our catch-all handler converts unexpected errors into a 500 JSON body
    # instead of the test runner re-raising them.
    return TestClient(app, raise_server_exceptions=False)
