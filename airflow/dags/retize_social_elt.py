from __future__ import annotations

import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


PROJECT_DIR = Path("/opt/airflow/project")
DBT_DIR = PROJECT_DIR / "dbt"
QUERIES_DIR = PROJECT_DIR / "queries"


def _run_shell_step(step_name: str, command: list[str], cwd: str | None = None) -> None:
    workdir = cwd or str(PROJECT_DIR)
    env = os.environ.copy()
    start = time.monotonic()

    logging.info("[%s] Starting command in %s", step_name, workdir)
    logging.info("[%s] Command: %s", step_name, " ".join(command))

    completed = subprocess.run(
        command,
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.stdout:
        logging.info("[%s] stdout:\n%s", step_name, completed.stdout.strip())
    if completed.stderr:
        logging.info("[%s] stderr:\n%s", step_name, completed.stderr.strip())

    if completed.returncode != 0:
        raise AirflowException(f"[{step_name}] command failed with exit code {completed.returncode}")

    elapsed = time.monotonic() - start
    logging.info("[%s] Completed successfully in %.2f seconds", step_name, elapsed)


def _check_binaries() -> None:
    for binary in ("python", "dbt"):
        completed = subprocess.run(
            ["bash", "-lc", f"command -v {binary}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AirflowException(f"Required binary not found in PATH: {binary}")

    logging.info("[precheck] Required binaries available: python, dbt")


def _run_query_file(query_file_name: str) -> None:
    start = time.monotonic()
    query_path = QUERIES_DIR / query_file_name
    if not query_path.exists():
        raise AirflowException(f"Query file not found: {query_path}")

    sql_text = query_path.read_text(encoding="utf-8")
    hook = PostgresHook(postgres_conn_id="retize_social")

    logging.info("[queries] Executing %s", query_path)

    with hook.get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_text)

            if cursor.description is None:
                logging.info("[queries] %s executed (no result set)", query_file_name)
                return

            columns = [col.name for col in cursor.description]
            rows = cursor.fetchall()

    sample_size = min(5, len(rows))
    logging.info("[queries] %s returned %s rows", query_file_name, len(rows))
    if sample_size > 0:
        logging.info("[queries] %s sample columns: %s", query_file_name, columns)
        for row in rows[:sample_size]:
            logging.info("[queries] %s sample row: %s", query_file_name, row)

    elapsed = time.monotonic() - start
    logging.info("[queries] %s completed in %.2f seconds", query_file_name, elapsed)


default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=20),
}


with DAG(
    dag_id="retize_social_elt",
    description="Pipeline completo: dlt -> dbt run -> dbt test -> queries",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@once",
    catchup=False,
    max_active_runs=1,
    tags=["retize", "elt", "dlt", "dbt"],
) as dag:
    precheck_runtime = PythonOperator(
        task_id="precheck_runtime",
        python_callable=_check_binaries,
    )

    run_dlt_ingestion = PythonOperator(
        task_id="run_dlt_ingestion",
        python_callable=_run_shell_step,
        op_kwargs={
            "step_name": "dlt_ingestion",
            "command": ["python", "-m", "src.ingestion.dlt_pipeline"],
            "cwd": str(PROJECT_DIR),
        },
    )

    run_dbt = PythonOperator(
        task_id="run_dbt",
        python_callable=_run_shell_step,
        op_kwargs={
            "step_name": "dbt_run",
            "command": [
                "dbt",
                "run",
                "--project-dir",
                str(DBT_DIR),
                "--profiles-dir",
                str(DBT_DIR),
                "--target",
                "dev",
            ],
            "cwd": str(PROJECT_DIR),
        },
    )

    run_dbt_tests = PythonOperator(
        task_id="run_dbt_test",
        python_callable=_run_shell_step,
        op_kwargs={
            "step_name": "dbt_test",
            "command": [
                "dbt",
                "test",
                "--project-dir",
                str(DBT_DIR),
                "--profiles-dir",
                str(DBT_DIR),
                "--target",
                "dev",
            ],
            "cwd": str(PROJECT_DIR),
        },
    )

    query_01 = PythonOperator(
        task_id="query_01",
        python_callable=_run_query_file,
        op_kwargs={"query_file_name": "pergunta_01.sql"},
    )

    query_02 = PythonOperator(
        task_id="query_02",
        python_callable=_run_query_file,
        op_kwargs={"query_file_name": "pergunta_02.sql"},
    )

    query_03 = PythonOperator(
        task_id="query_03",
        python_callable=_run_query_file,
        op_kwargs={"query_file_name": "pergunta_03.sql"},
    )

    query_04 = PythonOperator(
        task_id="query_04",
        python_callable=_run_query_file,
        op_kwargs={"query_file_name": "pergunta_04.sql"},
    )

    query_05 = PythonOperator(
        task_id="query_05",
        python_callable=_run_query_file,
        op_kwargs={"query_file_name": "pergunta_05.sql"},
    )

    precheck_runtime >> run_dlt_ingestion >> run_dbt >> run_dbt_tests >> query_01 >> query_02 >> query_03 >> query_04 >> query_05
