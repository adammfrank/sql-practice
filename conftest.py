# conftest.py
import re
import pytest
from dojo.config import load_config
from dojo.db import connect, clone_template, drop_database

def _exists(dbname: str) -> bool:
    with connect(load_config().maintenance_db, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        return cur.fetchone() is not None

@pytest.fixture(scope="session", autouse=True)
def template_ready():
    cfg = load_config()
    if not _exists(cfg.template_db):
        pytest.exit(f"Template '{cfg.template_db}' missing. Run: python -m dojo.seed", returncode=1)

@pytest.fixture
def lesson_db(request):
    slug = request.path.parent.name
    clone = "dojo_test_" + re.sub(r"[^a-z0-9_]", "_", slug.lower())
    clone_template(clone)
    conn = connect(clone)
    try:
        yield conn
    finally:
        conn.close()
        drop_database(clone)
