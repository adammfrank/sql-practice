# tests/test_plan.py
from dojo.plan import Plan

SAMPLE = [{
    "Plan": {
        "Node Type": "Aggregate",
        "Plans": [
            {"Node Type": "Index Scan", "Index Name": "idx_orders_customer",
             "Plans": [{"Node Type": "Seq Scan"}]}
        ]
    },
    "Execution Time": 12.5,
    "Planning Time": 0.3,
}]

def test_node_types_preorder():
    p = Plan(SAMPLE)
    assert p.node_types() == ["Aggregate", "Index Scan", "Seq Scan"]

def test_has_node():
    p = Plan(SAMPLE)
    assert p.has_node("Index Scan")
    assert not p.has_node("Hash Join")

def test_uses_index():
    p = Plan(SAMPLE)
    assert p.uses_index("idx_orders_customer")
    assert not p.uses_index("nope")

def test_times():
    p = Plan(SAMPLE)
    assert p.execution_time_ms == 12.5
    assert p.planning_time_ms == 0.3
