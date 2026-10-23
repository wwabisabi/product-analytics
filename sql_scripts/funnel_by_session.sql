-- воронка по сессиям

-- 1. cама воронка (абсолютные числа)

WITH first_events AS (
    SELECT 
        user_id,
        session_id,
        MIN(CASE WHEN event_type = 'view'        THEN event_timestamp END) AS first_view,
        MIN(CASE WHEN event_type = 'add_to_cart' THEN event_timestamp END) AS first_add_to_cart,
        MIN(CASE WHEN event_type = 'checkout'    THEN event_timestamp END) AS first_checkout,
        MIN(CASE WHEN event_type = 'purchase'    THEN event_timestamp END) AS first_purchase
    FROM events
    GROUP BY user_id, session_id
)

SELECT 
    COUNT(*) FILTER (
        WHERE first_view IS NOT NULL 
    ) AS step1_view,
    
    COUNT(*) FILTER (
        WHERE first_view        IS NOT NULL
          AND first_add_to_cart IS NOT NULL 
          AND first_view        < first_add_to_cart
    ) AS step2_add_to_cart,
    
    COUNT(*) FILTER (
        WHERE first_view        IS NOT NULL
          AND first_add_to_cart IS NOT NULL 
          AND first_checkout    IS NOT NULL 
          AND first_view        < first_add_to_cart
          AND first_add_to_cart < first_checkout
    ) AS step3_checkout,
    
    COUNT(*) FILTER (
        WHERE first_view        IS NOT NULL
          AND first_add_to_cart IS NOT NULL 
          AND first_checkout    IS NOT NULL
          AND first_purchase    IS NOT NULL
          AND first_view        < first_add_to_cart
          AND first_add_to_cart < first_checkout
          AND first_checkout    < first_purchase
    ) AS step4_purchase

FROM first_events;

---

-- 2. конверсии (проценты)

WITH first_events AS (
    SELECT 
        user_id,
        session_id,
        MIN(CASE WHEN event_type = 'view'        THEN event_timestamp END) AS first_view,
        MIN(CASE WHEN event_type = 'add_to_cart' THEN event_timestamp END) AS first_add_to_cart,
        MIN(CASE WHEN event_type = 'checkout'    THEN event_timestamp END) AS first_checkout,
        MIN(CASE WHEN event_type = 'purchase'    THEN event_timestamp END) AS first_purchase
    FROM events
    GROUP BY user_id, session_id
),

steps AS (
    SELECT 
        COUNT(*) FILTER (
            WHERE first_view IS NOT NULL 
        ) AS step1_view,
        
        COUNT(*) FILTER (
            WHERE first_view        IS NOT NULL
              AND first_add_to_cart IS NOT NULL 
              AND first_view        < first_add_to_cart
        ) AS step2_add_to_cart,
        
        COUNT(*) FILTER (
            WHERE first_view        IS NOT NULL
              AND first_add_to_cart IS NOT NULL 
              AND first_checkout    IS NOT NULL 
              AND first_view        < first_add_to_cart
              AND first_add_to_cart < first_checkout
        ) AS step3_checkout,
        
        COUNT(*) FILTER (
            WHERE first_view        IS NOT NULL
              AND first_add_to_cart IS NOT NULL 
              AND first_checkout    IS NOT NULL
              AND first_purchase    IS NOT NULL
              AND first_view        < first_add_to_cart
              AND first_add_to_cart < first_checkout
              AND first_checkout    < first_purchase
        ) AS step4_purchase
    FROM first_events
)

SELECT 
    ROUND(100.0 * step2_add_to_cart / NULLIF(step1_view, 0), 2)        AS view_to_cart_cr,
    ROUND(100.0 * step3_checkout    / NULLIF(step2_add_to_cart, 0), 2) AS cart_to_checkout_cr,
    ROUND(100.0 * step4_purchase    / NULLIF(step3_checkout, 0), 2)    AS checkout_to_purchase_cr,
    ROUND(100.0 * step4_purchase    / NULLIF(step1_view, 0), 2)        AS view_to_purchase_cr
FROM steps;