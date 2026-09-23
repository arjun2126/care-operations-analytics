import logging
import os
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "care_analytics")
    database_user: str = os.getenv("DATABASE_USER", "care_analyst")
    database_password: str = os.getenv("DATABASE_PASSWORD", "care_analyst_local")
    database_schema: str = os.getenv("DATABASE_SCHEMA", "public")
    data_dir: str = os.getenv("DATA_DIR", "data")
    raw_dir: str = os.getenv("RAW_DIR", "data/raw")
    processed_dir: str = os.getenv("PROCESSED_DIR", "data/processed")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/pipeline.log")
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))
    num_clients: int = int(os.getenv("NUM_CLIENTS", "300"))
    num_workers: int = int(os.getenv("NUM_WORKERS", "110"))
    num_funders: int = int(os.getenv("NUM_FUNDERS", "6"))
    num_visits: int = int(os.getenv("NUM_VISITS", "7500"))
    exception_count: int = int(os.getenv("EXCEPTION_COUNT", "300"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}",
    )


config = Config()
