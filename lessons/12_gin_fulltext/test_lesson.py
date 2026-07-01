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
    grader.assert_plan(p, must_have=["Bitmap Index Scan"])
    measured = timing.measure_execution_ms(conn, lesson.solution_sql)
    # reviews.body is Faker lorem-ipsum text (dojo/seed.py: fake.paragraph),
    # not real product-review prose -- the brief's phrase "fast delivery"
    # matches zero rows in this corpus. 'dog' was chosen by sampling
    # document frequencies with ts_stat() and confirming on the full table:
    # it matches 25,520 of 1,000,000 rows (~2.55%), a realistic "moderately
    # common search term" frequency. Measured on the seeded template: seq
    # scan baseline ~6.6-8.8s (computing to_tsvector per row over 1M rows),
    # GIN bitmap index scan ~40-48ms -- around 150-200x faster. The brief's
    # ratio=10 is comfortably achievable.
    grader.assert_faster_than_baseline(measured, baseline, ratio=10, floor_ms=2.0)
