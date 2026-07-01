# dojo/seed.py
import datetime as dt
import json
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
    t0 = time.time()
    n = 0
    with cur.copy(stmt) as cp:
        for r in rows:
            cp.write_row(r)
            n += 1
    print(f"  {table}: {n} rows in {time.time() - t0:.1f}s")

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
    return dt.datetime.fromtimestamp(epoch_seconds, tz=dt.timezone.utc).isoformat()

def _json(obj) -> str:
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
