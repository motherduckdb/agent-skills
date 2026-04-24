# DuckDB SQL Syntax Reference

Complete function and data type reference for DuckDB on MotherDuck.

---

## Version-Sensitive Features

DuckDB's current upstream documentation can move ahead of the DuckDB versions currently supported by MotherDuck. Check MotherDuck's version-lifecycle docs before treating newly released syntax or types as production-safe in MotherDuck.

Examples to verify before relying on them:

- `MERGE INTO`
- `FILL()` window interpolation
- newly added or newly expanded types such as `VARIANT` or native `GEOMETRY`
- DuckDB 1.5 date/time behavior such as `date_trunc` returning `TIMESTAMP` when applied to `DATE`
- lakehouse-format changes that depend on current DuckDB, DuckLake, Iceberg, Delta, or httpfs extension behavior

MotherDuck-only lifecycle commands are operational SQL, not analytical query syntax:

```sql
SHUTDOWN;
SHUTDOWN TERMINATE (REASON 'stuck batch job');
```

Use `SHUTDOWN` for graceful Duckling shutdown after current work completes. Use `SHUTDOWN TERMINATE` only when the user explicitly wants to interrupt running work.

## Data Types

| Type | Description | Example |
|------|-------------|---------|
| `BOOLEAN` | True/false | `TRUE`, `FALSE` |
| `TINYINT` | 8-bit integer (-128 to 127) | `42::TINYINT` |
| `SMALLINT` | 16-bit integer | `1000::SMALLINT` |
| `INTEGER` / `INT` | 32-bit integer | `42` |
| `BIGINT` | 64-bit integer | `9999999999` |
| `HUGEINT` | 128-bit integer | `170141183460469231731687303715884105727` |
| `FLOAT` / `REAL` | 32-bit floating point | `3.14::FLOAT` |
| `DOUBLE` | 64-bit floating point | `3.14159265358979` |
| `DECIMAL(p, s)` | Fixed-point decimal | `DECIMAL(18, 2)` |
| `VARCHAR` / `TEXT` | Variable-length string | `'hello'` |
| `BLOB` | Binary data | `'\xAA\xBB'::BLOB` |
| `DATE` | Calendar date | `DATE '2023-07-23'` |
| `TIME` | Time of day | `TIME '14:30:00'` |
| `TIMESTAMP` | Date and time (no timezone) | `TIMESTAMP '2023-07-23 14:30:00'` |
| `TIMESTAMPTZ` | Timestamp with timezone | `TIMESTAMPTZ '2023-07-23 14:30:00+00'` |
| `INTERVAL` | Time duration | `INTERVAL 30 DAY` |
| `UUID` | Universally unique identifier | `gen_random_uuid()` |
| `JSON` | JSON data | `'{"a": 1}'::JSON` |
| `LIST(T)` / `T[]` | Variable-length list | `[1, 2, 3]` |
| `STRUCT` | Named fields | `{'a': 1, 'b': 'text'}` |
| `MAP(K, V)` | Key-value pairs | `MAP(['a'], [1])` |
| `UNION(...)` | Tagged union | `UNION(num INT, str VARCHAR)` |
| `ENUM(...)` | Enumeration | `CREATE TYPE mood AS ENUM ('happy', 'sad')` |

---

## String Functions

```sql
length('hello')                        -- 5
upper('hello') / lower('HELLO')        -- 'HELLO' / 'hello'
trim('  hi  ') / ltrim() / rtrim()     -- 'hi'
substr('DuckDB', 1, 4)                -- 'Duck' (start, length)
'DuckDB'[1:4]                         -- 'Duck' (slice, 1-indexed)
left('DuckDB', 4) / right('DuckDB', 2) -- 'Duck' / 'DB'
replace('DuckDB', 'Duck', 'Goose')    -- 'GooseDB'
contains('DuckDB', 'Duck')            -- true
starts_with('DuckDB', 'Duck')         -- true
ends_with('DuckDB', 'DB')             -- true
concat('a', ' ', 'b') / 'a' || 'b'   -- Concatenation
format('{} has {} items', 'cart', 5)   -- 'cart has 5 items'
lpad('42', 5, '0')                    -- '00042'
rpad('hi', 5, '!')                    -- 'hi!!!'
repeat('ab', 3)                       -- 'ababab'
reverse('hello')                      -- 'olleh'
split_part('a.b.c', '.', 2)           -- 'b'
string_split('a,b,c', ',')            -- ['a', 'b', 'c']
string_agg(col, ', ' ORDER BY col)    -- Ordered concatenation
regexp_replace('abc123', '[0-9]+', 'X') -- 'abcX'
regexp_matches('abc123', '[0-9]+')     -- true
regexp_extract('abc123def', '([0-9]+)', 1) -- '123'
```

---

## Numeric Functions

```sql
abs(-42)                               -- 42
ceil(3.2) / floor(3.8)                -- 4 / 3
round(3.14159, 2)                      -- 3.14
trunc(3.99)                            -- 3
ln(e) / log10(1000) / log2(8)         -- 1.0 / 3.0 / 3.0
power(2, 10)                           -- 1024
sqrt(144)                              -- 12.0
mod(17, 5) / 17 % 5                   -- 2
sign(-42)                              -- -1
greatest(1, 5, 3) / least(1, 5, 3)   -- 5 / 1
random()                               -- Random float in [0, 1)
setseed(0.42)                          -- Set seed for reproducibility
```

---

## Date/Time Functions

```sql
now() / current_date / current_timestamp                   -- Current date/time
date_part('year', DATE '2023-07-23')                       -- 2023
EXTRACT(MONTH FROM DATE '2023-07-23')                      -- 7
date_diff('day', DATE '2023-01-01', DATE '2023-07-23')    -- 203
age(TIMESTAMP '2023-07-23', TIMESTAMP '2020-01-01')       -- 3 years 6 months 22 days
date_add(DATE '2023-07-23', INTERVAL 30 DAY)              -- 2023-08-22
date_sub(DATE '2023-07-23', INTERVAL 1 MONTH)             -- 2023-06-23
date_trunc('month', TIMESTAMP '2023-07-23 14:30:00')      -- 2023-07-01 00:00:00
make_date(2023, 7, 23)                                     -- DATE '2023-07-23'
make_timestamp(2023, 7, 23, 14, 30, 0)                     -- TIMESTAMP
strftime(NOW(), '%Y-%m-%d')                                -- '2023-07-23'
strptime('07/23/2023', '%m/%d/%Y')::DATE                   -- Parse custom format
epoch(TIMESTAMP '2023-07-23 00:00:00')                     -- Seconds since epoch
epoch_ms(TIMESTAMP '2023-07-23 00:00:00')                  -- Milliseconds since epoch
to_timestamp(1690070400)                                    -- Epoch seconds to timestamp
```

---

## Aggregate Functions

```sql
-- Basic aggregates
count(*)                               -- Row count
count(DISTINCT col)                    -- Distinct count
sum(amount)                            -- Total
avg(score)                             -- Average
min(price)                             -- Minimum
max(price)                             -- Maximum

-- First/last (order-dependent)
first(col)                             -- First value encountered
last(col)                              -- Last value encountered
first(col ORDER BY date_col)           -- First by explicit order

-- Argmax/argmin — value at row where another column is extremal
arg_max(status, updated_at)            -- Status at latest update
arg_min(product_name, price)           -- Name of cheapest product

-- List aggregate — collect values into a list
list(col)                              -- [val1, val2, ...]
list(DISTINCT col)                     -- Deduplicated list

-- String aggregate
string_agg(name, ', ' ORDER BY name)   -- 'Alice, Bob, Charlie'

-- Approximate
approx_count_distinct(col)             -- HyperLogLog distinct count

-- Statistical
median(col)                            -- Median value
mode(col)                              -- Most frequent value
quantile(col, 0.95)                    -- 95th percentile (discrete)
quantile_cont(col, 0.95)              -- 95th percentile (continuous/interpolated)
quantile_disc(col, 0.95)              -- 95th percentile (discrete)
stddev(col)                            -- Standard deviation (sample)
variance(col)                          -- Variance (sample)

-- Correlation and regression
corr(x, y)                             -- Pearson correlation
covar_pop(x, y)                        -- Population covariance
covar_samp(x, y)                       -- Sample covariance
regr_slope(y, x)                       -- Linear regression slope
regr_intercept(y, x)                   -- Linear regression intercept

-- Bitwise
bit_and(col)                           -- Bitwise AND of all values
bit_or(col)                            -- Bitwise OR of all values
bit_xor(col)                           -- Bitwise XOR of all values

-- Boolean
bool_and(col)                          -- TRUE if all values are TRUE
bool_or(col)                           -- TRUE if any value is TRUE
```

---

## Window Functions

```sql
ROW_NUMBER() OVER (ORDER BY score DESC)
RANK() OVER (ORDER BY score DESC)              -- Gaps on ties
DENSE_RANK() OVER (ORDER BY score DESC)        -- No gaps
NTILE(4) OVER (ORDER BY score)                 -- Quartile buckets
PERCENT_RANK() OVER (ORDER BY score)           -- Relative rank (0 to 1)
CUME_DIST() OVER (ORDER BY score)              -- Cumulative distribution
LAG(col, 1) OVER (ORDER BY date_col)           -- Previous row
LEAD(col, 1) OVER (ORDER BY date_col)          -- Next row
FIRST_VALUE(col) OVER (PARTITION BY grp ORDER BY date_col)
LAST_VALUE(col) OVER (PARTITION BY grp ORDER BY date_col
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
NTH_VALUE(col, 3) OVER (ORDER BY date_col)     -- Nth row value
-- Window frames
SUM(amount) OVER (ORDER BY date_col ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
```

---

## JSON Functions

Requires the `json` extension (pre-installed on MotherDuck).

```sql
json_col->>'key'                              -- Extract as text
json_col->'$.nested.path'                     -- Extract as JSON
json_extract(data, '$.user.name')             -- Extract as JSON
json_extract_string(data, '$.user.name')      -- Extract as VARCHAR
json_type(data)                               -- 'OBJECT', 'ARRAY', etc.
json_array_length(data->'$.items')            -- Array element count
json_keys(data)                               -- Top-level keys
json_valid('{"a": 1}')                        -- true
json_serialize(any_value)                     -- Value to JSON string
to_json({'a': 1, 'b': 'text'})               -- Struct to JSON
from_json('{"a": 1}', '{"a": "INT"}')        -- JSON to typed struct
```

---

## List Functions

```sql
-- Construction
list_value(1, 2, 3)                           -- [1, 2, 3]
[1, 2, 3]                                     -- Literal syntax
generate_series(1, 10)                         -- [1, 2, ..., 10] as rows
range(0, 5)                                    -- [0, 1, 2, 3, 4] as rows

-- Aggregation and transformation
list_aggregate([1, 2, 3], 'sum')              -- 6
list_sort([3, 1, 2])                          -- [1, 2, 3]
list_reverse_sort([3, 1, 2])                  -- [3, 2, 1]
list_distinct([1, 1, 2, 3])                   -- [1, 2, 3]
list_unique([1, 1, 2, 3])                     -- 3 (count of unique)

-- Search
list_contains([1, 2, 3], 2)                   -- true
list_position([10, 20, 30], 20)               -- 2 (1-indexed)

-- Higher-order functions
list_filter([1, 2, 3, 4, 5], x -> x > 3)     -- [4, 5]
list_transform([1, 2, 3], x -> x * 10)        -- [10, 20, 30]
list_reduce([1, 2, 3, 4], (x, y) -> x + y)   -- 10

-- Manipulation
list_concat([1, 2], [3, 4])                   -- [1, 2, 3, 4]
list_slice([10, 20, 30, 40], 2, 3)            -- [20, 30]
flatten([[1, 2], [3, 4]])                     -- [1, 2, 3, 4]

-- Expansion
UNNEST([10, 20, 30])                          -- Expands to 3 rows

-- List comprehensions
[x * 2 FOR x IN [1, 2, 3]]                   -- [2, 4, 6]
[x FOR x IN [1, 2, 3, 4, 5] IF x > 3]       -- [4, 5]
```

---

## Spatial Functions

Provided by the `spatial` extension (pre-installed on MotherDuck).

```sql
-- Construction
ST_Point(longitude, latitude)
ST_MakeLine(geom1, geom2)
ST_GeomFromText('POINT(0 0)')
ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))')

-- Measurement
ST_Area(polygon)                              -- Area of polygon
ST_Length(line)                                -- Length of line
ST_Distance(geom1, geom2)                     -- Distance between geometries

-- Relationships
ST_Intersects(geom1, geom2)                   -- True if geometries intersect
ST_Contains(outer_geom, inner_geom)           -- True if outer contains inner
ST_Within(inner_geom, outer_geom)             -- True if inner is within outer

-- Transformation
ST_Transform(geom, 'EPSG:4326', 'EPSG:3857') -- Reproject coordinates
ST_Buffer(geom, distance)                     -- Buffer around geometry

-- Serialization
ST_AsText(geom)                               -- WKT string
ST_AsGeoJSON(geom)                            -- GeoJSON string
```

---

## H3 Functions

Provided by the `h3` extension (pre-installed on MotherDuck).

```sql
-- Indexing
h3_latlng_to_cell(lat, lng, resolution)       -- Lat/lng to H3 cell ID
h3_cell_to_latlng(cell_id)                    -- H3 cell to lat/lng center
h3_cell_to_boundary(cell_id)                  -- H3 cell boundary polygon

-- Hierarchy
h3_get_resolution(cell_id)                    -- Resolution of cell (0-15)
h3_cell_to_parent(cell_id, parent_res)        -- Parent cell at resolution
h3_cell_to_children(cell_id, child_res)       -- Child cells at resolution

-- Traversal and area
h3_grid_disk(cell_id, k)                      -- Cells within k rings
h3_cell_area(cell_id, 'km^2')                 -- Area of cell

-- Conversion
h3_cells_to_multi_polygon(cell_list)          -- Cells to polygon geometry
```

---

## Table Functions

```sql
-- CSV
SELECT * FROM read_csv('data.csv');
SELECT * FROM read_csv('data.csv',
    header = true,
    delim = ',',
    quote = '"',
    columns = {'name': 'VARCHAR', 'age': 'INTEGER'}
);

-- Parquet
SELECT * FROM read_parquet('data.parquet');
SELECT * FROM read_parquet('s3://bucket/path/*.parquet');  -- Glob pattern
SELECT * FROM read_parquet(['file1.parquet', 'file2.parquet']);

-- JSON
SELECT * FROM read_json('data.json');
SELECT * FROM read_json('data.json', format = 'array');

-- Excel
SELECT * FROM read_excel('data.xlsx');
SELECT * FROM read_excel('data.xlsx', sheet = 'Sheet2');

-- Generate series and range
SELECT * FROM generate_series(1, 100);         -- 1 to 100 inclusive
SELECT * FROM range(0, 10);                    -- 0 to 9

-- Unnest (expand list/struct to rows)
SELECT UNNEST([1, 2, 3]) AS val;
SELECT UNNEST({'a': 1, 'b': 2});               -- Columns a and b

-- Glob (list files matching pattern)
SELECT * FROM glob('data/*.csv');
```

---

## PIVOT / UNPIVOT

### PIVOT — rows to columns

```sql
PIVOT monthly_sales ON month USING SUM(revenue) GROUP BY product;
PIVOT orders ON status IN ('pending', 'shipped', 'delivered') USING COUNT(*) GROUP BY region;
```

### UNPIVOT — columns to rows

```sql
UNPIVOT quarterly_data ON q1, q2, q3, q4 INTO NAME quarter VALUE revenue;
```

---

## Regular Expressions

```sql
-- SIMILAR TO (SQL standard regex)
SELECT 'hello' SIMILAR TO 'h.*o';             -- true
SELECT name FROM t WHERE name SIMILAR TO '[A-Z]%';

-- Regex match (boolean)
regexp_matches('abc123', '^[a-z]+[0-9]+$')    -- true

-- Regex replace
regexp_replace('abc 123 def', '[0-9]+', 'NUM') -- 'abc NUM def'
regexp_replace('aaa', 'a', 'b', 'g')          -- 'bbb' (global flag)

-- Regex extract
regexp_extract('email: user@host.com', '([a-z]+)@([a-z.]+)', 0) -- 'user@host.com'
regexp_extract('email: user@host.com', '([a-z]+)@([a-z.]+)', 1) -- 'user'
regexp_extract('email: user@host.com', '([a-z]+)@([a-z.]+)', 2) -- 'host.com'

-- Split by regex
regexp_split_to_array('one, two,  three', ',\\s*') -- ['one', 'two', 'three']

-- LIKE and ILIKE (pattern matching, not regex)
SELECT * FROM t WHERE name LIKE 'A%';         -- Case-sensitive
SELECT * FROM t WHERE name ILIKE 'a%';        -- Case-insensitive
```

---

## Conditional Expressions

```sql
CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' ELSE 'C' END
COALESCE(col1, col2, 'default')               -- First non-NULL
IFNULL(nullable_col, 'fallback')              -- Two-arg coalesce
NULLIF(col, 0)                                -- NULL if col = 0
IIF(score > 50, 'pass', 'fail')               -- Inline if (ternary)
```

---

## Common Table Expressions (CTEs)

```sql
-- Basic CTE
WITH active AS (SELECT * FROM users WHERE status = 'active')
SELECT department, COUNT(*) FROM active GROUP BY ALL;

-- Multiple CTEs
WITH
  recent AS (SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAY),
  summary AS (SELECT customer_id, SUM(amount) AS total FROM recent GROUP BY customer_id)
SELECT u.name, s.total FROM users u JOIN summary s ON u.id = s.customer_id;

-- Recursive CTE
WITH RECURSIVE counter(n) AS (
    SELECT 1 UNION ALL SELECT n + 1 FROM counter WHERE n < 10
)
SELECT * FROM counter;
```

---

## CREATE TABLE, INSERT, COPY

```sql
-- Standard CREATE
CREATE TABLE events (
    id INTEGER PRIMARY KEY, name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT current_timestamp, tags VARCHAR[], metadata JSON
);

-- CTAS
CREATE TABLE summary AS SELECT category, SUM(sales) AS total FROM raw_data GROUP BY ALL;

-- CREATE OR REPLACE
CREATE OR REPLACE TABLE staging AS SELECT * FROM read_parquet('s3://bucket/*.parquet');

-- INSERT
INSERT INTO events (name, tags) VALUES ('click', ['ui', 'button']);
INSERT INTO archive SELECT * FROM events WHERE created_at < '2023-01-01';

-- COPY (export)
COPY (SELECT * FROM events) TO 'events.parquet' (FORMAT PARQUET);
COPY (SELECT * FROM events) TO 'events.csv' (HEADER, DELIMITER ',');
```

---

## Useful Patterns

### Deduplication with QUALIFY

```sql
SELECT *
FROM raw_events
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at DESC) = 1;
```

### Lateral Join (correlated subquery as table)

```sql
SELECT o.order_id, t.item
FROM orders o, LATERAL UNNEST(o.items) AS t(item);
```

### Sampling

```sql
SELECT * FROM large_table USING SAMPLE 1000;          -- 1000 rows
SELECT * FROM large_table USING SAMPLE 10 PERCENT;    -- 10% of rows
```

### String aggregation with ordering

```sql
SELECT department, string_agg(name, ', ' ORDER BY name) AS members
FROM employees
GROUP BY department;
```

### Generate date series for gap-filling

```sql
WITH dates AS (
    SELECT UNNEST(generate_series(DATE '2023-01-01', DATE '2023-12-31', INTERVAL 1 DAY)) AS dt
)
SELECT d.dt, COALESCE(e.count, 0) AS event_count
FROM dates d
LEFT JOIN (SELECT date_trunc('day', created_at) AS dt, COUNT(*) AS count FROM events GROUP BY 1) e
ON d.dt = e.dt;
```
