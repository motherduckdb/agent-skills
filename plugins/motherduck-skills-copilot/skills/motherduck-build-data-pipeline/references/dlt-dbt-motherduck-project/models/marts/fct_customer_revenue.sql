select
  customers.customer_id,
  customers.customer_name,
  customers.segment,
  customers.region,
  count(orders.order_id) as order_count,
  sum(orders.amount) as total_amount,
  max(orders.order_date) as last_order_date
from {{ ref("stg_customers") }} as customers
join {{ ref("stg_orders") }} as orders
  on customers.customer_id = orders.customer_id
group by 1, 2, 3, 4
