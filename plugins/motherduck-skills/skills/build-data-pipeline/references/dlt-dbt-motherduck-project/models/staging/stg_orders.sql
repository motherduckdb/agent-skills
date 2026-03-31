with ranked_orders as (
    select
        cast(order_id as varchar) as order_id,
        cast(customer_id as varchar) as customer_id,
        cast(order_date as date) as order_date,
        upper(trim(cast(status as varchar))) as status,
        cast(amount as decimal(18,2)) as amount,
        cast(updated_at as timestamp) as updated_at,
        row_number() over (
            partition by cast(order_id as varchar)
            order by cast(updated_at as timestamp) desc
        ) as row_num
    from {{ source("raw", "orders_raw") }}
)

select
    order_id,
    customer_id,
    order_date,
    status,
    amount,
    updated_at
from ranked_orders
where row_num = 1
  and status = 'PAID'
