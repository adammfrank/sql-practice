import pytest
from dojo import grader
from dojo.plan import Plan

def mk(node_types, index=None):
    root = {"Node Type": node_types[0]}
    if index and node_types[0].endswith("Scan"):
        root["Index Name"] = index
    cur = root
    for nt in node_types[1:]:
        child = {"Node Type": nt}
        if index and nt.endswith("Scan"):
            child["Index Name"] = index
        cur["Plans"] = [child]; cur = child
    return Plan([{"Plan": root, "Execution Time": 1.0, "Planning Time": 0.1}])

def test_rows_equal_unordered():
    grader.assert_rows_equal([(1,),(2,)], [(2,),(1,)])

def test_rows_equal_mismatch():
    with pytest.raises(AssertionError):
        grader.assert_rows_equal([(1,)], [(2,)])

def test_assert_plan_must_have_ok():
    grader.assert_plan(mk(["Aggregate","Index Scan"]), must_have=["Index Scan"])

def test_assert_plan_must_not_have_fails():
    with pytest.raises(AssertionError):
        grader.assert_plan(mk(["Seq Scan"]), must_not_have=["Seq Scan"])

def test_assert_uses_index():
    grader.assert_plan(mk(["Index Scan"], index="idx_x"), uses_index="idx_x")

def test_faster_ok():
    grader.assert_faster_than_baseline(10.0, 100.0, ratio=8)

def test_faster_fails():
    with pytest.raises(AssertionError):
        grader.assert_faster_than_baseline(50.0, 100.0, ratio=8)

def test_faster_floor_skips():
    grader.assert_faster_than_baseline(1.5, 1.0, ratio=8)  # baseline under floor -> pass
