from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    maintenance_db: str
    template_db: str

def load_config() -> DbConfig:
    return DbConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "dojo"),
        password=os.getenv("POSTGRES_PASSWORD", "dojo"),
        maintenance_db=os.getenv("POSTGRES_MAINTENANCE_DB", "postgres"),
        template_db=os.getenv("DOJO_TEMPLATE_DB", "dojo_template"),
    )

def conninfo(cfg: DbConfig, dbname: str) -> str:
    return (
        f"host={cfg.host} port={cfg.port} user={cfg.user} "
        f"password={cfg.password} dbname={dbname}"
    )
