import json
import sys
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts._lib.motherduck_artifact_utils import artifact_session


CLIENTS = [
    {"slug": "acme", "database": "customer_acme", "region": "us-east-1"},
    {"slug": "globex", "database": "customer_globex", "region": "eu-central-1"},
]


def fetch_rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    with artifact_session(
        slug="motherduck-partner-delivery",
        database_keys=[client["database"] for client in CLIENTS],
    ) as session:
        conn = session.conn
        for client in CLIENTS:
            usage_table = session.table(client["database"], "main", "usage_daily")
            conn.execute(
                f"""
                CREATE TABLE {usage_table} (
                    usage_date DATE,
                    account_count INTEGER
                )
                """
            )
            conn.execute(
                f"""
                INSERT INTO {usage_table}
                VALUES ('2026-03-01', 12), ('2026-03-02', 14)
                """
            )

        result = {
            "backend": session.describe(),
            "delivery_pattern": "one database and service-account boundary per client",
            "clients": [],
        }
        for client in CLIENTS:
            actual_database = session.database_name(client["database"])
            result["clients"].append(
                {
                    **client,
                    "database": actual_database,
                    "tables": fetch_rows(
                        conn,
                        f"""
                        SELECT table_name
                        FROM duckdb_tables()
                        WHERE database_name = '{actual_database}'
                        ORDER BY table_name
                        """,
                    ),
                }
            )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
