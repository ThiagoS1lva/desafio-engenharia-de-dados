from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import dlt
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PIPELINE_NAME = "social_raw_ingestion"
DATASET_NAME = "raw"
WRITE_DISPOSITION = "replace"

CSV_SOURCES = [
    {
        "file_name": "instagram_media.csv",
        "table_name": "instagram_media",
        "required_columns": {"id", "username", "timestamp"},
    },
    {
        "file_name": "instagram_media_insights.csv",
        "table_name": "instagram_media_insights",
        "required_columns": {"id", "reach", "views"},
    },
    {
        "file_name": "instagram_comments.csv",
        "table_name": "instagram_comments",
        "required_columns": {"post_id", "comment_id", "predicted_sentiment"},
    },
    {
        "file_name": "tiktok_posts.csv",
        "table_name": "tiktok_posts",
        "required_columns": {"item_id", "create_time", "business_username"},
    },
    {
        "file_name": "tiktok_comments.csv",
        "table_name": "tiktok_comments",
        "required_columns": {"post_id", "comment_id", "predicted_sentiment"},
    },
]


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def build_postgres_url() -> str:
    host = get_env("POSTGRES_HOST", "localhost")
    port = get_env("POSTGRES_PORT", "5432")
    db = get_env("POSTGRES_DB", "retize_social")
    user = quote_plus(get_env("POSTGRES_USER", "retize_user"))
    password = quote_plus(get_env("POSTGRES_PASSWORD", "retize_password"))

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def load_csv_records(
    csv_file: Path,
    required_columns: set[str],
) -> list[dict[str, str]]:
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    # Mantém os valores brutos como strings; a conversão de tipos é tratada depois nos modelos de staging do dbt.
    df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns in {csv_file.name}: "
            f"{', '.join(sorted(missing_columns))}"
        )

    if df.empty:
        raise ValueError(f"CSV file has no rows: {csv_file}")

    return df.to_dict(orient="records")


def validate_loaded_count(
    postgres_url: str,
    table_name: str,
    expected_count: int,
) -> None:
    with psycopg2.connect(postgres_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("select count(*) from {}.{}").format(
                    sql.Identifier(DATASET_NAME),
                    sql.Identifier(table_name),
                )
            )
            loaded_count = cursor.fetchone()[0]

    if loaded_count != expected_count:
        raise RuntimeError(
            f"Row count mismatch for {DATASET_NAME}.{table_name}: "
            f"expected {expected_count}, got {loaded_count}"
        )

    print(f"Validated {DATASET_NAME}.{table_name}: {loaded_count} rows loaded.")


def load_source(
    pipeline: dlt.Pipeline,
    postgres_url: str,
    source: dict[str, object],
) -> int:
    csv_file = PROJECT_ROOT / str(source["file_name"])
    table_name = str(source["table_name"])
    required_columns = source["required_columns"]

    if not isinstance(required_columns, set):
        raise TypeError(f"required_columns must be a set for {csv_file.name}")

    records = load_csv_records(csv_file, required_columns)

    print(f"Loading {csv_file.name} into {DATASET_NAME}.{table_name}...")
    load_info = pipeline.run(
        records,
        table_name=table_name,
        write_disposition=WRITE_DISPOSITION,
    )
    print(load_info)

    validate_loaded_count(postgres_url, table_name, expected_count=len(records))
    return len(records)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    postgres_url = build_postgres_url()

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=dlt.destinations.postgres(postgres_url),
        dataset_name=DATASET_NAME,
    )

    loaded_tables: list[tuple[str, int]] = []
    for source in CSV_SOURCES:
        row_count = load_source(pipeline, postgres_url, source)
        loaded_tables.append((str(source["table_name"]), row_count))

    print("Ingestion completed successfully:")
    for table_name, row_count in loaded_tables:
        print(f"- {DATASET_NAME}.{table_name}: {row_count} rows")


if __name__ == "__main__":
    main()
