-- информация о колонках
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'users',
      'products',
      'orders',
      'order_items',
      'events'
  )
ORDER BY
    table_name,
    ordinal_position;

-- кол-во пользователей и заказов
SELECT
    (SELECT COUNT(*) FROM users)  AS cnt_users,
    (SELECT COUNT(*) FROM orders) AS cnt_orders;

-- выручка
SELECT SUM(oi.quantity * oi.unit_price) AS gross_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'completed';

-- средний чек
WITH order_revenue AS (
    SELECT
        o.order_id,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'completed'
    GROUP BY o.order_id
)
SELECT
    SUM(revenue)           AS gross_revenue,
    COUNT(*)               AS completed_orders,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM order_revenue;

-- кол-во событий
select event_type, count(*) as cnt
from events
group by event_type 
order by cnt desc
