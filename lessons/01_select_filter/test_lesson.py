from dojo.lesson import Lesson
from dojo import grader

lesson = Lesson(__file__)

def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)
    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=False)
