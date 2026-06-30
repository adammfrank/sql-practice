from dojo.config import DbConfig, load_config, conninfo

def test_load_config_defaults(monkeypatch):
    for k in ["POSTGRES_HOST","POSTGRES_PORT","POSTGRES_USER","POSTGRES_PASSWORD",
              "POSTGRES_MAINTENANCE_DB","DOJO_TEMPLATE_DB"]:
        monkeypatch.delenv(k, raising=False)
    cfg = load_config()
    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.user == "dojo"
    assert cfg.maintenance_db == "postgres"
    assert cfg.template_db == "dojo_template"

def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("POSTGRES_PORT", "6000")
    monkeypatch.setenv("POSTGRES_USER", "alice")
    cfg = load_config()
    assert cfg.port == 6000
    assert cfg.user == "alice"

def test_conninfo_contains_dbname():
    cfg = DbConfig("localhost", 5432, "dojo", "dojo", "postgres", "dojo_template")
    s = conninfo(cfg, "dojo_test_x")
    assert "dbname=dojo_test_x" in s
    assert "host=localhost" in s
    assert "port=5432" in s
