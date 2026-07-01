from dojo.lesson import Lesson
from dojo import grader, timing, plan as planmod

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)
    baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)
    lesson.apply_indexes(conn)
    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=False)
    p = planmod.explain(conn, lesson.solution_sql)
    grader.assert_plan(p, must_not_have=["Seq Scan"], uses_index="idx_customers_lower_email")
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    # customers.email is `user{id}@example.com` for id 1..50000 (dojo/seed.py),
    # so lower(email) = 'user4242@example.com' matches exactly one row out of
    # 50,000 -- highly selective. Measured on the seeded template: baseline
    # (seq scan) ~10-11ms, indexed (bitmap index scan on the expression
    # index) ~0.02-0.06ms -- several hundred-x faster. The brief's ratio=8
    # is comfortably achievable here.
    grader.assert_faster_than_baseline(measured, baseline, ratio=8, floor_ms=2.0)
