import json
import sys
import tempfile
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts.motherduck_artifact_utils import artifact_session


def fetch_rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    with artifact_session(
        slug="build-data-pipeline",
        database_keys=["raw", "staging", "analytics"],
    ) as session:
        conn = session.conn
        raw_table = session.table("raw", "main", "orders_landing")
        staging_table = session.table("staging", "main", "orders_deduped")
        analytics_table = session.table("analytics", "main", "daily_revenue")

        with tempfile.TemporaryDirectory(prefix="md_pipeline_stage_") as tmpdir:
            parquet_path = Path(tmpdir) / "orders_landing.parquet"
            conn.execute(
                """
                CREATE TEMP TABLE stage_orders_extract AS
                SELECT *
                FROM (
                  VALUES
                    (1, 101, DATE '2026-03-01', 120.0, TIMESTAMP '2026-03-01 10:00:00'),
                    (1, 101, DATE '2026-03-01', 120.0, TIMESTAMP '2026-03-01 12:00:00'),
                    (2, 102, DATE '2026-03-02', 75.0, TIMESTAMP '2026-03-02 09:00:00'),
                    (3, 103, DATE '2026-03-03', 210.0, TIMESTAMP '2026-03-03 11:00:00')
                ) AS source_rows(order_id, customer_id, order_date, total_amount, updated_at)
                """
            )
            conn.execute(
                f"""
                COPY stage_orders_extract
                TO {sql_string(str(parquet_path))}
                (FORMAT PARQUET)
                """
            )
            conn.execute(
                f"""
                CREATE TABLE {raw_table} AS
                SELECT *
                FROM read_parquet({sql_string(str(parquet_path))})
                """
            )

        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {staging_table} AS
            WITH ranked AS (
              SELECT *,
                     ROW_NUMBER() OVER (
                       PARTITION BY order_id
                       ORDER BY updated_at DESC
                     ) AS row_num
              FROM {raw_table}
            )
            SELECT order_id, customer_id, order_date, total_amount
            FROM ranked
            WHERE row_num = 1
            """
        )

        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {analytics_table} AS
            SELECT
              order_date,
              COUNT(*) AS order_count,
              SUM(total_amount) AS total_revenue,
              AVG(total_amount) AS avg_order_value
            FROM {staging_table}
            GROUP BY 1
            ORDER BY 1
            """
        )

        result = {
            "backend": session.describe(),
            "ingestion_mode": "bulk_parquet_stage",
            "stages": {
                "raw": fetch_rows(conn, f"SELECT COUNT(*) AS row_count FROM {raw_table}"),
                "staging": fetch_rows(conn, f"SELECT COUNT(*) AS row_count FROM {staging_table}"),
                "analytics": fetch_rows(conn, f"SELECT * FROM {analytics_table}"),
            },
        }
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
