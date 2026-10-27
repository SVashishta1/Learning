-- postgres_examples.sql: PostgreSQL-only versions of 08_response_times.sql.
-- Run with: python run_sql.py queries/postgres_examples.sql --postgres postgresql://localhost/northwind

-- Median first response time per raw category spelling for WISMO, using PostgreSQL's built-in percentile function
SELECT CASE WHEN LOWER(TRIM(category)) IN ('wismo', 'where is my shipment') THEN 'wismo' ELSE 'not wismo' END AS kind,
       COUNT(*) AS answered_tickets,
       ROUND(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (
           ORDER BY EXTRACT(EPOCH FROM (first_response_at::timestamp - created_at::timestamp)) / 3600
       ) AS NUMERIC), 1) AS median_hours
FROM tickets
WHERE first_response_at IS NOT NULL
GROUP BY 1
ORDER BY 1 DESC;

-- Share answered within 8 hours, with FILTER (a PostgreSQL shortcut for SUM(CASE ...))
SELECT COUNT(*) AS answered,
       COUNT(*) FILTER (WHERE first_response_at::timestamp - created_at::timestamp <= INTERVAL '8 hours') AS within_8h
FROM tickets
WHERE first_response_at IS NOT NULL;
