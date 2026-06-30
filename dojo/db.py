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
