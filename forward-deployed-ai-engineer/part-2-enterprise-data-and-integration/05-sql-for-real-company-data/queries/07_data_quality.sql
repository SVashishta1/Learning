-- 07_data_quality.sql: a data-quality report. Run this FIRST on any new customer database.
-- Each row is one check and how many rows fail it. Works in SQLite and PostgreSQL.

SELECT 'tickets without a category' AS check_name, COUNT(*) AS problem_rows
FROM tickets WHERE category IS NULL
UNION ALL
SELECT 'tickets pointing at a shipment that does not exist', COUNT(*)
FROM tickets AS t LEFT JOIN shipments AS s ON s.shipment_id = t.shipment_id
WHERE t.shipment_id IS NOT NULL AND s.shipment_id IS NULL
UNION ALL
SELECT 'tickets with no first response yet', COUNT(*)
FROM tickets WHERE first_response_at IS NULL
UNION ALL
SELECT 'shipments with weight zero or below', COUNT(*)
FROM shipments WHERE weight_kg <= 0
UNION ALL
SELECT 'promised dates not written as YYYY-MM-DD', COUNT(*)
FROM shipments WHERE promised_date NOT LIKE '____-__-__'
UNION ALL
SELECT 'status written in a non-standard way', COUNT(*)
FROM shipments WHERE status NOT IN ('delivered', 'in_transit', 'delayed')
UNION ALL
SELECT 'delivered time set but status is not delivered', COUNT(*)
FROM shipments WHERE delivered_at IS NOT NULL AND LOWER(TRIM(status)) NOT IN ('delivered', 'delivred')
UNION ALL
SELECT 'shipments invoiced more than once', COUNT(*)
FROM (SELECT shipment_id FROM invoices GROUP BY shipment_id HAVING COUNT(*) > 1) AS doubles
UNION ALL
SELECT 'customers that look like duplicates', COUNT(*)
FROM (SELECT TRIM(REPLACE(LOWER(name), ' b.v.', '')) AS k FROM customers GROUP BY 1 HAVING COUNT(*) > 1) AS dups
UNION ALL
SELECT 'customer emails not in lower case', COUNT(*)
FROM customers WHERE email <> LOWER(email);
