from dojo.lesson import Lesson
from dojo import grader, timing

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)

    # Baseline: the live aggregate's execution time, measured BEFORE the
    # materialized view exists (so it's really scanning ~1M order_items
    # and joining, not benefiting from anything your indexes.sql creates).
    baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)

    # Creates mv_cat_revenue (+ an index on it).
    lesson.apply_indexes(conn)

    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=False)

    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    grader.assert_faster_than_baseline(measured, baseline, ratio=20, floor_ms=2.0)
