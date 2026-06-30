from dojo.lesson import Lesson
from dojo import grader, plan as planmod

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)
    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected)
    p = planmod.explain(conn, lesson.solution_sql)
    grader.assert_plan(p, must_have=["Seq Scan"])
