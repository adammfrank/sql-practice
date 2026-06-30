from dojo.lesson import Lesson

def test_slug_and_read(tmp_path):
    d = tmp_path / "02_first_index"
    d.mkdir()
    (d / "solution.sql").write_text("SELECT 1;")
    (d / "test_lesson.py").write_text("")
    lesson = Lesson(str(d / "test_lesson.py"))
    assert lesson.slug == "02_first_index"
    assert lesson.solution_sql.strip() == "SELECT 1;"
    assert lesson.indexes_sql == ""        # missing file -> empty
    assert lesson.expected_sql == ""
