import json
from pathlib import Path
from dojo.plan import explain

BASELINE_PATH = Path(__file__).parent.parent / "data" / "baseline.json"

def measure_execution_ms(conn, query, params=None, repeats: int = 5, warmup: int = 1) -> float:
    for _ in range(warmup):
        explain(conn, query, params, analyze=True)
    times = [explain(conn, query, params, analyze=True).execution_time_ms
             for _ in range(repeats)]
    return min(times)

def load_baseline() -> dict:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text())
    return {}

def save_baseline(d: dict) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(d, indent=2))

def cached_baseline(conn, key: str, query, params=None) -> float:
    data = load_baseline()
    if key in data:
        return data[key]
    ms = measure_execution_ms(conn, query, params)
    data[key] = ms
    save_baseline(data)
    return ms
