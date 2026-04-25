from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import dlt
import pandas as pd
import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = PROJECT_ROOT / "instagram_media.csv"

PIPELINE_NAME = "social_raw_ingestion"
DATASET_NAME = "raw"
TABLE_NAME = "instagram_media"


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def build_postgres_url() -> str:
    host = get_env("POSTGRES_HOST", "localhost")
    port = get_env("POSTGRES_PORT", "5432")
    db = get_env("POSTGRES_DB", "retize_social")
    user = quote_plus(get_env("POSTGRES_USER", "retize_user"))
    password = quote_plus(get_env("POSTGRES_PASSWORD", "retize_password"))

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def load_csv_records(csv_file: Path) -> list[dict[str, str]]:
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    # Keep raw values as strings; type casting is handled later in dbt staging models.
    df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
    return df.to_dict(orient="records")


def validate_loaded_count(postgres_url: str, expected_count: int) -> None:
    with psycopg2.connect(postgres_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"select count(*) from {DATASET_NAME}.{TABLE_NAME}")
            loaded_count = cursor.fetchone()[0]

    if loaded_count != expected_count:
        raise RuntimeError(
            f"Row count mismatch for {DATASET_NAME}.{TABLE_NAME}: "
            f"expected {expected_count}, got {loaded_count}"
        )

    print(f"Validated {DATASET_NAME}.{TABLE_NAME}: {loaded_count} rows loaded.")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    postgres_url = build_postgres_url()
    records = load_csv_records(CSV_FILE)

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=dlt.destinations.postgres(postgres_url),
        dataset_name=DATASET_NAME,
    )

    load_info = pipeline.run(
        records,
        table_name=TABLE_NAME,
        write_disposition="replace",
    )

    print(load_info)
    validate_loaded_count(postgres_url, expected_count=len(records))


if __name__ == "__main__":
    main()
