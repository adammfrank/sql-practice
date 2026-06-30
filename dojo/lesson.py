from pathlib import Path

class Lesson:
    def __init__(self, test_file_path: str):
        self.dir = Path(test_file_path).parent
        self.slug = self.dir.name

    def read(self, name: str) -> str:
        f = self.dir / name
        return f.read_text() if f.exists() else ""

    @property
    def solution_sql(self) -> str:
        return self.read("solution.sql")

    @property
    def indexes_sql(self) -> str:
        return self.read("indexes.sql")

    @property
    def expected_sql(self) -> str:
        return self.read("expected.sql")

    def apply_indexes(self, conn) -> None:
        ddl = self.indexes_sql.strip()
        if ddl:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def fetch(self, conn, query_sql: str):
        with conn.cursor() as cur:
            cur.execute(query_sql)
            return cur.fetchall()
