with user_purchases as (

	-- все месяцы, в которые пользователь совершал успешные покупки
	select distinct
		o.user_id,
		(date_trunc('month', o.order_date))::date as purchase_month
	from orders o
	where o.order_status = 'completed'
),

first_purchase as (

	-- месяц первой покупки (когорта) для каждого пользователя
	select
		user_id,
		min(purchase_month) as cohort_month
	from user_purchases
	group by user_id
),

cohort_activity as (

	-- для каждой покупки: когорта + номер месяца с момента первой покупки
	select
		f.cohort_month,
		p.user_id,
		(extract(year from p.purchase_month) * 12 + extract(month from p.purchase_month))
		- (extract(year from f.cohort_month) * 12 + extract(month from f.cohort_month)) as month_number
	from user_purchases p
	join first_purchase f on f.user_id = p.user_id
),

cohort_sizes as (

	-- общий размер каждой когорты (база для процентов)
	select
		cohort_month,
		count(distinct user_id) as total_users
	from cohort_activity
	where month_number = 0
	group by cohort_month
),

retention as (

	-- сколько уникальных пользователей вернулось за покупкой в месяц N
	select
		cohort_month,
		month_number,
		count(distinct user_id) as active_users
	from cohort_activity
	group by cohort_month, month_number
)

select 
	r.cohort_month as cohort_date,
	s.total_users,
	
	-- m0 (месяц первой покупки)
	round(100.0 * max(case when r.month_number = 0 then r.active_users else 0 end) / s.total_users, 1) as m0,
	-- m1
	round(100.0 * max(case when r.month_number = 1 then r.active_users else 0 end) / s.total_users, 1) as m1,
	-- m2
	round(100.0 * max(case when r.month_number = 2 then r.active_users else 0 end) / s.total_users, 1) as m2,
	-- m3
	round(100.0 * max(case when r.month_number = 3 then r.active_users else 0 end) / s.total_users, 1) as m3,
	-- m4
	round(100.0 * max(case when r.month_number = 4 then r.active_users else 0 end) / s.total_users, 1) as m4,
	-- m5
	round(100.0 * max(case when r.month_number = 5 then r.active_users else 0 end) / s.total_users, 1) as m5
	
from retention r
join cohort_sizes s on s.cohort_month = r.cohort_month
group by r.cohort_month, s.total_users
order by r.cohort_month