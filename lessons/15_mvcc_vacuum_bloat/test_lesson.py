import time
from dojo.lesson import Lesson
from dojo.db import connect

lesson = Lesson(__file__)

# Threshold the lesson is graded against: VACUUM must clear out at least
# this fraction of the dead tuples we deliberately created.
REDUCTION_THRESHOLD = 0.90

# Hard self-check: the pre-solution setup must leave at least this many
# dead tuples, or the "before" measurement isn't testing anything real.
MIN_DEAD_BEFORE = 400_000


def _clear_and_read_dead_tup(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_stat_clear_snapshot()")
        cur.execute(
            "SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = 'events'"
        )
        row = cur.fetchone()
        return row[0] if row else 0


def _poll_dead_tup(conn, predicate, timeout_s: float = 3.0, interval_s: float = 0.1) -> int:
    """The stats collector can lag behind a just-committed UPDATE/VACUUM.
    Re-clear the snapshot and re-read in a bounded loop until `predicate`
    is satisfied (or we run out of time, in which case we return whatever
    we last saw and let the caller's assertion report the real failure)."""
    deadline = time.monotonic() + timeout_s
    value = _clear_and_read_dead_tup(conn)
    while not predicate(value) and time.monotonic() < deadline:
        time.sleep(interval_s)
        value = _clear_and_read_dead_tup(conn)
    return value


def test_solution(lesson_db):
    conn = lesson_db

    # Disable autovacuum on this clone's events table FIRST, so autovacuum
    # can't sneak in and clean up our dead tuples mid-test and wreck the
    # before/after measurement.
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE events SET (autovacuum_enabled = false)")
    conn.commit()

    # Create dead tuples: every one of these 500,000 rows gets a new row
    # version (MVCC), and the old version becomes a dead tuple once the
    # UPDATE commits.
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE events SET payload = payload || '{\"v\":1}'::jsonb "
            "WHERE id <= 500000"
        )
    conn.commit()

    before = _poll_dead_tup(conn, lambda v: v > 0)
    assert before > MIN_DEAD_BEFORE, (
        "Test setup didn't actually create enough dead tuples — "
        f"n_dead_tup is only {before} (expected > {MIN_DEAD_BEFORE}). "
        "This is a test bug, not a solution bug."
    )

    # The learner's fix: run solution.sql directly. VACUUM cannot run
    # inside a transaction block, so we execute it on a separate
    # autocommit connection targeting the SAME per-test clone.
    stmt = lesson.solution_sql.strip()
    with connect(conn.info.dbname, autocommit=True) as ac:
        with ac.cursor() as cur:
            cur.execute(stmt)

    after = _clear_and_read_dead_tup(conn)
    assert after <= before * (1 - REDUCTION_THRESHOLD), (
        f"n_dead_tup only dropped from {before} to {after} after running "
        f"your solution.sql — need at least a {REDUCTION_THRESHOLD:.0%} "
        "reduction. Did you VACUUM the right table?"
    )
