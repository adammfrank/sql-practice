"""Spin up a persistent, explorable clone of the seeded template for a lesson.

Creates a database named ``dojo_lab_<slug>``, applies the lesson's
``indexes.sql`` and (if present) ``setup.sql`` — the extra rows / skewed
state a lesson's test would otherwise create only transiently inside a
throwaway clone — then drops you into a ``psql`` session connected to it.

The clone persists after you quit ``psql`` so you can reconnect; running
``make lab`` again re-creates it fresh. ``make lab-clean`` drops every
``dojo_lab_*`` database.

Usage:
    uv run python -m dojo.lab lessons/07_statistics
    uv run python -m dojo.lab --clean
"""
import re
import subprocess
import sys
from pathlib import Path

from psycopg import sql

from dojo.lesson import Lesson
from dojo.db import connect, clone_template
from dojo.config import load_config


def _clone_name(slug: str) -> str:
    return "dojo_lab_" + re.sub(r"[^a-z0-9_]", "_", slug.lower())


def _resolve_dir(arg: str) -> Path | None:
    path = Path(arg)
    if path.is_file():
        return path.parent
    if path.is_dir():
        return path
    fallback = Path("lessons") / arg
    return fallback if fallback.is_dir() else None


def _apply(conn, statements: str) -> bool:
    statements = statements.strip()
    if not statements:
        return False
    with conn.cursor() as cur:
        cur.execute(statements)
    conn.commit()
    return True


def clean() -> int:
    cfg = load_config()
    with connect(cfg.maintenance_db, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("SELECT datname FROM pg_database WHERE datname LIKE 'dojo_lab_%'")
        names = [row[0] for row in cur.fetchall()]
        for name in names:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(name)))
    print(f"Dropped {len(names)} lab database(s): {', '.join(names) or '(none)'}")
    return 0


def run(arg: str) -> int:
    lesson_dir = _resolve_dir(arg)
    if lesson_dir is None:
        print(f"Lesson not found: {arg}", file=sys.stderr)
        return 1

    lesson = Lesson(str(lesson_dir / "test_lesson.py"))
    clone = _clone_name(lesson.slug)
    cfg = load_config()

    clone_template(clone)
    conn = connect(clone)
    try:
        applied = []
        if _apply(conn, lesson.indexes_sql):
            applied.append("indexes.sql")
        if _apply(conn, lesson.setup_sql):
            applied.append("setup.sql")
    finally:
        conn.close()

    print(f"\nLab ready: database '{clone}' — a fresh clone of the template"
          + (f", with {' + '.join(applied)} applied." if applied
             else " (nothing applied beyond the seed)."))
    print("Drop it when you're done with:  make lab-clean\n")

    psql_cmd = ["docker", "compose", "exec", "db", "psql", "-U", cfg.user, "-d", clone]
    if sys.stdin.isatty():
        print("Opening psql (\\q to quit)...\n")
        return subprocess.call(psql_cmd)
    print("Connect with:\n  " + " ".join(psql_cmd))
    return 0


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m dojo.lab <lessons/NN_name> | --clean", file=sys.stderr)
        raise SystemExit(2)
    if sys.argv[1] == "--clean":
        raise SystemExit(clean())
    raise SystemExit(run(sys.argv[1]))


if __name__ == "__main__":
    main()
