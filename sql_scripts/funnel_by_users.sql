-- воронка по пользователям
with first_events as (
    select 
        user_id,
        min(case when event_type = 'view'        then event_timestamp end) as first_view,
        min(case when event_type = 'add_to_cart' then event_timestamp end) as first_add_to_cart,
        min(case when event_type = 'checkout'    then event_timestamp end) as first_checkout,
        min(case when event_type = 'purchase'    then event_timestamp end) as first_purchase
    from events
    group by user_id
)


select 
    count(*) filter (
        where first_view is not null 
    ) as step1_view,
    
    count(*) filter (
        where first_view        is not null
          and first_add_to_cart is not null 
          and first_view        < first_add_to_cart
    ) as step2_add_to_cart,
    
    count(*) filter (
        where first_view        is not null
          and first_add_to_cart is not null 
          and first_checkout    is not null 
          and first_view        < first_add_to_cart
          and first_add_to_cart < first_checkout
    ) as step3_checkout,
    
    count(*) filter (
        where first_view        is not null
          and first_add_to_cart is not null 
          and first_checkout    is not null
          and first_purchase    is not null
          and first_view        < first_add_to_cart
          and first_add_to_cart < first_checkout
          and first_checkout    < first_purchase
    ) as step4_purchase


from first_events;

---

with first_events as (
    select 
        user_id,
        min(case when event_type = 'view'        then event_timestamp end) as first_view,
        min(case when event_type = 'add_to_cart' then event_timestamp end) as first_add_to_cart,
        min(case when event_type = 'checkout'    then event_timestamp end) as first_checkout,
        min(case when event_type = 'purchase'    then event_timestamp end) as first_purchase
    from events
    group by user_id
),

steps as (
	
	select 
	    count(*) filter (
	        where first_view is not null 
	    ) as step1_view,
	    
	    count(*) filter (
	        where first_view        is not null
	          and first_add_to_cart is not null 
	          and first_view        < first_add_to_cart
	    ) as step2_add_to_cart,
	    
	    count(*) filter (
	        where first_view        is not null
	          and first_add_to_cart is not null 
	          and first_checkout    is not null 
	          and first_view        < first_add_to_cart
	          and first_add_to_cart < first_checkout
	    ) as step3_checkout,
	    
	    count(*) filter (
	        where first_view        is not null
	          and first_add_to_cart is not null 
	          and first_checkout    is not null
	          and first_purchase    is not null
	          and first_view        < first_add_to_cart
	          and first_add_to_cart < first_checkout
	          and first_checkout    < first_purchase
	    ) as step4_purchase


	from first_events

)

select 
    round(100.0 * step2_add_to_cart / step1_view, 2)        as view_to_cart_cr,
    round(100.0 * step3_checkout    / step2_add_to_cart, 2) as cart_to_checkout_cr,
    round(100.0 * step4_purchase    / step3_checkout, 2)    as checkout_to_purchase_cr,
    round(100.0 * step4_purchase    / step1_view, 2)        as view_to_purchase_cr
from steps;


