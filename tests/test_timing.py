import json
from dojo import timing

def test_measure_uses_min(monkeypatch):
    times = iter([50.0, 9.0, 30.0, 12.0, 7.0, 40.0])  # warmup + 5
    class FakePlan:
        def __init__(self, t): self.execution_time_ms = t
    def fake_explain(conn, q, params=None, analyze=True):
        return FakePlan(next(times))
    monkeypatch.setattr(timing, "explain", fake_explain)
    assert timing.measure_execution_ms(None, "SELECT 1") == 7.0

def test_baseline_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "baseline.json"
    monkeypatch.setattr(timing, "BASELINE_PATH", f)
    timing.save_baseline({"02_first_index": 123.4})
    assert timing.load_baseline()["02_first_index"] == 123.4

def test_cached_baseline_caches(tmp_path, monkeypatch):
    f = tmp_path / "baseline.json"
    monkeypatch.setattr(timing, "BASELINE_PATH", f)
    calls = []
    monkeypatch.setattr(timing, "measure_execution_ms",
                        lambda *a, **k: calls.append(1) or 55.0)
    a = timing.cached_baseline(None, "k", "SELECT 1")
    b = timing.cached_baseline(None, "k", "SELECT 1")
    assert a == b == 55.0
    assert len(calls) == 1  # measured once, then cached
