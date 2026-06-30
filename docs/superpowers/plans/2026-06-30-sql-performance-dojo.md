# SQL Performance Dojo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pytest-graded PostgreSQL course that teaches SQL performance and indexing, where each lesson is gated on correctness, query plan, and a calibrated speed target.

**Architecture:** A reusable `dojo/` harness package (config, connections, seeding, plan parsing, timing, grading, lesson loading) drives `pytest`. Postgres 16 runs via Docker Compose; data is seeded once into a `dojo_template` database that each lesson test clones for isolation. Lessons are numbered folders containing a README, a learner-edited `solution.sql`/`indexes.sql`, a hidden reference query `expected.sql`, and a `test_lesson.py` that composes harness assertions.

**Tech Stack:** Python 3.11+, pytest, psycopg v3, PostgreSQL 16, Faker, Docker Compose.

## Global Constraints

- Python 3.11+ only.
- DB driver is `psycopg` v3 (import name `psycopg`). No ORM; all lesson SQL is hand-written.
- PostgreSQL 16 via `docker-compose.yml`. Connection params come from environment variables with defaults (see Task 1).
- Data generation is deterministic: seed Python `random` and `Faker` with fixed seeds so every run produces identical data, plans, and comparable timings.
- The template database is named `dojo_template`. Per-lesson clones are named `dojo_test_<lesson_slug>`.
- Tests require Postgres running and the template seeded; harness must fail with an actionable message if not.
- `data/baseline.json` and the local `.env` are gitignored. `.env.example` is committed.
- Commit after every task with a conventional-commit message.

---

## File Structure

```
sql-practice/
  README.md                    # quickstart + how grading works (Task 14)
  pyproject.toml               # deps + pytest config (Task 1)
  requirements.txt             # mirror of runtime deps (Task 1)
  docker-compose.yml           # Postgres 16 + volume (Task 2)
  .env.example                 # connection defaults (Task 2)
  .gitignore                   # (Task 1)
  Makefile                     # up/down/seed/test convenience (Task 14)
  dojo/
    __init__.py
    config.py                  # DbConfig, load_config, conninfo (Task 3)
    db.py                      # connect, clone_template, drop_database, lesson_db ctx (Task 4)
    schema.sql                 # DDL for all tables (Task 5)
    seed.py                    # deterministic data generation -> dojo_template (Task 6)
    plan.py                    # explain() + Plan tree helpers (Task 7)
    timing.py                  # measure_execution_ms + baseline cache (Task 8)
    grader.py                  # assert_rows_equal/assert_plan/assert_faster_than_baseline (Task 9)
    lesson.py                  # Lesson loader (reads sql files, applies indexes) (Task 10)
  tests/
    test_config.py             # (Task 3)
    test_plan.py               # (Task 7)
    test_timing.py             # (Task 8)
    test_grader.py             # (Task 9)
    test_lesson_loader.py      # (Task 10)
    test_smoke.py              # end-to-end seed+clone+trivial query (Task 11)
  conftest.py                  # fixtures: template_ready, lesson_db (Task 11)
  data/
    .gitkeep
    baseline.json              # generated, gitignored
  lessons/
    00_setup/ ... 18_capstone/ # (Tasks 12, 13, 15-19)
```

---

## Task 1: Project scaffolding (deps, config files, gitignore)

**Files:**
- Create: `pyproject.toml`, `requirements.txt`, `.gitignore`, `data/.gitkeep`, `dojo/__init__.py`

**Interfaces:**
- Produces: an installable dev environment; `pytest` configured to discover `tests/`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "sql-performance-dojo"
version = "0.1.0"
description = "A pytest-graded PostgreSQL course on performance and indexing"
requires-python = ">=3.11"
dependencies = [
    "psycopg[binary]>=3.1",
    "faker>=24.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests", "lessons"]
python_files = ["test_*.py", "test_lesson.py"]
addopts = "-ra"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Write `requirements.txt`**

```
psycopg[binary]>=3.1
faker>=24.0
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.pyc
.env
data/baseline.json
.pytest_cache/
.venv/
```

- [ ] **Step 4: Create empty `dojo/__init__.py` and `data/.gitkeep`**

Both empty files.

- [ ] **Step 5: Create and verify the virtualenv**

Run: `python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"`
Expected: installs psycopg, faker, python-dotenv, pytest without error.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml requirements.txt .gitignore dojo/__init__.py data/.gitkeep
git commit -m "chore: project scaffolding and dependencies"
```

---

## Task 2: Docker Compose + environment template

**Files:**
- Create: `docker-compose.yml`, `.env.example`

**Interfaces:**
- Produces: Postgres 16 reachable on `localhost:5432` (override via env); credentials `dojo`/`dojo`, maintenance db `postgres`.

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: dojo
      POSTGRES_PASSWORD: dojo
      POSTGRES_DB: postgres
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - dojo_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dojo"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  dojo_pgdata:
```

- [ ] **Step 2: Write `.env.example`**

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dojo
POSTGRES_PASSWORD=dojo
POSTGRES_MAINTENANCE_DB=postgres
DOJO_TEMPLATE_DB=dojo_template
```

- [ ] **Step 3: Start Postgres and verify health**

Run: `docker compose up -d && docker compose ps`
Expected: the `db` service is `healthy` within ~30s.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "chore: add Postgres 16 docker-compose and env template"
```

---

## Task 3: Configuration module

**Files:**
- Create: `dojo/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `DbConfig` dataclass with fields `host: str, port: int, user: str, password: str, maintenance_db: str, template_db: str`.
  - `load_config() -> DbConfig` — reads env vars (loading `.env` if present) with the defaults from `.env.example`.
  - `conninfo(cfg: DbConfig, dbname: str) -> str` — returns a libpq conninfo string for the given database name.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from dojo.config import DbConfig, load_config, conninfo

def test_load_config_defaults(monkeypatch):
    for k in ["POSTGRES_HOST","POSTGRES_PORT","POSTGRES_USER","POSTGRES_PASSWORD",
              "POSTGRES_MAINTENANCE_DB","DOJO_TEMPLATE_DB"]:
        monkeypatch.delenv(k, raising=False)
    cfg = load_config()
    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.user == "dojo"
    assert cfg.maintenance_db == "postgres"
    assert cfg.template_db == "dojo_template"

def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("POSTGRES_PORT", "6000")
    monkeypatch.setenv("POSTGRES_USER", "alice")
    cfg = load_config()
    assert cfg.port == 6000
    assert cfg.user == "alice"

def test_conninfo_contains_dbname():
    cfg = DbConfig("localhost", 5432, "dojo", "dojo", "postgres", "dojo_template")
    s = conninfo(cfg, "dojo_test_x")
    assert "dbname=dojo_test_x" in s
    assert "host=localhost" in s
    assert "port=5432" in s
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dojo.config'`.

- [ ] **Step 3: Write minimal implementation**

```python
# dojo/config.py
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    maintenance_db: str
    template_db: str

def load_config() -> DbConfig:
    return DbConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "dojo"),
        password=os.getenv("POSTGRES_PASSWORD", "dojo"),
        maintenance_db=os.getenv("POSTGRES_MAINTENANCE_DB", "postgres"),
        template_db=os.getenv("DOJO_TEMPLATE_DB", "dojo_template"),
    )

def conninfo(cfg: DbConfig, dbname: str) -> str:
    return (
        f"host={cfg.host} port={cfg.port} user={cfg.user} "
        f"password={cfg.password} dbname={dbname}"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add dojo/config.py tests/test_config.py
git commit -m "feat: add config module with env-driven DbConfig"
```

---

## Task 4: Connection + clone/drop database helpers

**Files:**
- Create: `dojo/db.py`

**Interfaces:**
- Consumes: `dojo.config.load_config`, `conninfo`.
- Produces:
  - `connect(dbname: str, autocommit: bool = False) -> psycopg.Connection`
  - `clone_template(clone_name: str, template: str | None = None) -> None` — connects to the maintenance db with autocommit, runs `DROP DATABASE IF EXISTS <clone> (WITH FORCE)` then `CREATE DATABASE <clone> TEMPLATE <template>`. Identifiers quoted via `psycopg.sql`.
  - `drop_database(name: str) -> None` — drops `<name>` with force from the maintenance db.

**Note:** No dedicated unit test here — exercised by `test_smoke.py` (Task 11) and every lesson. Identifier quoting prevents injection from clone names.

- [ ] **Step 1: Write implementation**

```python
# dojo/db.py
import psycopg
from psycopg import sql
from dojo.config import load_config, conninfo

def connect(dbname: str, autocommit: bool = False) -> psycopg.Connection:
    cfg = load_config()
    conn = psycopg.connect(conninfo(cfg, dbname))
    conn.autocommit = autocommit
    return conn

def _maintenance_conn() -> psycopg.Connection:
    cfg = load_config()
    return connect(cfg.maintenance_db, autocommit=True)

def clone_template(clone_name: str, template: str | None = None) -> None:
    cfg = load_config()
    template = template or cfg.template_db
    with _maintenance_conn() as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
            sql.Identifier(clone_name)))
        cur.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
            sql.Identifier(clone_name), sql.Identifier(template)))

def drop_database(name: str) -> None:
    with _maintenance_conn() as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
            sql.Identifier(name)))
```

- [ ] **Step 2: Smoke-check against running Postgres**

Run: `.venv/Scripts/python -c "from dojo.db import connect; connect('postgres').close(); print('ok')"`
Expected: prints `ok` (Postgres from Task 2 must be up).

- [ ] **Step 3: Commit**

```bash
git add dojo/db.py
git commit -m "feat: add connection and template clone/drop helpers"
```

---

## Task 5: Database schema DDL

**Files:**
- Create: `dojo/schema.sql`

**Interfaces:**
- Produces: tables `customers, products, orders, order_items, reviews, events` with the columns the lessons rely on. Primary keys and foreign keys only — **no** secondary indexes (those are the learner's job). `events.ts` is a real timestamp; `products.attributes` and `events.payload` are `jsonb`; `reviews.body` and `products.description` are `text`.

- [ ] **Step 1: Write `dojo/schema.sql`**

```sql
CREATE TABLE customers (
    id          bigint PRIMARY KEY,
    name        text NOT NULL,
    email       text NOT NULL,
    country     text NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE products (
    id          bigint PRIMARY KEY,
    name        text NOT NULL,
    category    text NOT NULL,
    price       numeric(10,2) NOT NULL,
    description text NOT NULL,
    attributes  jsonb NOT NULL
);

CREATE TABLE orders (
    id          bigint PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status      text NOT NULL,
    total       numeric(12,2) NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE order_items (
    id          bigint PRIMARY KEY,
    order_id    bigint NOT NULL REFERENCES orders(id),
    product_id  bigint NOT NULL REFERENCES products(id),
    quantity    int NOT NULL,
    price       numeric(10,2) NOT NULL
);

CREATE TABLE reviews (
    id          bigint PRIMARY KEY,
    product_id  bigint NOT NULL REFERENCES products(id),
    rating      int NOT NULL,
    body        text NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE events (
    id          bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    event_type  text NOT NULL,
    payload     jsonb NOT NULL,
    ts          timestamptz NOT NULL
);
```

- [ ] **Step 2: Validate the DDL applies**

Run: `docker compose exec -T db psql -U dojo -d postgres -c "CREATE DATABASE ddlcheck;" && docker compose exec -T db psql -U dojo -d ddlcheck -f - < dojo/schema.sql && docker compose exec -T db psql -U dojo -d postgres -c "DROP DATABASE ddlcheck;"`
Expected: all `CREATE TABLE` succeed, no errors.

- [ ] **Step 3: Commit**

```bash
git add dojo/schema.sql
git commit -m "feat: add e-commerce schema DDL"
```

---

## Task 6: Deterministic seeding into the template database

**Files:**
- Create: `dojo/seed.py`

**Interfaces:**
- Consumes: `dojo.config`, `dojo.db.connect`, `dojo/schema.sql`.
- Produces: `main()` (entrypoint for `python -m dojo.seed`) that drops/creates `dojo_template`, applies the schema, generates deterministic data with these counts, runs `ANALYZE`. Row counts: customers 50_000, products 10_000, orders 500_000, order_items 1_000_000, reviews 1_000_000, events 3_000_000. Helper `generate(conn)` does the data load using `COPY` for speed and `Faker` seeded at 1234, `random.seed(1234)`.

**Implementation notes for the engineer:**
- Use `random.Random(1234)` and `Faker(); Faker.seed(1234)` for reproducibility.
- Use `cursor.copy()` (psycopg v3 COPY) to bulk-load each table — row-by-row INSERT of millions of rows is far too slow.
- `events.ts` spans the last 365 days, monotonic-ish (shuffle lightly) so BRIN is meaningful; `orders.created_at` similar.
- `orders.status` drawn from `['pending','paid','shipped','cancelled']` with skew (most `paid`) so partial-index and selectivity lessons have realistic distributions.
- `products.attributes` jsonb like `{"color": "...", "size": "...", "tags": [...]}`.
- `events.payload` jsonb like `{"path": "...", "value": N}`.
- `reviews.body` from `faker.paragraph()` so full-text search has real words.
- Print progress per table and total elapsed.

- [ ] **Step 1: Write `dojo/seed.py`**

```python
# dojo/seed.py
import io
import random
import time
from pathlib import Path

from faker import Faker
from psycopg import sql

from dojo.config import load_config
from dojo.db import connect

SCHEMA = (Path(__file__).parent / "schema.sql").read_text()

N_CUSTOMERS = 50_000
N_PRODUCTS = 10_000
N_ORDERS = 500_000
N_ORDER_ITEMS = 1_000_000
N_REVIEWS = 1_000_000
N_EVENTS = 3_000_000

STATUSES = ["pending", "paid", "paid", "paid", "shipped", "cancelled"]
CATEGORIES = ["books", "electronics", "garden", "toys", "clothing", "food"]
COLORS = ["red", "green", "blue", "black", "white"]
SIZES = ["s", "m", "l", "xl"]
EVENT_TYPES = ["view", "click", "add_to_cart", "purchase", "logout"]

def _copy(cur, table, columns, rows):
    cols = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
    stmt = sql.SQL("COPY {} ({}) FROM STDIN").format(sql.Identifier(table), cols)
    with cur.copy(stmt) as cp:
        for r in rows:
            cp.write_row(r)

def generate(conn, rng: random.Random, fake: Faker):
    base = 1_700_000_000  # fixed epoch base for deterministic timestamps
    day = 86_400

    with conn.cursor() as cur:
        # customers
        _copy(cur, "customers", ["id","name","email","country","created_at"],
              ((i, fake.name(), f"user{i}@example.com",
                fake.country_code(),
                _ts(base - rng.randint(0, 730) * day))
               for i in range(1, N_CUSTOMERS + 1)))
        # products
        _copy(cur, "products", ["id","name","category","price","description","attributes"],
              ((i, fake.catch_phrase(), rng.choice(CATEGORIES),
                round(rng.uniform(1, 500), 2), fake.paragraph(nb_sentences=3),
                _json({"color": rng.choice(COLORS), "size": rng.choice(SIZES),
                       "tags": rng.sample(CATEGORIES, 2)}))
               for i in range(1, N_PRODUCTS + 1)))
        # orders
        _copy(cur, "orders", ["id","customer_id","status","total","created_at"],
              ((i, rng.randint(1, N_CUSTOMERS), rng.choice(STATUSES),
                round(rng.uniform(5, 2000), 2),
                _ts(base - rng.randint(0, 365) * day))
               for i in range(1, N_ORDERS + 1)))
        # order_items
        _copy(cur, "order_items", ["id","order_id","product_id","quantity","price"],
              ((i, rng.randint(1, N_ORDERS), rng.randint(1, N_PRODUCTS),
                rng.randint(1, 5), round(rng.uniform(1, 500), 2))
               for i in range(1, N_ORDER_ITEMS + 1)))
        # reviews
        _copy(cur, "reviews", ["id","product_id","rating","body","created_at"],
              ((i, rng.randint(1, N_PRODUCTS), rng.randint(1, 5),
                fake.paragraph(nb_sentences=5),
                _ts(base - rng.randint(0, 365) * day))
               for i in range(1, N_REVIEWS + 1)))
        # events (time-ordered for BRIN)
        _copy(cur, "events", ["id","customer_id","event_type","payload","ts"],
              ((i, rng.randint(1, N_CUSTOMERS), rng.choice(EVENT_TYPES),
                _json({"path": f"/p/{rng.randint(1, N_PRODUCTS)}", "value": rng.randint(0, 1000)}),
                _ts(base - N_EVENTS + i))  # strictly increasing -> ideal for BRIN
               for i in range(1, N_EVENTS + 1)))
    conn.commit()

def _ts(epoch_seconds: int) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(epoch_seconds, tz=dt.timezone.utc).isoformat()

def _json(obj) -> str:
    import json
    return json.dumps(obj)

def main():
    cfg = load_config()
    rng = random.Random(1234)
    fake = Faker()
    Faker.seed(1234)

    # (re)create template from maintenance db
    from dojo.db import drop_database
    drop_database(cfg.template_db)
    with connect(cfg.maintenance_db, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cfg.template_db)))

    with connect(cfg.template_db) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
        t0 = time.time()
        generate(conn, rng, fake)
        with conn.cursor() as cur:
            cur.execute("ANALYZE")
        conn.commit()
        print(f"Seeded {cfg.template_db} in {time.time() - t0:.1f}s")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the seed**

Run: `.venv/Scripts/python -m dojo.seed`
Expected: prints `Seeded dojo_template in <N>s`; no errors. (May take a few minutes for 3M events.)

- [ ] **Step 3: Verify row counts**

Run: `docker compose exec -T db psql -U dojo -d dojo_template -c "SELECT count(*) FROM events;"`
Expected: `3000000`.

- [ ] **Step 4: Commit**

```bash
git add dojo/seed.py
git commit -m "feat: deterministic data seeding into template database"
```

---

## Task 7: Query plan parsing

**Files:**
- Create: `dojo/plan.py`
- Test: `tests/test_plan.py`

**Interfaces:**
- Consumes: a live `psycopg.Connection`.
- Produces:
  - `explain(conn, query: str, params=None, analyze: bool = True) -> Plan` — runs `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <query>` (or without ANALYZE when `analyze=False`) and returns a `Plan`.
  - `class Plan` with: `.root: dict`, `.nodes() -> list[dict]` (pre-order flatten of `Plan`/`Plans`), `.node_types() -> list[str]`, `.has_node(node_type: str) -> bool`, `.uses_index(index_name: str) -> bool` (any node whose `Index Name` == name), `.execution_time_ms: float`, `.planning_time_ms: float`, `.render() -> str` (compact text of node types for failure messages).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plan.py
from dojo.plan import Plan

SAMPLE = [{
    "Plan": {
        "Node Type": "Aggregate",
        "Plans": [
            {"Node Type": "Index Scan", "Index Name": "idx_orders_customer",
             "Plans": [{"Node Type": "Seq Scan"}]}
        ]
    },
    "Execution Time": 12.5,
    "Planning Time": 0.3,
}]

def test_node_types_preorder():
    p = Plan(SAMPLE)
    assert p.node_types() == ["Aggregate", "Index Scan", "Seq Scan"]

def test_has_node():
    p = Plan(SAMPLE)
    assert p.has_node("Index Scan")
    assert not p.has_node("Hash Join")

def test_uses_index():
    p = Plan(SAMPLE)
    assert p.uses_index("idx_orders_customer")
    assert not p.uses_index("nope")

def test_times():
    p = Plan(SAMPLE)
    assert p.execution_time_ms == 12.5
    assert p.planning_time_ms == 0.3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_plan.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'dojo.plan'`.

- [ ] **Step 3: Write implementation**

```python
# dojo/plan.py
class Plan:
    def __init__(self, explain_json: list):
        self._top = explain_json[0]
        self.root = self._top["Plan"]

    def nodes(self) -> list[dict]:
        out = []
        def walk(n):
            out.append(n)
            for child in n.get("Plans", []):
                walk(child)
        walk(self.root)
        return out

    def node_types(self) -> list[str]:
        return [n["Node Type"] for n in self.nodes()]

    def has_node(self, node_type: str) -> bool:
        return node_type in self.node_types()

    def uses_index(self, index_name: str) -> bool:
        return any(n.get("Index Name") == index_name for n in self.nodes())

    @property
    def execution_time_ms(self) -> float:
        return float(self._top.get("Execution Time", 0.0))

    @property
    def planning_time_ms(self) -> float:
        return float(self._top.get("Planning Time", 0.0))

    def render(self) -> str:
        return " -> ".join(self.node_types())


def explain(conn, query: str, params=None, analyze: bool = True) -> Plan:
    opts = "ANALYZE, BUFFERS, FORMAT JSON" if analyze else "FORMAT JSON"
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN ({opts}) " + query, params)
        data = cur.fetchone()[0]
    return Plan(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_plan.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add dojo/plan.py tests/test_plan.py
git commit -m "feat: add EXPLAIN plan parsing and Plan helpers"
```

---

## Task 8: Timing measurement + baseline cache

**Files:**
- Create: `dojo/timing.py`
- Test: `tests/test_timing.py`

**Interfaces:**
- Consumes: `dojo.plan.explain`.
- Produces:
  - `measure_execution_ms(conn, query, params=None, repeats: int = 5, warmup: int = 1) -> float` — runs `explain(analyze=True)` `repeats` times after `warmup` runs, returns the **minimum** `execution_time_ms` (most stable).
  - `load_baseline() -> dict` / `save_baseline(d: dict) -> None` — read/write `data/baseline.json` (returns `{}` if absent).
  - `cached_baseline(conn, key: str, query, params=None) -> float` — return cached ms for `key` if present, else measure, store, and return.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_timing.py
import json
from dojo import timing

def test_measure_uses_min(monkeypatch):
    times = iter([50.0, 9.0, 30.0, 12.0, 7.0, 40.0])  # warmup + 5
    class FakePlan:
        def __init__(self, t): self.execution_time_ms = t
    def fake_explain(conn, q, params=None, analyze=True):
        return FakePlan(next(times))
    monkeypatch.setattr(timing, "explain", fake_explain)
    assert timing.measure_execution_ms(None, "SELECT 1") == 7.0

def test_baseline_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "baseline.json"
    monkeypatch.setattr(timing, "BASELINE_PATH", f)
    timing.save_baseline({"02_first_index": 123.4})
    assert timing.load_baseline()["02_first_index"] == 123.4

def test_cached_baseline_caches(tmp_path, monkeypatch):
    f = tmp_path / "baseline.json"
    monkeypatch.setattr(timing, "BASELINE_PATH", f)
    calls = []
    monkeypatch.setattr(timing, "measure_execution_ms",
                        lambda *a, **k: calls.append(1) or 55.0)
    a = timing.cached_baseline(None, "k", "SELECT 1")
    b = timing.cached_baseline(None, "k", "SELECT 1")
    assert a == b == 55.0
    assert len(calls) == 1  # measured once, then cached
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_timing.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'dojo.timing'`.

- [ ] **Step 3: Write implementation**

```python
# dojo/timing.py
import json
from pathlib import Path
from dojo.plan import explain

BASELINE_PATH = Path(__file__).parent.parent / "data" / "baseline.json"

def measure_execution_ms(conn, query, params=None, repeats: int = 5, warmup: int = 1) -> float:
    for _ in range(warmup):
        explain(conn, query, params, analyze=True)
    times = [explain(conn, query, params, analyze=True).execution_time_ms
             for _ in range(repeats)]
    return min(times)

def load_baseline() -> dict:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text())
    return {}

def save_baseline(d: dict) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(d, indent=2))

def cached_baseline(conn, key: str, query, params=None) -> float:
    data = load_baseline()
    if key in data:
        return data[key]
    ms = measure_execution_ms(conn, query, params)
    data[key] = ms
    save_baseline(data)
    return ms
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_timing.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add dojo/timing.py tests/test_timing.py
git commit -m "feat: add timing measurement and baseline cache"
```

---

## Task 9: Grading assertions

**Files:**
- Create: `dojo/grader.py`
- Test: `tests/test_grader.py`

**Interfaces:**
- Consumes: `dojo.plan.Plan`.
- Produces (each raises `AssertionError` with a teaching message on failure):
  - `assert_rows_equal(actual: list, expected: list, ordered: bool = False) -> None`
  - `assert_plan(plan: Plan, must_have: list[str] | None = None, must_not_have: list[str] | None = None, uses_index: str | None = None) -> None` — failure message includes `plan.render()`.
  - `assert_faster_than_baseline(measured_ms: float, baseline_ms: float, ratio: float, floor_ms: float = 2.0) -> None` — passes if `measured_ms <= baseline_ms / ratio` OR `baseline_ms < floor_ms` (too fast to matter). Failure message shows both times and the achieved ratio.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_grader.py
import pytest
from dojo import grader
from dojo.plan import Plan

def mk(node_types, index=None):
    root = {"Node Type": node_types[0]}
    cur = root
    for nt in node_types[1:]:
        child = {"Node Type": nt}
        if index and nt.endswith("Scan"):
            child["Index Name"] = index
        cur["Plans"] = [child]; cur = child
    return Plan([{"Plan": root, "Execution Time": 1.0, "Planning Time": 0.1}])

def test_rows_equal_unordered():
    grader.assert_rows_equal([(1,),(2,)], [(2,),(1,)])

def test_rows_equal_mismatch():
    with pytest.raises(AssertionError):
        grader.assert_rows_equal([(1,)], [(2,)])

def test_assert_plan_must_have_ok():
    grader.assert_plan(mk(["Aggregate","Index Scan"]), must_have=["Index Scan"])

def test_assert_plan_must_not_have_fails():
    with pytest.raises(AssertionError):
        grader.assert_plan(mk(["Seq Scan"]), must_not_have=["Seq Scan"])

def test_assert_uses_index():
    grader.assert_plan(mk(["Index Scan"], index="idx_x"), uses_index="idx_x")

def test_faster_ok():
    grader.assert_faster_than_baseline(10.0, 100.0, ratio=8)

def test_faster_fails():
    with pytest.raises(AssertionError):
        grader.assert_faster_than_baseline(50.0, 100.0, ratio=8)

def test_faster_floor_skips():
    grader.assert_faster_than_baseline(1.5, 1.0, ratio=8)  # baseline under floor -> pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_grader.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'dojo.grader'`.

- [ ] **Step 3: Write implementation**

```python
# dojo/grader.py
from dojo.plan import Plan

def assert_rows_equal(actual, expected, ordered: bool = False) -> None:
    a = list(actual) if ordered else sorted(map(tuple, actual))
    e = list(expected) if ordered else sorted(map(tuple, expected))
    assert a == e, (
        f"Result rows differ.\n  expected {len(e)} rows, got {len(a)}.\n"
        f"  first expected: {e[:3]}\n  first actual:   {a[:3]}"
    )

def assert_plan(plan: Plan, must_have=None, must_not_have=None, uses_index=None) -> None:
    for nt in (must_have or []):
        assert plan.has_node(nt), (
            f"Expected plan to contain a '{nt}' node.\n  plan: {plan.render()}"
        )
    for nt in (must_not_have or []):
        assert not plan.has_node(nt), (
            f"Plan should NOT contain a '{nt}' node (you're still doing that).\n"
            f"  plan: {plan.render()}"
        )
    if uses_index is not None:
        assert plan.uses_index(uses_index), (
            f"Expected the plan to use index '{uses_index}'.\n  plan: {plan.render()}"
        )

def assert_faster_than_baseline(measured_ms, baseline_ms, ratio, floor_ms=2.0) -> None:
    if baseline_ms < floor_ms:
        return
    target = baseline_ms / ratio
    achieved = baseline_ms / measured_ms if measured_ms else float("inf")
    assert measured_ms <= target, (
        f"Too slow. baseline={baseline_ms:.2f}ms, yours={measured_ms:.2f}ms, "
        f"need <= {target:.2f}ms (>= {ratio}x faster). You achieved {achieved:.1f}x."
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_grader.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add dojo/grader.py tests/test_grader.py
git commit -m "feat: add grading assertions for rows, plan, and speed"
```

---

## Task 10: Lesson loader

**Files:**
- Create: `dojo/lesson.py`
- Test: `tests/test_lesson_loader.py`

**Interfaces:**
- Produces:
  - `class Lesson` constructed as `Lesson(test_file_path: str)` — `dir = Path(test_file_path).parent`.
  - `.slug -> str` (the directory name, e.g. `02_first_index`).
  - `.read(name: str) -> str` — read `<dir>/<name>`; return `""` if absent.
  - `.solution_sql -> str`, `.indexes_sql -> str`, `.expected_sql -> str` (read the respective files).
  - `.apply_indexes(conn) -> None` — execute `indexes.sql` if non-empty/non-blank, then `conn.commit()`.
  - `.fetch(conn, query_sql: str) -> list[tuple]` — execute and `fetchall()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lesson_loader.py
from dojo.lesson import Lesson

def test_slug_and_read(tmp_path):
    d = tmp_path / "02_first_index"
    d.mkdir()
    (d / "solution.sql").write_text("SELECT 1;")
    (d / "test_lesson.py").write_text("")
    lesson = Lesson(str(d / "test_lesson.py"))
    assert lesson.slug == "02_first_index"
    assert lesson.solution_sql.strip() == "SELECT 1;"
    assert lesson.indexes_sql == ""        # missing file -> empty
    assert lesson.expected_sql == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_lesson_loader.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'dojo.lesson'`.

- [ ] **Step 3: Write implementation**

```python
# dojo/lesson.py
from pathlib import Path

class Lesson:
    def __init__(self, test_file_path: str):
        self.dir = Path(test_file_path).parent
        self.slug = self.dir.name

    def read(self, name: str) -> str:
        f = self.dir / name
        return f.read_text() if f.exists() else ""

    @property
    def solution_sql(self) -> str:
        return self.read("solution.sql")

    @property
    def indexes_sql(self) -> str:
        return self.read("indexes.sql")

    @property
    def expected_sql(self) -> str:
        return self.read("expected.sql")

    def apply_indexes(self, conn) -> None:
        ddl = self.indexes_sql.strip()
        if ddl:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def fetch(self, conn, query_sql: str):
        with conn.cursor() as cur:
            cur.execute(query_sql)
            return cur.fetchall()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_lesson_loader.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add dojo/lesson.py tests/test_lesson_loader.py
git commit -m "feat: add lesson loader for sql files and index application"
```

---

## Task 11: pytest fixtures + end-to-end smoke test

**Files:**
- Create: `conftest.py`, `tests/test_smoke.py`

**Interfaces:**
- Consumes: `dojo.config`, `dojo.db`.
- Produces fixtures:
  - `template_ready` (session scope, autouse) — verifies the template DB exists; if not, `pytest.exit("Run 'python -m dojo.seed' first")`.
  - `lesson_db(request)` (function scope) — derives a clone name from the requesting test's directory slug (or module name for harness tests), calls `clone_template`, yields an open connection to the clone, and drops the clone on teardown.

- [ ] **Step 1: Write `conftest.py`**

```python
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
```

- [ ] **Step 2: Write `tests/test_smoke.py`**

```python
# tests/test_smoke.py
def test_clone_has_seeded_data(lesson_db):
    with lesson_db.cursor() as cur:
        cur.execute("SELECT count(*) FROM customers")
        assert cur.fetchone()[0] == 50_000
        cur.execute("SELECT count(*) FROM events")
        assert cur.fetchone()[0] == 3_000_000
```

- [ ] **Step 3: Run the smoke test**

Run: `.venv/Scripts/pytest tests/test_smoke.py -v`
Expected: 1 passed (requires Postgres up and `python -m dojo.seed` already run).

- [ ] **Step 4: Run the whole harness suite**

Run: `.venv/Scripts/pytest tests -v`
Expected: all harness tests pass.

- [ ] **Step 5: Commit**

```bash
git add conftest.py tests/test_smoke.py
git commit -m "test: add pytest fixtures and end-to-end smoke test"
```

---

## Lesson Authoring Procedure (referenced by all lesson tasks)

Every lesson task below produces a folder `lessons/<slug>/` with four files and follows this same procedure. The per-lesson task gives the specifics (problem, reference query, technique, plan assertions, ratio).

**Files per lesson:**
- `README.md` — problem statement, hints about the target plan, and the performance target.
- `expected.sql` — the canonical correct query (the answer key for *correctness*). Committed.
- `solution.sql` — starter file the learner edits. Committed with a comment stub only.
- `indexes.sql` — starter file for the learner's DDL. Committed empty (or with a comment).
- `test_lesson.py` — the gate, written per the template below.

**`test_lesson.py` template** (fill the bracketed parts from the per-lesson spec):

```python
from dojo.lesson import Lesson
from dojo import grader, timing, plan as planmod

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    # 1. correctness: compare learner solution to reference query
    expected = lesson.fetch(conn, lesson.expected_sql)
    # baseline measured BEFORE the learner's indexes exist (naive cost)
    baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)
    lesson.apply_indexes(conn)
    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=<ORDERED>)
    # 2. plan
    p = planmod.explain(conn, lesson.solution_sql)
    grader.assert_plan(p, must_have=<MUST_HAVE>, must_not_have=<MUST_NOT_HAVE>,
                       uses_index=<USES_INDEX>)
    # 3. speed
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    grader.assert_faster_than_baseline(measured, baseline, ratio=<RATIO>, floor_ms=2.0)
```

For lessons that are *not* index-speedup-shaped (statistics, vacuum/bloat, partitioning, materialized views), the per-lesson spec replaces the speed/plan section with the assertions named in that lesson's task (e.g. assert estimated-vs-actual rows ratio, assert partition pruning prunes to one partition, assert bloat dropped after VACUUM). Each such task spells out the exact assertions — do not use the ratio template there.

**Authoring loop for each lesson (TDD-for-content):**
1. Write `README.md`, `expected.sql`, `indexes.sql` (empty), `solution.sql` (stub), `test_lesson.py`.
2. Run `pytest lessons/<slug>` → it must FAIL (stub solution doesn't pass the gate). This proves the gate bites.
3. Write the *reference answer* into `solution.sql` and `indexes.sql` temporarily; run `pytest lessons/<slug>` → must PASS. This proves the lesson is solvable and the target is achievable.
4. Reset `solution.sql`/`indexes.sql` to their starter stubs; confirm FAIL again.
5. Commit.

---

## Task 12: Lesson 00 — setup & profiling vocabulary

**Files:** Create `lessons/00_setup/{README.md,expected.sql,solution.sql,indexes.sql,test_lesson.py}`

**Spec:**
- **Teaches:** how to run the harness and read `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`; what a Seq Scan is.
- **Problem (`expected.sql`):** `SELECT count(*) FROM orders WHERE status = 'pending';`
- **Gate:** correctness only (no plan/speed assertion) — this lesson just confirms the environment works and teaches reading a plan. `test_lesson.py` asserts `assert_rows_equal` and additionally asserts the plan **has** a `Seq Scan` (to show the learner the un-indexed baseline), with NO speed assertion.
- **README:** explain the EXPLAIN options, point to `docker compose up` + `python -m dojo.seed`, show how to run `pytest lessons/00_setup`.
- `solution.sql` ships pre-filled with the correct query here (lesson 00 is a guided warm-up; the learner just runs it).

- [ ] **Step 1:** Write all five files per the spec and the authoring procedure.
- [ ] **Step 2:** Run `.venv/Scripts/pytest lessons/00_setup -v` → PASS (solution pre-filled).
- [ ] **Step 3:** Commit: `git add lessons/00_setup && git commit -m "feat: lesson 00 setup and profiling vocabulary"`

---

## Task 13: Lesson 01 — select/filter refresher

**Files:** Create `lessons/01_select_filter/{README.md,expected.sql,solution.sql,indexes.sql,test_lesson.py}`

**Spec:**
- **Teaches:** JOIN/WHERE/GROUP BY refresher; correctness-only gate.
- **Problem:** "Total revenue (`SUM(oi.quantity*oi.price)`) per product category for `paid` orders." 
- **`expected.sql`:**
```sql
SELECT p.category, SUM(oi.quantity * oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'paid'
GROUP BY p.category;
```
- **Gate:** correctness only (`assert_rows_equal`, unordered). No plan/speed assertion (this re-acclimates the learner).
- `solution.sql` ships as a stub comment; learner writes the query.

- [ ] **Step 1:** Write files; follow authoring loop (stub fails, reference passes, reset to stub).
- [ ] **Step 2:** Verify with reference answer: PASS; with stub: FAIL.
- [ ] **Step 3:** Commit: `git add lessons/01_select_filter && git commit -m "feat: lesson 01 select/filter refresher"`

---

## Task 14: README, Makefile, and onboarding docs

**Files:** Create `README.md` (root), `Makefile`

**Interfaces:** Produces the canonical "start here" doc and `make` shortcuts.

- [ ] **Step 1: Write `Makefile`**

```makefile
.PHONY: up down seed test
up:
	docker compose up -d
down:
	docker compose down
seed:
	.venv/Scripts/python -m dojo.seed
test:
	.venv/Scripts/pytest
```

- [ ] **Step 2: Write `README.md`** covering: prerequisites (Docker, Python 3.11+); setup (`python -m venv`, install, copy `.env.example` to `.env`, `make up`, `make seed`); the gameplay loop (read README, edit `indexes.sql`/`solution.sql`, run `pytest lessons/NN_*`); how grading works (correctness → plan → speed vs. calibrated baseline); the curriculum list (Parts 0–6 with the 19 lesson slugs); and a "resetting your baseline" note (delete `data/baseline.json`).

- [ ] **Step 3: Verify the documented setup path** by following the README from scratch in a clean checkout mentally; ensure commands match actual file names.

- [ ] **Step 4: Commit**

```bash
git add README.md Makefile
git commit -m "docs: add README quickstart and Makefile"
```

---

## Tasks 15–19: Remaining lessons

Each task below = one lesson folder authored via the **Lesson Authoring Procedure**. The spec gives the reference query/technique and the exact gate. Group related lessons but commit per lesson. For every lesson: stub must FAIL, reference answer must PASS, then reset stub.

### Task 15: Part 2 — Core B-tree indexing (4 lessons)

- [ ] **`02_first_index`** — Teaches single-column B-tree. Problem: `SELECT id,total,created_at FROM orders WHERE customer_id = 4242;`. Reference `indexes.sql`: `CREATE INDEX idx_orders_customer ON orders(customer_id);`. Gate: `must_have=["Index Scan"]`, `must_not_have=["Seq Scan"]`, `uses_index="idx_orders_customer"`, `ratio=8`. Commit.
- [ ] **`03_composite_index`** — Teaches multi-column index + column order. Problem: `SELECT id FROM orders WHERE customer_id = 4242 AND status = 'paid';`. Reference index: `CREATE INDEX idx_orders_cust_status ON orders(customer_id, status);`. Gate: `must_have=["Index Scan"]`, `must_not_have=["Seq Scan"]`, `uses_index="idx_orders_cust_status"`, `ratio=8`. README explains why `(customer_id,status)` beats two single-column indexes here. Commit.
- [ ] **`04_left_prefix`** — Teaches the left-prefix rule. Problem: `SELECT id FROM orders WHERE status = 'shipped';` given that an index on `(customer_id,status)` already exists (ship it pre-created in `indexes.sql` as the "wrong" index). The learner must add the correct index `CREATE INDEX idx_orders_status ON orders(status);`. Gate: `uses_index="idx_orders_status"`, `must_not_have=["Seq Scan"]`, `ratio=5`. README explains why the composite index's second column can't be used alone. Commit.
- [ ] **`05_index_only_scan`** — Teaches covering indexes via `INCLUDE` + Index Only Scan. Problem: `SELECT customer_id, total FROM orders WHERE customer_id BETWEEN 1000 AND 1100;`. Reference index: `CREATE INDEX idx_orders_cust_incl ON orders(customer_id) INCLUDE (total);` then `VACUUM orders;` (note in README: index-only needs the visibility map). Gate: `must_have=["Index Only Scan"]`, `ratio=8`. The `test_lesson.py` runs `VACUUM` (via autocommit connection) before measuring, OR instructs the learner to include it — spec: learner puts `VACUUM orders;` is not allowed in a transaction, so the test issues `conn.autocommit=True` and runs VACUUM after applying indexes, documented in README. Commit.
- [ ] **`06_order_by_index`** — Teaches using an index to remove a Sort. Problem: `SELECT id FROM orders WHERE customer_id = 4242 ORDER BY created_at DESC LIMIT 10;`. Reference index: `CREATE INDEX idx_orders_cust_created ON orders(customer_id, created_at DESC);`. Gate: `must_not_have=["Sort"]`, `uses_index="idx_orders_cust_created"`, `ordered=True`, `ratio=5`. Commit.

### Task 16: Part 3 — Planner & joins (3 lessons)

- [ ] **`07_statistics`** — Teaches `ANALYZE`/statistics/selectivity. This lesson is NOT ratio-shaped. Setup: README has the learner run a query whose estimate is badly wrong because stats are stale (the test creates the scenario by inserting/updating rows then NOT analyzing, or by dropping stats). The learner's `solution.sql` is `ANALYZE orders;` (plus optionally `CREATE STATISTICS` for correlated columns `status,customer_id`). Gate (custom, in `test_lesson.py`): capture `EXPLAIN` (no ANALYZE) estimated rows for a probe query before and after the learner's `solution.sql`; assert that after running it, `abs(estimated-actual)/actual` for the probe drops below 0.25. The probe query and actual count are defined in the test. README explains `pg_statistic`, `n_distinct`, histograms, `CREATE STATISTICS`. Commit.
- [ ] **`08_join_algorithms`** — Teaches nested-loop vs hash vs merge. Problem: a join of `orders`⋈`order_items` aggregated. Part A: with no indexes and default `work_mem`, observe a Hash Join (assert `must_have=["Hash Join"]`). Part B: the learner adds indexes on the join keys (`order_items(order_id)`) and the gate requires the plan to switch to a Nested Loop driven by an Index Scan for a *selective* variant (`WHERE o.customer_id = 4242`): `must_have=["Nested Loop","Index Scan"]`, `must_not_have=["Seq Scan"]`, `ratio=8`. README explains when the planner prefers each algorithm and `work_mem`. Commit.
- [ ] **`09_bitmap_scans`** — Teaches bitmap index scans combining two indexes. Problem: `SELECT id FROM orders WHERE status='pending' AND created_at >= now() - interval '30 days';` with two separate single-column indexes (`orders(status)` and `orders(created_at)`) so the planner uses `BitmapAnd`. Reference `indexes.sql` creates both. Gate: `must_have=["Bitmap Heap Scan","BitmapAnd"]`, `ratio=5`. README explains bitmap scans and why two single-column indexes can be combined. Commit.

### Task 17: Part 4 — The index zoo (5 lessons)

- [ ] **`10_partial_index`** — Problem: `SELECT id FROM orders WHERE status = 'pending';` (rare status). Reference index: `CREATE INDEX idx_orders_pending ON orders(id) WHERE status='pending';`. Gate: `uses_index="idx_orders_pending"`, `must_not_have=["Seq Scan"]`, `ratio=10`. README contrasts partial vs full index size. Commit.
- [ ] **`11_expression_index`** — Problem: `SELECT id FROM customers WHERE lower(email) = 'user4242@example.com';`. Reference index: `CREATE INDEX idx_customers_lower_email ON customers(lower(email));`. Gate: `uses_index="idx_customers_lower_email"`, `must_not_have=["Seq Scan"]`, `ratio=8`. Commit.
- [ ] **`12_gin_fulltext`** — Problem: find reviews whose body matches a phrase. Reference: `CREATE INDEX idx_reviews_body_fts ON reviews USING gin (to_tsvector('english', body));` and `solution.sql` uses `WHERE to_tsvector('english', body) @@ plainto_tsquery('english', 'fast delivery')`. Compare to the naive `body ILIKE '%fast delivery%'` baseline (which is `expected.sql` for correctness — note: ensure both return the same row set, or define `expected.sql` as the tsquery form and compare counts). Gate: `must_have=["Bitmap Index Scan"]` (GIN scans show as bitmap), `ratio=10`. README maps this to Postgres full-text + GIN. Commit.
- [ ] **`13_gin_jsonb`** — Problem: `SELECT id FROM products WHERE attributes @> '{"color":"red"}';`. Reference index: `CREATE INDEX idx_products_attrs ON products USING gin (attributes);`. Gate: `uses_index="idx_products_attrs"` (or `must_have=["Bitmap Index Scan"]`), `ratio=8`. README explains GIN for JSONB containment and `jsonb_path_ops`. Commit.
- [ ] **`14_gist_brin`** — Two-part lesson on the big `events` table. BRIN part: `SELECT count(*) FROM events WHERE ts >= '<a date>' AND ts < '<a date+1day>';`. Reference index: `CREATE INDEX idx_events_ts_brin ON events USING brin (ts);`. Gate: `must_have=["Bitmap Index Scan"]`, `uses_index="idx_events_ts_brin"`, `ratio=5`, and README notes the BRIN index is tiny vs a B-tree. (GiST is covered as README reading with an illustrative range/`tstzrange` example, no separate gate, since the schema has no native range column.) Commit.

### Task 18: Part 5 — Operational performance (3 lessons)

- [ ] **`15_mvcc_vacuum_bloat`** — NOT ratio-shaped. `test_lesson.py` (custom): on the clone, `UPDATE events SET payload = payload WHERE id <= 500000;` to create dead tuples, measure table size / dead tuple count via `pg_stat_user_tables` (`n_dead_tup`) and `pg_relation_size`. Learner's `solution.sql` is `VACUUM events;` (autocommit). Gate: assert `n_dead_tup` after the learner's solution is at least 90% lower than before. README explains MVCC, dead tuples, autovacuum, `fillfactor`, HOT updates. Commit.
- [ ] **`16_partitioning`** — NOT ratio-shaped (DDL-heavy). Learner creates a partitioned copy of events by month and queries it; gate asserts **partition pruning**: `EXPLAIN` for a single-month query shows only one partition scanned (assert the number of `Seq Scan`/`Index Scan` leaf nodes over partition tables == 1, via counting nodes whose `Relation Name` matches the partition prefix). README explains declarative partitioning + pruning. Provide the full partitioned-table DDL in the reference answer. Commit.
- [ ] **`17_materialized_views`** — NOT ratio-shaped in the index sense, but speed-comparative. Problem: an expensive per-category revenue aggregate (reuse lesson 01's query). Learner creates `CREATE MATERIALIZED VIEW mv_cat_revenue AS <agg>;` plus an index on it, then `solution.sql` selects from the matview. Gate: `assert_rows_equal` to the live aggregate, and `assert_faster_than_baseline(measured, baseline=<live agg time>, ratio=20)`. README explains matviews + `REFRESH MATERIALIZED VIEW [CONCURRENTLY]`. Commit.

### Task 19: Part 6 — Capstone

- [ ] **`18_capstone`** — A deliberately slow multi-table report: "top 10 products by revenue among `paid` orders in the last 90 days, with review counts." `expected.sql` is the correct (slow, un-indexed) query. The learner must add whatever indexes are needed and may rewrite the query, hitting `must_not_have=["Seq Scan"]` on the large tables, and `ratio=15`. README frames it as the final exam and lists which techniques are relevant. Author the reference solution (indexes + tuned query) to confirm the target is achievable. Commit.

---

## Self-Review Notes (completed by plan author)

- **Spec coverage:** Every curriculum lesson (00–18) maps to Tasks 12, 13, 15–19. Harness components (config, db, seed, plan, timing, grader, lesson, fixtures) map to Tasks 3–11. Docker/provisioning → Task 2. Calibration → Task 8 + the test template. Docs → Task 14. No spec section is unaddressed.
- **Index-type coverage check:** B-tree single (02), composite (03), left-prefix (04), covering/INCLUDE (05), order-by (06), partial (10), expression (11), GIN full-text (12), GIN jsonb (13), BRIN (14), GiST (14 README). All present.
- **Non-ratio lessons** (07, 15, 16) explicitly override the speed template with named custom assertions, per the authoring procedure note — not placeholders.
- **Type consistency:** `Lesson(__file__)`, `Plan(explain_json)`, `explain(conn, sql)`, `measure_execution_ms`, `cached_baseline`, `assert_rows_equal/assert_plan/assert_faster_than_baseline` are used with identical signatures in the test template and their defining tasks.
- **Known authoring risk flagged for executor:** lessons 05/15/16/17 require `VACUUM`/`CREATE DATABASE`-style statements that cannot run inside a transaction block — run them on an autocommit connection. The `lesson_db` fixture yields a normal connection; these tests must set `conn.autocommit = True` before such statements. This is called out in each affected lesson's task.
