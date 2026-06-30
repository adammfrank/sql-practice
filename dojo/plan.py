# dojo/plan.py
class Plan:
    def __init__(self, explain_json: list):
        self._top = explain_json[0]
        self.root = self._top["Plan"]

    def nodes(self) -> list[dict]:
        out = []
        def walk(n):
            out.append(n)
            for child in n.get("Plans", []):
                walk(child)
        walk(self.root)
        return out

    def node_types(self) -> list[str]:
        return [n["Node Type"] for n in self.nodes()]

    def has_node(self, node_type: str) -> bool:
        return node_type in self.node_types()

    def uses_index(self, index_name: str) -> bool:
        return any(n.get("Index Name") == index_name for n in self.nodes())

    @property
    def execution_time_ms(self) -> float:
        return float(self._top.get("Execution Time", 0.0))

    @property
    def planning_time_ms(self) -> float:
        return float(self._top.get("Planning Time", 0.0))

    def render(self) -> str:
        return " -> ".join(self.node_types())


def explain(conn, query: str, params=None, analyze: bool = True) -> Plan:
    opts = "ANALYZE, BUFFERS, FORMAT JSON" if analyze else "FORMAT JSON"
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN ({opts}) " + query, params)
        data = cur.fetchone()[0]
    return Plan(data)
