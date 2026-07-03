"""Show a lesson's query plan without running its test/gate.

Clones the seeded template into a throwaway database, applies the
lesson's ``indexes.sql``, then runs its ``solution.sql`` through
``EXPLAIN (ANALYZE, BUFFERS)`` and prints the plan. The clone is dropped
afterward, exactly like the test harness does.

Usage:
    uv run python -m dojo.plan_lesson lessons/04_left_prefix
"""
import re
import sys
from pathlib import Path

from dojo.lesson import Lesson
from dojo.db import connect, clone_template, drop_database


def _clone_name(slug: str) -> str:
    return "dojo_plan_" + re.sub(r"[^a-z0-9_]", "_", slug.lower())


def _resolve_dir(lesson_arg: str) -> Path | None:
    """Accept ``lessons/04_left_prefix``, a bare slug, or a file in the dir."""
    path = Path(lesson_arg)
    if path.is_file():
        return path.parent
    if path.is_dir():
        return path
    fallback = Path("lessons") / lesson_arg
    return fallback if fallback.is_dir() else None


def run(lesson_arg: str) -> int:
    lesson_dir = _resolve_dir(lesson_arg)
    if lesson_dir is None:
        print(f"Lesson not found: {lesson_arg}", file=sys.stderr)
        return 1

    lesson = Lesson(str(lesson_dir / "test_lesson.py"))
    solution = lesson.solution_sql.strip()
    if not solution:
        print(f"No solution.sql to plan in {lesson_dir}", file=sys.stderr)
        return 1

    clone = _clone_name(lesson.slug)
    clone_template(clone)
    try:
        conn = connect(clone)
        try:
            lesson.apply_indexes(conn)
            with conn.cursor() as cur:
                try:
                    cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + solution)
                    rows = cur.fetchall()
                except Exception as exc:  # noqa: BLE001 - surface any planner error
                    conn.rollback()
                    print(f"Could not EXPLAIN this solution.sql:\n  {exc}",
                          file=sys.stderr)
                    print("(EXPLAIN can't profile utility statements like "
                          "ANALYZE or VACUUM — those lessons have no query plan "
                          "to show.)", file=sys.stderr)
                    return 1

            indexes = lesson.indexes_sql.strip()
            print(f"# lesson: {lesson.slug}")
            print("# indexes.sql:")
            print(_indent(indexes) if indexes else "    (none)")
            print("# solution.sql:")
            print(_indent(solution))
            print("# EXPLAIN (ANALYZE, BUFFERS):")
            for (line,) in rows:
                print(line)
        finally:
            conn.close()
    finally:
        drop_database(clone)
    return 0


def _indent(text: str) -> str:
    return "\n".join("    " + line for line in text.splitlines())


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m dojo.plan_lesson <lessons/NN_name>",
              file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(sys.argv[1]))


if __name__ == "__main__":
    main()
