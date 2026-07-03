from dojo.lesson import Lesson
from dojo import grader, timing, plan as planmod

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)
    baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)
    lesson.apply_indexes(conn)
    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=True)
    p = planmod.explain(conn, lesson.solution_sql)
    grader.assert_plan(p, must_not_have=["Sort", "Seq Scan"])
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    grader.assert_faster_than_baseline(measured, baseline, ratio=5, floor_ms=2.0)
