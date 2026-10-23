-- 01_first_look.sql: SELECT, FROM, WHERE, ORDER BY, LIMIT, COUNT. Works in SQLite and PostgreSQL.

-- How many rows are in each table?
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'shipments', COUNT(*) FROM shipments
UNION ALL SELECT 'scans', COUNT(*) FROM scans
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'invoices', COUNT(*) FROM invoices;

-- The 5 newest tickets
SELECT ticket_id, created_at, category, subject
FROM tickets
ORDER BY created_at DESC
LIMIT 5;

-- How many tickets have no category? (NULL means "no value at all"; test it with IS NULL, never = NULL)
SELECT COUNT(*) AS tickets_without_category
FROM tickets
WHERE category IS NULL;

-- Delayed shipments going to Utrecht, earliest promise first
SELECT shipment_id, destination, promised_date, status
FROM shipments
WHERE status = 'delayed' AND destination = 'Utrecht'
ORDER BY promised_date
LIMIT 5;
