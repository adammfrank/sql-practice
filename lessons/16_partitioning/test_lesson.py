from dojo.lesson import Lesson
from dojo import grader
from dojo import plan as planmod

lesson = Lesson(__file__)

# Partitions are named with this prefix (see indexes.sql / README.md).
# Used to identify partition leaf-scan nodes in the EXPLAIN plan.
PARTITION_PREFIX = "events_p_"

SCAN_NODE_TYPES = {"Seq Scan", "Index Scan", "Index Only Scan", "Bitmap Heap Scan"}


def _partition_leaf_scan_count(p: planmod.Plan) -> int:
    count = 0
    for n in p.nodes():
        if n.get("Node Type") in SCAN_NODE_TYPES:
            rel = n.get("Relation Name") or ""
            if rel.startswith(PARTITION_PREFIX):
                count += 1
    return count


def test_solution(lesson_db):
    conn = lesson_db
    expected = lesson.fetch(conn, lesson.expected_sql)

    # Builds the partitioned copy of `events` (DDL + ~3M-row backfill INSERT).
    lesson.apply_indexes(conn)

    actual = lesson.fetch(conn, lesson.solution_sql)
    grader.assert_rows_equal(actual, expected, ordered=False)

    p = planmod.explain(conn, lesson.solution_sql)
    pruned_count = _partition_leaf_scan_count(p)
    assert pruned_count == 1, (
        "Expected exactly one partition to be scanned (partition pruning), "
        f"but found {pruned_count} partition leaf scan(s) in the plan.\n"
        f"  plan: {p.render()}\n"
        f"  nodes: {[(n.get('Node Type'), n.get('Relation Name')) for n in p.nodes()]}"
    )
