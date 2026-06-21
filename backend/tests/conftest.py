import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Point the database module at a temp file before any imports that use it
os.environ["TESTING"] = "1"

from app.main import create_app
from app.database import init_db, DB_PATH


@pytest.fixture
def client():
    """Provide a TestClient backed by a fresh temporary database.

    Each test that uses this fixture gets its own isolated SQLite database
    that is created in a temp file, initialized with tables and default
    categories, and then deleted at the end of the test. This means tests
    never interfere with each other or with the real application database.

    The DB_PATH module-level variable in app.database is temporarily
    overridden so every get_db() call uses the temp file instead of
    the normal data/expenses.db.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db = tmp.name

    import app.database as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = temp_db

    init_db()
    app = create_app()
    with TestClient(app) as c:
        yield c

    db_module.DB_PATH = original_path
    os.unlink(temp_db)
