-- конверсия по товарам (от просмотра до покупки)

with events_with_product as (

	-- собираем события просмотра и корзины, где id товара уже есть
	select
		user_id,
		product_id,
		event_type,
		event_timestamp
	from events
	where event_type in ('view', 'add_to_cart')
	
	union all
	
	-- собираем события оформления и покупки, доставая id товара через позиции заказа
	select
		e.user_id,
		oi.product_id,
		e.event_type,
		e.event_timestamp
	from events e
	join order_items oi on oi.order_id = e.order_id 
	where e.event_type in ('checkout', 'purchase')
),

first_events as (

	-- первое время наступления каждого шага для пары (пользователь + товар)
	select
		user_id,
		product_id,
		min(case when event_type = 'view'        then event_timestamp end) as first_view,
		min(case when event_type = 'purchase'    then event_timestamp end) as first_purchase
	from events_with_product
	group by user_id, product_id

),

product_funnel as (

	-- считаем шаги воронки по каждому товару
	select
		product_id,
		count(*) filter (
			where first_view is not null 
		) as step1_view,
		
		count(*) filter (
			where first_view        is not null
			and first_purchase      is not null 
			and first_view          < first_purchase
		) as step2_purchase
	from first_events
	group by product_id

)

select 
	p.product_id,
	p.product_name,
	p.category,
	f.step1_view,
	f.step2_purchase,
	round(100.0 * f.step2_purchase / nullif(f.step1_view, 0), 2) as view_to_purchase_cr
from product_funnel f
join products p on p.product_id = f.product_id
where f.step1_view > 0
order by view_to_purchase_cr asc