from dojo.plan import Plan

def assert_rows_equal(actual, expected, ordered: bool = False) -> None:
    a = list(actual) if ordered else sorted(map(tuple, actual))
    e = list(expected) if ordered else sorted(map(tuple, expected))
    assert a == e, (
        f"Result rows differ.\n  expected {len(e)} rows, got {len(a)}.\n"
        f"  first expected: {e[:3]}\n  first actual:   {a[:3]}"
    )

def assert_plan(plan: Plan, must_have=None, must_not_have=None, uses_index=None) -> None:
    for nt in (must_have or []):
        assert plan.has_node(nt), (
            f"Expected plan to contain a '{nt}' node.\n  plan: {plan.render()}"
        )
    for nt in (must_not_have or []):
        assert not plan.has_node(nt), (
            f"Plan should NOT contain a '{nt}' node (you're still doing that).\n"
            f"  plan: {plan.render()}"
        )
    if uses_index is not None:
        assert plan.uses_index(uses_index), (
            f"Expected the plan to use index '{uses_index}'.\n  plan: {plan.render()}"
        )

def assert_faster_than_baseline(measured_ms, baseline_ms, ratio, floor_ms=2.0) -> None:
    if baseline_ms < floor_ms:
        return
    target = baseline_ms / ratio
    achieved = baseline_ms / measured_ms if measured_ms else float("inf")
    assert measured_ms <= target, (
        f"Too slow. baseline={baseline_ms:.2f}ms, yours={measured_ms:.2f}ms, "
        f"need <= {target:.2f}ms (>= {ratio}x faster). You achieved {achieved:.1f}x."
    )
