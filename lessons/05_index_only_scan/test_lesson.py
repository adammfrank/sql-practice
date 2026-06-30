from dojo.lesson import Lesson
from dojo import grader, timing, plan as planmod
from dojo.db import connect

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)
    baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)
    lesson.apply_indexes(conn)

    # An Index Only Scan requires the visibility map to be up to date,
    # which only happens after VACUUM. VACUUM cannot run inside a
    # transaction block, so we do it on a separate autocommit connection.
    vc = connect(conn.info.dbname, autocommit=True)
    vc.execute("VACUUM orders")
    vc.close()

    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=False)
    p = planmod.explain(conn, lesson.solution_sql)
    grader.assert_plan(p, must_have=["Index Only Scan"], must_not_have=["Seq Scan"])
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    grader.assert_faster_than_baseline(measured, baseline, ratio=8, floor_ms=2.0)
