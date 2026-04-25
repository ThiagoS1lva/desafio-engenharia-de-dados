from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_NAME = "raw"
ACCEPTED_SENTIMENTS = ("positivo", "neutro", "negativo")
PERIOD_START = "2025-03-01 00:00:00+00"
PERIOD_END_EXCLUSIVE = "2026-04-01 00:00:00+00"


@dataclass(frozen=True)
class TableSpec:
    file_name: str
    table_name: str
    required_columns: tuple[str, ...]
    unique_columns: tuple[str, ...]


@dataclass(frozen=True)
class RelationshipCheck:
    name: str
    child_table: str
    child_column: str
    parent_table: str
    parent_column: str


@dataclass(frozen=True)
class DateCheck:
    name: str
    table_name: str
    column_name: str
    source_type: str


TABLE_SPECS = (
    TableSpec("instagram_media.csv", "instagram_media", ("id",), ("id",)),
    TableSpec("instagram_media_insights.csv", "instagram_media_insights", ("id",), ("id",)),
    TableSpec(
        "instagram_comments.csv",
        "instagram_comments",
        ("comment_id", "post_id"),
        ("comment_id",),
    ),
    TableSpec("tiktok_posts.csv", "tiktok_posts", ("item_id",), ("item_id",)),
    TableSpec(
        "tiktok_comments.csv",
        "tiktok_comments",
        ("comment_id", "post_id"),
        ("comment_id",),
    ),
)

RELATIONSHIP_CHECKS = (
    RelationshipCheck(
        "instagram insights sem media correspondente",
        "instagram_media_insights",
        "id",
        "instagram_media",
        "id",
    ),
    RelationshipCheck(
        "comentarios instagram sem media correspondente",
        "instagram_comments",
        "post_id",
        "instagram_media",
        "id",
    ),
    RelationshipCheck(
        "comentarios tiktok sem post correspondente",
        "tiktok_comments",
        "post_id",
        "tiktok_posts",
        "item_id",
    ),
)

DATE_CHECKS = (
    DateCheck("data de publicacao instagram", "instagram_media", "timestamp", "timestamp_text"),
    DateCheck("data de comentario instagram", "instagram_comments", "comment_timestamp", "timestamp_text"),
    DateCheck("data de publicacao tiktok", "tiktok_posts", "create_time", "unix_timestamp"),
    DateCheck("data de comentario tiktok", "tiktok_comments", "comment_timestamp", "timestamp_text"),
)


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def build_postgres_url() -> str:
    host = get_env("POSTGRES_HOST", "localhost")
    port = get_env("POSTGRES_PORT", "5432")
    db = get_env("POSTGRES_DB", "retize_social")
    user = quote_plus(get_env("POSTGRES_USER", "retize_user"))
    password = quote_plus(get_env("POSTGRES_PASSWORD", "retize_password"))

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def count_csv_rows(csv_file: Path) -> int:
    if not csv_file.exists():
        raise FileNotFoundError(f"Arquivo CSV nao encontrado: {csv_file}")

    with csv_file.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        return sum(1 for _ in reader)


def fetch_scalar(conn: psycopg2.extensions.connection, query: sql.Composed, params: tuple = ()) -> int:
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()[0]


def table_identifier(table_name: str) -> sql.Composed:
    return sql.SQL("{}.{}").format(sql.Identifier(DATASET_NAME), sql.Identifier(table_name))


def column_is_blank(column_name: str) -> sql.Composed:
    return sql.SQL("nullif(btrim(coalesce({}::text, '')), '') is null").format(
        sql.Identifier(column_name)
    )


def column_is_not_blank(column_name: str) -> sql.Composed:
    return sql.SQL("nullif(btrim(coalesce({}::text, '')), '') is not null").format(
        sql.Identifier(column_name)
    )


def table_exists(conn: psycopg2.extensions.connection, table_name: str) -> bool:
    query = sql.SQL(
        """
        select exists (
            select 1
            from information_schema.tables
            where table_schema = %s
              and table_name = %s
        )
        """
    )
    return bool(fetch_scalar(conn, query, (DATASET_NAME, table_name)))


def count_table_rows(conn: psycopg2.extensions.connection, table_name: str) -> int:
    query = sql.SQL("select count(*) from {}").format(table_identifier(table_name))
    return fetch_scalar(conn, query)


def count_blank_keys(
    conn: psycopg2.extensions.connection,
    table_name: str,
    key_column: str,
) -> int:
    query = sql.SQL("select count(*) from {} where {}").format(
        table_identifier(table_name),
        column_is_blank(key_column),
    )
    return fetch_scalar(conn, query)


def count_duplicate_keys(
    conn: psycopg2.extensions.connection,
    table_name: str,
    key_column: str,
) -> int:
    query = sql.SQL(
        """
        select count(*)
        from (
            select {key_column}
            from {table}
            where {key_not_blank}
            group by {key_column}
            having count(*) > 1
        ) duplicates
        """
    ).format(
        key_column=sql.Identifier(key_column),
        table=table_identifier(table_name),
        key_not_blank=column_is_not_blank(key_column),
    )
    return fetch_scalar(conn, query)


def count_invalid_sentiments(conn: psycopg2.extensions.connection, table_name: str) -> int:
    accepted_values = sql.SQL(", ").join(sql.Literal(value) for value in ACCEPTED_SENTIMENTS)
    query = sql.SQL(
        """
        select count(*)
        from {table}
        where nullif(btrim(coalesce({sentiment_column}::text, '')), '') is null
           or lower(btrim({sentiment_column}::text)) not in ({accepted_values})
        """
    ).format(
        table=table_identifier(table_name),
        sentiment_column=sql.Identifier("predicted_sentiment"),
        accepted_values=accepted_values,
    )
    return fetch_scalar(conn, query)


def count_orphans(conn: psycopg2.extensions.connection, check: RelationshipCheck) -> int:
    query = sql.SQL(
        """
        select count(*)
        from {child_table} as child
        left join {parent_table} as parent
            on {child_key} = {parent_key}
        where nullif(btrim(coalesce({child_key}::text, '')), '') is not null
          and {parent_key} is null
        """
    ).format(
        child_table=table_identifier(check.child_table),
        parent_table=table_identifier(check.parent_table),
        child_key=sql.Identifier("child", check.child_column),
        parent_key=sql.Identifier("parent", check.parent_column),
    )
    return fetch_scalar(conn, query)


def count_invalid_dates(conn: psycopg2.extensions.connection, check: DateCheck) -> int:
    if check.source_type == "unix_timestamp":
        query = sql.SQL(
            """
            select count(*)
            from {table}
            where nullif(btrim(coalesce({column}::text, '')), '') is not null
              and {column}::text !~ '^\\d+(\\.\\d+)?$'
            """
        ).format(table=table_identifier(check.table_name), column=sql.Identifier(check.column_name))
    else:
        query = sql.SQL(
            """
            select count(*)
            from {table}
            where nullif(btrim(coalesce({column}::text, '')), '') is not null
              and {column}::text !~ '^\\d{{4}}-\\d{{2}}-\\d{{2}} '
            """
        ).format(table=table_identifier(check.table_name), column=sql.Identifier(check.column_name))

    return fetch_scalar(conn, query)


def count_dates_outside_period(conn: psycopg2.extensions.connection, check: DateCheck) -> int:
    if check.source_type == "unix_timestamp":
        query = sql.SQL(
            """
            select count(*)
            from {table}
            where {column}::text ~ '^\\d+(\\.\\d+)?$'
              and (
                  to_timestamp({column}::double precision) < %s::timestamptz
                  or to_timestamp({column}::double precision) >= %s::timestamptz
              )
            """
        ).format(table=table_identifier(check.table_name), column=sql.Identifier(check.column_name))
    else:
        query = sql.SQL(
            """
            select count(*)
            from {table}
            where {column}::text ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}} '
              and (
                  {column}::timestamptz < %s::timestamptz
                  or {column}::timestamptz >= %s::timestamptz
              )
            """
        ).format(table=table_identifier(check.table_name), column=sql.Identifier(check.column_name))

    return fetch_scalar(conn, query, (PERIOD_START, PERIOD_END_EXCLUSIVE))


def add_result(results: list[str], prefix: str, message: str) -> None:
    results.append(f"{prefix} {message}")


def validate_tables(conn: psycopg2.extensions.connection) -> tuple[list[str], list[str], set[str]]:
    critical_errors: list[str] = []
    warnings: list[str] = []
    existing_tables: set[str] = set()

    for spec in TABLE_SPECS:
        if not table_exists(conn, spec.table_name):
            add_result(critical_errors, "[ERRO]", f"Tabela ausente: {DATASET_NAME}.{spec.table_name}")
            continue

        existing_tables.add(spec.table_name)
        csv_count = count_csv_rows(PROJECT_ROOT / spec.file_name)
        table_count = count_table_rows(conn, spec.table_name)

        if table_count != csv_count:
            add_result(
                critical_errors,
                "[ERRO]",
                f"Contagem divergente em {DATASET_NAME}.{spec.table_name}: CSV={csv_count}, banco={table_count}",
            )
        else:
            print(f"[OK] {DATASET_NAME}.{spec.table_name}: {table_count} linhas")

        for required_column in spec.required_columns:
            blank_keys = count_blank_keys(conn, spec.table_name, required_column)
            if blank_keys > 0:
                add_result(
                    critical_errors,
                    "[ERRO]",
                    f"{DATASET_NAME}.{spec.table_name}.{required_column} tem {blank_keys} valores vazios",
                )

        for unique_column in spec.unique_columns:
            duplicate_keys = count_duplicate_keys(conn, spec.table_name, unique_column)
            if duplicate_keys > 0:
                add_result(
                    warnings,
                    "[ALERTA]",
                    f"{DATASET_NAME}.{spec.table_name}.{unique_column} tem {duplicate_keys} chaves duplicadas",
                )

        if spec.table_name.endswith("comments"):
            invalid_sentiments = count_invalid_sentiments(conn, spec.table_name)
            if invalid_sentiments > 0:
                add_result(
                    critical_errors,
                    "[ERRO]",
                    f"{DATASET_NAME}.{spec.table_name} tem {invalid_sentiments} sentimentos invalidos",
                )

    return critical_errors, warnings, existing_tables


def validate_relationships(
    conn: psycopg2.extensions.connection,
    existing_tables: set[str],
) -> list[str]:
    warnings: list[str] = []

    for check in RELATIONSHIP_CHECKS:
        if check.child_table not in existing_tables or check.parent_table not in existing_tables:
            continue

        orphan_count = count_orphans(conn, check)
        if orphan_count > 0:
            add_result(
                warnings,
                "[ALERTA]",
                f"{check.name}: {orphan_count} registros sem relacionamento",
            )

    return warnings


def validate_dates(conn: psycopg2.extensions.connection, existing_tables: set[str]) -> list[str]:
    warnings: list[str] = []

    for check in DATE_CHECKS:
        if check.table_name not in existing_tables:
            continue

        invalid_dates = count_invalid_dates(conn, check)
        if invalid_dates > 0:
            add_result(
                warnings,
                "[ALERTA]",
                f"{check.name}: {invalid_dates} datas com formato inesperado",
            )

        out_of_period = count_dates_outside_period(conn, check)
        if out_of_period > 0:
            add_result(
                warnings,
                "[ALERTA]",
                f"{check.name}: {out_of_period} datas fora do periodo {PERIOD_START} a {PERIOD_END_EXCLUSIVE}",
            )

    return warnings


def print_results(title: str, results: list[str]) -> None:
    if not results:
        print(f"{title}: nenhum item encontrado")
        return

    print(title)
    for result in results:
        print(f"- {result}")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    try:
        with psycopg2.connect(build_postgres_url()) as conn:
            critical_errors, table_warnings, existing_tables = validate_tables(conn)
            relationship_warnings = validate_relationships(conn, existing_tables)
            date_warnings = validate_dates(conn, existing_tables)
    except psycopg2.OperationalError as exc:
        print(f"[ERRO] Falha ao conectar no PostgreSQL: {exc}")
        sys.exit(1)

    warnings = table_warnings + relationship_warnings + date_warnings

    print_results("Erros criticos", critical_errors)
    print_results("Alertas", warnings)

    if critical_errors:
        print("Validacao raw finalizada com erro critico.")
        sys.exit(1)

    print("Validacao raw finalizada com sucesso.")


if __name__ == "__main__":
    main()
