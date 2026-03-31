# Migration Validation Reference

Concrete SQL patterns and a Python orchestrator for validating that a migration to MotherDuck produced correct results. Every query outputs a `pct_variance` column so the user can decide what is acceptable.

---

## Row Count Comparison

Compare total row counts between source and target with percentage variance.

```sql
WITH counts AS (
    SELECT
        'source' AS side,
        count(*) AS row_count
    FROM "source_db"."main"."orders"
    UNION ALL
    SELECT
        'target' AS side,
        count(*) AS row_count
    FROM "target_db"."main"."orders"
)
SELECT
    MAX(row_count) FILTER (WHERE side = 'source') AS source_rows,
    MAX(row_count) FILTER (WHERE side = 'target') AS target_rows,
    MAX(row_count) FILTER (WHERE side = 'target')
        - MAX(row_count) FILTER (WHERE side = 'source') AS row_diff,
    ROUND(
        100.0
        * (MAX(row_count) FILTER (WHERE side = 'target')
           - MAX(row_count) FILTER (WHERE side = 'source'))
        / NULLIF(MAX(row_count) FILTER (WHERE side = 'source'), 0),
        2
    ) AS pct_variance
FROM counts;
```

---

## Side-by-Side Metric Comparison

Compare key aggregates between source and target. Replace `amount` and `quantity` with your numeric columns.

```sql
WITH source_metrics AS (
    SELECT
        count(*) AS row_count,
        SUM(amount) AS sum_amount,
        AVG(amount) AS avg_amount,
        MIN(amount) AS min_amount,
        MAX(amount) AS max_amount,
        SUM(quantity) AS sum_quantity,
        AVG(quantity) AS avg_quantity
    FROM "source_db"."main"."orders"
),
target_metrics AS (
    SELECT
        count(*) AS row_count,
        SUM(amount) AS sum_amount,
        AVG(amount) AS avg_amount,
        MIN(amount) AS min_amount,
        MAX(amount) AS max_amount,
        SUM(quantity) AS sum_quantity,
        AVG(quantity) AS avg_quantity
    FROM "target_db"."main"."orders"
),
comparisons AS (
    SELECT unnest([
        {'metric': 'row_count',    'source': s.row_count::DOUBLE,    'target': t.row_count::DOUBLE},
        {'metric': 'sum_amount',   'source': s.sum_amount::DOUBLE,   'target': t.sum_amount::DOUBLE},
        {'metric': 'avg_amount',   'source': s.avg_amount::DOUBLE,   'target': t.avg_amount::DOUBLE},
        {'metric': 'min_amount',   'source': s.min_amount::DOUBLE,   'target': t.min_amount::DOUBLE},
        {'metric': 'max_amount',   'source': s.max_amount::DOUBLE,   'target': t.max_amount::DOUBLE},
        {'metric': 'sum_quantity', 'source': s.sum_quantity::DOUBLE, 'target': t.sum_quantity::DOUBLE},
        {'metric': 'avg_quantity', 'source': s.avg_quantity::DOUBLE, 'target': t.avg_quantity::DOUBLE}
    ]) AS r
    FROM source_metrics s, target_metrics t
)
SELECT
    r.metric AS metric_name,
    r.source AS source_value,
    r.target AS target_value,
    ROUND(r.target - r.source, 4) AS abs_diff,
    ROUND(
        100.0 * (r.target - r.source) / NULLIF(r.source, 0), 2
    ) AS pct_variance
FROM comparisons;
```

---

## Uniqueness Check on Target

Verify the migration did not introduce duplicate records. Replace `order_id` with your primary key column.

```sql
SELECT
    order_id,
    count(*) AS duplicate_count
FROM "target_db"."main"."orders"
GROUP BY order_id
HAVING count(*) > 1
ORDER BY duplicate_count DESC;
```

An empty result set means no duplicates exist.

---

## New Records (In Target, Not In Source)

Identify records that appear in the target but not in the source. These may be expected (if the migration included new data) or a problem.

```sql
SELECT order_id
FROM "target_db"."main"."orders"
EXCEPT
SELECT order_id
FROM "source_db"."main"."orders";
```

Count them:

```sql
SELECT count(*) AS new_record_count
FROM (
    SELECT order_id FROM "target_db"."main"."orders"
    EXCEPT
    SELECT order_id FROM "source_db"."main"."orders"
);
```

---

## Deleted Records (In Source, Not In Target)

Identify records that exist in the source but are missing from the target.

```sql
SELECT order_id
FROM "source_db"."main"."orders"
EXCEPT
SELECT order_id
FROM "target_db"."main"."orders";
```

Count them:

```sql
SELECT count(*) AS deleted_record_count
FROM (
    SELECT order_id FROM "source_db"."main"."orders"
    EXCEPT
    SELECT order_id FROM "target_db"."main"."orders"
);
```

---

## Changed Records Tracking

Find records that exist in both source and target but have different values. Replace column names with your own.

### Column-Level Comparison

Use `IS DISTINCT FROM` instead of `<>` to handle NULLs correctly.

```sql
SELECT
    s.order_id,
    s.amount AS source_amount,
    t.amount AS target_amount,
    s.status AS source_status,
    t.status AS target_status
FROM "source_db"."main"."orders" s
JOIN "target_db"."main"."orders" t
    ON s.order_id = t.order_id
WHERE s.amount IS DISTINCT FROM t.amount
   OR s.status IS DISTINCT FROM t.status;
```

### Hash-Based Comparison for Wide Tables

When a table has many columns, compare row hashes instead of listing every column.

```sql
WITH source_hashed AS (
    SELECT
        order_id,
        md5(COLUMNS(* EXCLUDE (order_id))::VARCHAR) AS row_hash
    FROM "source_db"."main"."orders"
),
target_hashed AS (
    SELECT
        order_id,
        md5(COLUMNS(* EXCLUDE (order_id))::VARCHAR) AS row_hash
    FROM "target_db"."main"."orders"
)
SELECT
    COALESCE(s.order_id, t.order_id) AS order_id,
    s.row_hash AS source_hash,
    t.row_hash AS target_hash
FROM source_hashed s
JOIN target_hashed t
    ON s.order_id = t.order_id
WHERE s.row_hash IS DISTINCT FROM t.row_hash;
```

Once you identify changed IDs via hashing, use the column-level comparison query filtered to those IDs to see exactly what changed.

### Performance Note

For large tables, filter both sides to a date range or partition before comparing:

```sql
-- Add a WHERE clause to both source and target CTEs
WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01'
```

---

## Python Validation Orchestrator

Runs all checks and returns a structured report. Uses the DuckDB Python API.

```python
"""
Migration Validation Orchestrator
Runs source-vs-target checks and reports variance.

Install: pip install duckdb
"""

import duckdb


def validate_migration(
    source_conn: duckdb.DuckDBPyConnection,
    target_conn: duckdb.DuckDBPyConnection,
    source_table: str,
    target_table: str,
    key_column: str,
    numeric_columns: list[str],
    variance_threshold_pct: float = 0.0,
) -> dict:
    """
    Run all migration validation checks.

    Args:
        source_conn: Connection to the source database.
        target_conn: Connection to the target database.
        source_table: Fully qualified source table (e.g., '"source_db"."main"."orders"').
        target_table: Fully qualified target table (e.g., '"target_db"."main"."orders"').
        key_column: Primary key column name for record-level comparisons.
        numeric_columns: List of numeric column names for metric comparisons.
        variance_threshold_pct: Acceptable % variance. 0.0 means exact match required.

    Returns:
        Dict with results for each check and an overall pass/fail.
    """
    results = {}

    # --- Row counts ---
    source_count = source_conn.sql(f"SELECT count(*) FROM {source_table}").fetchone()[0]
    target_count = target_conn.sql(f"SELECT count(*) FROM {target_table}").fetchone()[0]
    count_variance = (
        round(100.0 * (target_count - source_count) / source_count, 2)
        if source_count > 0
        else None
    )
    results["row_counts"] = {
        "source": source_count,
        "target": target_count,
        "diff": target_count - source_count,
        "pct_variance": count_variance,
        "pass": abs(count_variance or 0) <= variance_threshold_pct,
    }

    # --- Metric comparison ---
    metrics = {}
    for col in numeric_columns:
        for agg in ["SUM", "AVG", "MIN", "MAX"]:
            source_val = source_conn.sql(
                f"SELECT {agg}({col})::DOUBLE FROM {source_table}"
            ).fetchone()[0]
            target_val = target_conn.sql(
                f"SELECT {agg}({col})::DOUBLE FROM {target_table}"
            ).fetchone()[0]
            pct = (
                round(100.0 * (target_val - source_val) / source_val, 4)
                if source_val
                else None
            )
            metric_key = f"{agg.lower()}_{col}"
            metrics[metric_key] = {
                "source": source_val,
                "target": target_val,
                "pct_variance": pct,
                "pass": abs(pct or 0) <= variance_threshold_pct,
            }
    results["metrics"] = metrics

    # --- Uniqueness ---
    dupes = target_conn.sql(
        f"SELECT {key_column}, count(*) AS cnt FROM {target_table} "
        f"GROUP BY {key_column} HAVING cnt > 1"
    ).fetchall()
    results["uniqueness"] = {
        "duplicate_count": len(dupes),
        "duplicate_keys": [row[0] for row in dupes[:20]],
        "pass": len(dupes) == 0,
    }

    # --- New records (in target, not in source) ---
    new_ids = target_conn.sql(
        f"SELECT {key_column} FROM {target_table} "
        f"EXCEPT SELECT {key_column} FROM {source_table}"
    ).fetchall()
    results["new_records"] = {
        "count": len(new_ids),
        "sample_keys": [row[0] for row in new_ids[:20]],
        "pass": len(new_ids) == 0,
    }

    # --- Deleted records (in source, not in target) ---
    deleted_ids = source_conn.sql(
        f"SELECT {key_column} FROM {source_table} "
        f"EXCEPT SELECT {key_column} FROM {target_table}"
    ).fetchall()
    results["deleted_records"] = {
        "count": len(deleted_ids),
        "sample_keys": [row[0] for row in deleted_ids[:20]],
        "pass": len(deleted_ids) == 0,
    }

    # --- Changed records (hash comparison) ---
    changed = target_conn.sql(f"""
        WITH source_h AS (
            SELECT {key_column},
                   md5(COLUMNS(* EXCLUDE ({key_column}))::VARCHAR) AS rh
            FROM {source_table}
        ),
        target_h AS (
            SELECT {key_column},
                   md5(COLUMNS(* EXCLUDE ({key_column}))::VARCHAR) AS rh
            FROM {target_table}
        )
        SELECT s.{key_column}
        FROM source_h s
        JOIN target_h t ON s.{key_column} = t.{key_column}
        WHERE s.rh IS DISTINCT FROM t.rh
    """).fetchall()
    results["changed_records"] = {
        "count": len(changed),
        "sample_keys": [row[0] for row in changed[:20]],
        "pass": len(changed) == 0,
    }

    # --- Overall ---
    results["overall_pass"] = all(
        v.get("pass", True)
        for v in results.values()
        if isinstance(v, dict) and "pass" in v
    ) and all(
        m.get("pass", True) for m in results.get("metrics", {}).values()
    )

    return results


def print_report(results: dict) -> None:
    """Print a human-readable validation report."""
    print("=== Migration Validation Report ===\n")

    rc = results["row_counts"]
    status = "PASS" if rc["pass"] else "FAIL"
    print(f"Row Counts [{status}]: source={rc['source']}  target={rc['target']}  "
          f"diff={rc['diff']}  variance={rc['pct_variance']}%")

    print("\nMetrics:")
    for name, m in results["metrics"].items():
        status = "PASS" if m["pass"] else "FAIL"
        print(f"  {name} [{status}]: source={m['source']}  target={m['target']}  "
              f"variance={m['pct_variance']}%")

    u = results["uniqueness"]
    status = "PASS" if u["pass"] else "FAIL"
    print(f"\nUniqueness [{status}]: {u['duplicate_count']} duplicate keys found")

    nr = results["new_records"]
    status = "PASS" if nr["pass"] else "FAIL"
    print(f"New Records [{status}]: {nr['count']} records in target not in source")

    dr = results["deleted_records"]
    status = "PASS" if dr["pass"] else "FAIL"
    print(f"Deleted Records [{status}]: {dr['count']} records in source not in target")

    cr = results["changed_records"]
    status = "PASS" if cr["pass"] else "FAIL"
    print(f"Changed Records [{status}]: {cr['count']} records with different values")

    overall = "PASS" if results["overall_pass"] else "FAIL"
    print(f"\n=== Overall: {overall} ===")
```

### Usage Example

```python
import duckdb

# Connect to both databases
USE_CASE_USER_AGENT = "agent-skills/1.0.0(harness-codex;llm-gpt-5.4)"
conn = duckdb.connect(f"md:?custom_user_agent={USE_CASE_USER_AGENT}")

# If source is a Postgres database (local DuckDB only):
# conn.sql("ATTACH 'dbname=legacy host=pg.example.com' AS source_db (TYPE POSTGRES, READ_ONLY)")

results = validate_migration(
    source_conn=conn,
    target_conn=conn,
    source_table='"source_db"."main"."orders"',
    target_table='"target_db"."main"."orders"',
    key_column="order_id",
    numeric_columns=["amount", "quantity"],
    variance_threshold_pct=0.5,  # allow 0.5% variance
)

print_report(results)
```
