-- 06_window_functions.sql: ROW_NUMBER, LAG, running totals, RANK. Works in SQLite (3.25+) and PostgreSQL.
-- A window function looks at a "window" of related rows WITHOUT squashing them into one row like GROUP BY does.

-- The latest scan of each shipment (number the scans newest-first per shipment, keep number 1)
WITH numbered AS (
    SELECT shipment_id, scanned_at, location, event,
           ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY scanned_at DESC) AS rn
    FROM scans
)
SELECT shipment_id, scanned_at AS last_scan, location, event
FROM numbered
WHERE rn = 1
ORDER BY shipment_id
LIMIT 5;

-- Every scan of one shipment, next to the previous scan's time (LAG looks one row back)
SELECT shipment_id, event, location, scanned_at,
       LAG(scanned_at) OVER (PARTITION BY shipment_id ORDER BY scanned_at) AS previous_scan
FROM scans
WHERE shipment_id = (SELECT MIN(shipment_id) FROM shipments WHERE delivered_at IS NOT NULL)
ORDER BY scanned_at;

-- Tickets per month, with a running total (SUM over all months so far)
SELECT SUBSTR(created_at, 1, 7) AS month,
       COUNT(*) AS tickets,
       SUM(COUNT(*)) OVER (ORDER BY SUBSTR(created_at, 1, 7)) AS running_total
FROM tickets
GROUP BY SUBSTR(created_at, 1, 7)
ORDER BY month;

-- Top 5 customers by invoiced amount, ranked (RANK gives ties the same place)
SELECT c.name,
       ROUND(SUM(i.amount_eur), 0) AS invoiced_eur,
       RANK() OVER (ORDER BY SUM(i.amount_eur) DESC) AS place
FROM invoices AS i
JOIN customers AS c ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name
ORDER BY place
LIMIT 5;
