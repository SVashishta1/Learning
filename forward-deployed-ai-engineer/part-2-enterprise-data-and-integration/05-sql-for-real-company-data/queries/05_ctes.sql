-- 05_ctes.sql: WITH (common table expressions): name a step, then build on it. Works in SQLite and PostgreSQL.

-- Lesson 02 question: is "where is my shipment?" really about 40% of tickets?
WITH clean_tickets AS (
    SELECT ticket_id,
           CASE
               WHEN LOWER(TRIM(category)) IN ('wismo', 'where is my shipment') THEN 'wismo'
               WHEN LOWER(TRIM(category)) IN ('damage', 'damaged')             THEN 'damage'
               WHEN LOWER(TRIM(category)) IN ('invoice', 'billing')            THEN 'invoice'
               WHEN LOWER(TRIM(category)) IN ('address change', 'address')     THEN 'address_change'
               WHEN LOWER(TRIM(category)) IN ('other', 'general')              THEN 'other'
               WHEN category IS NULL AND (LOWER(subject) LIKE '%where is%' OR LOWER(subject) LIKE '%not arrived%'
                    OR LOWER(subject) LIKE '%tracking%' OR LOWER(subject) LIKE '%delivery status%') THEN 'wismo'
               WHEN category IS NULL AND (LOWER(subject) LIKE '%damage%' OR LOWER(subject) LIKE '%crushed%') THEN 'damage'
               WHEN category IS NULL AND (LOWER(subject) LIKE '%invoice%' OR LOWER(subject) LIKE '%charged%') THEN 'invoice'
               WHEN category IS NULL AND LOWER(subject) LIKE '%address%'       THEN 'address_change'
               ELSE 'other'
           END AS category
    FROM tickets
),
totals AS (
    SELECT COUNT(*) AS all_tickets FROM clean_tickets
)
SELECT c.category,
       COUNT(*)                                    AS tickets,
       ROUND(100.0 * COUNT(*) / t.all_tickets, 1)  AS percent
FROM clean_tickets AS c
CROSS JOIN totals AS t
GROUP BY c.category, t.all_tickets
ORDER BY tickets DESC;

-- Which customers send the most WISMO tickets per shipment? (two steps, each with a name)
WITH wismo_per_customer AS (
    SELECT customer_id, COUNT(*) AS wismo_tickets
    FROM tickets
    WHERE LOWER(TRIM(category)) IN ('wismo', 'where is my shipment')
    GROUP BY customer_id
),
shipments_per_customer AS (
    SELECT customer_id, COUNT(*) AS shipments
    FROM shipments
    GROUP BY customer_id
)
SELECT c.name,
       w.wismo_tickets,
       s.shipments,
       ROUND(1.0 * w.wismo_tickets / s.shipments, 2) AS tickets_per_shipment
FROM wismo_per_customer AS w
JOIN shipments_per_customer AS s ON s.customer_id = w.customer_id
JOIN customers AS c ON c.customer_id = w.customer_id
WHERE s.shipments >= 20
ORDER BY tickets_per_shipment DESC, c.name
LIMIT 5;
