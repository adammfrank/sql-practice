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
    grader.assert_plan(p, must_not_have=["Seq Scan"], uses_index="idx_orders_pending")
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    # Brief suggests ratio=10, calling 'pending' a "rare" status. It isn't:
    # STATUSES in dojo/seed.py is ["pending","paid","paid","paid","shipped",
    # "cancelled"], so 'pending' is ~1/6 of orders (measured: 83,531 of
    # 500,000, ~16.7%) -- the same low-selectivity ceiling that forced
    # lessons 04 and 09 to lower their ratios. Measured across repeated
    # clone-and-time trials on the seeded template, the partial index ran
    # 2.4x-4.3x faster than the seq-scan baseline (min observed 2.4x under
    # concurrent load). ratio=2 is set below that measured floor so the
    # gate is real without being flaky under load. The plan assertion
    # above (no Seq Scan, must use idx_orders_pending) is the primary
    # teaching gate for this lesson; the ratio is a secondary floor.
    grader.assert_faster_than_baseline(measured, baseline, ratio=2, floor_ms=2.0)
