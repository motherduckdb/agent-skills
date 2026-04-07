select
  cast(customer_id as varchar) as customer_id,
  cast(customer_name as varchar) as customer_name,
  cast(segment as varchar) as segment,
  cast(region as varchar) as region
from {{ source("raw", "customers_raw") }}
