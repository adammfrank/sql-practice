# tests/test_smoke.py
def test_clone_has_seeded_data(lesson_db):
    with lesson_db.cursor() as cur:
        cur.execute("SELECT count(*) FROM customers")
        assert cur.fetchone()[0] == 50_000
        cur.execute("SELECT count(*) FROM events")
        assert cur.fetchone()[0] == 3_000_000
