import json
import sys
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts._lib.motherduck_artifact_utils import artifact_session


def compare_metrics(conn: duckdb.DuckDBPyConnection, source_table: str, target_table: str, column: str) -> dict:
    results = {}
    for agg in ["count(*)", f"SUM({column})", f"AVG({column})", f"MIN({column})", f"MAX({column})"]:
        src = conn.execute(f"SELECT CAST({agg} AS DOUBLE) FROM {source_table}").fetchone()[0]
        tgt = conn.execute(f"SELECT CAST({agg} AS DOUBLE) FROM {target_table}").fetchone()[0]
        pct = round(100.0 * (tgt - src) / src, 4) if src else None
        results[agg] = {"source": src, "target": tgt, "pct_variance": pct}
    return results


def main() -> None:
    with artifact_session(
        slug="migrate-to-motherduck",
        database_keys=["legacy_source", "motherduck_target"],
    ) as session:
        conn = session.conn
        source_table = session.table("legacy_source", "main", "orders")
        target_table = session.table("motherduck_target", "main", "orders")
        conn.execute(f"CREATE TABLE {source_table} (order_id INTEGER, total_amount DOUBLE)")
        conn.execute(f"CREATE TABLE {target_table} (order_id INTEGER, total_amount DOUBLE)")
        conn.executemany(
            f"INSERT INTO {source_table} VALUES (?, ?)",
            [(1, 100.0), (2, 150.0), (3, 200.0)],
        )
        conn.executemany(
            f"INSERT INTO {target_table} VALUES (?, ?)",
            [(1, 100.0), (2, 150.0), (4, 210.0)],
        )

        result = {
            "backend": session.describe(),
            "metric_comparison": compare_metrics(conn, source_table, target_table, "total_amount"),
            "new_records": conn.execute(
                f"SELECT order_id FROM {target_table} EXCEPT SELECT order_id FROM {source_table}"
            ).fetchall(),
            "deleted_records": conn.execute(
                f"SELECT order_id FROM {source_table} EXCEPT SELECT order_id FROM {target_table}"
            ).fetchall(),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
