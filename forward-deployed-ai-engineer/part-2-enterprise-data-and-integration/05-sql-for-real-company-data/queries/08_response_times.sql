-- 08_response_times.sql: median first response time per category, and the 8-hour contract promise.
-- SQLite only (julianday is SQLite's date maths). The PostgreSQL version is in postgres_examples.sql.

-- Median first response time per category (short cleaning: empty categories count as 'other')
WITH clean AS (
    SELECT CASE
               WHEN LOWER(TRIM(category)) IN ('wismo', 'where is my shipment') THEN 'wismo'
               WHEN LOWER(TRIM(category)) IN ('damage', 'damaged')             THEN 'damage'
               WHEN LOWER(TRIM(category)) IN ('invoice', 'billing')            THEN 'invoice'
               WHEN LOWER(TRIM(category)) IN ('address change', 'address')     THEN 'address_change'
               ELSE 'other'
           END AS category,
           (julianday(first_response_at) - julianday(created_at)) * 24 AS hours   -- days * 24 = hours
    FROM tickets
    WHERE first_response_at IS NOT NULL
),
ranked AS (
    SELECT category, hours,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY hours) AS rn,   -- position from fastest
           COUNT(*)     OVER (PARTITION BY category)                AS n     -- tickets in the category
    FROM clean
)
SELECT category,
       MAX(n) AS answered_tickets,
       ROUND(AVG(hours), 1) AS median_hours        -- the middle row (or the average of the two middle rows)
FROM ranked
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY category
ORDER BY median_hours DESC;

-- Share of answered tickets that met the 8-hour contract promise
SELECT COUNT(*) AS answered,
       SUM(CASE WHEN (julianday(first_response_at) - julianday(created_at)) * 24 <= 8 THEN 1 ELSE 0 END) AS within_8h,
       ROUND(100.0 * SUM(CASE WHEN (julianday(first_response_at) - julianday(created_at)) * 24 <= 8
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS percent_within_8h
FROM tickets
WHERE first_response_at IS NOT NULL;
