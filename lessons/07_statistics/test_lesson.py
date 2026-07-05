from dojo.lesson import Lesson
from dojo import plan as planmod

lesson = Lesson(__file__)

PROBE = "SELECT id FROM orders WHERE status = 'pending'"

# Threshold the lesson is graded against: after ANALYZE, the planner's
# row-count estimate must be within this fraction of the true count.
ERROR_THRESHOLD = 0.25


def _skew_stats(conn):
    """Apply the lesson's setup.sql: a burst of new 'pending' orders inserted
    without ANALYZE-ing, so the planner's cached statistics (from the
    template's seed-time ANALYZE) no longer reflect the table's real status
    distribution. This is the same setup `make lab` applies, so the lab and
    the gate exercise an identical scenario."""
    with conn.cursor() as cur:
        cur.execute(lesson.setup_sql)
    conn.commit()


def _estimate_rows(conn) -> float:
    p = planmod.explain(conn, PROBE, analyze=False)
    return float(p.root["Plan Rows"])


def _actual_rows(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM ({PROBE}) t")
        return cur.fetchone()[0]


def test_solution(lesson_db):
    conn = lesson_db

    _skew_stats(conn)

    actual = _actual_rows(conn)
    stale_estimate = _estimate_rows(conn)
    stale_error = abs(stale_estimate - actual) / actual
    assert stale_error >= ERROR_THRESHOLD, (
        "Test setup didn't actually create stale statistics — the estimate "
        f"({stale_estimate:.0f}) is already within {ERROR_THRESHOLD:.0%} of "
        f"the actual count ({actual}). This is a test bug, not a solution bug."
    )

    # The learner's fix: run solution.sql directly. It's a DDL/maintenance
    # statement (ANALYZE), not a SELECT, so we execute it rather than using
    # lesson.fetch (which assumes a result set).
    stmt = lesson.solution_sql.strip()
    with conn.cursor() as cur:
        cur.execute(stmt)
    conn.commit()

    fresh_estimate = _estimate_rows(conn)
    fresh_error = abs(fresh_estimate - actual) / actual
    assert fresh_error < ERROR_THRESHOLD, (
        f"Planner estimate ({fresh_estimate:.0f}) is still more than "
        f"{ERROR_THRESHOLD:.0%} off the actual count ({actual}) after "
        f"running your solution.sql. Did you ANALYZE the right table?"
    )
