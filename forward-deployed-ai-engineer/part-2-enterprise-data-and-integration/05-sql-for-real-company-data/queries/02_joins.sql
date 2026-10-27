-- 02_joins.sql: combining tables with JOIN and LEFT JOIN. Works in SQLite and PostgreSQL.

-- Each ticket with its customer's name (INNER JOIN keeps only rows that match on both sides)
SELECT t.ticket_id, c.name AS customer, t.subject
FROM tickets AS t
JOIN customers AS c ON c.customer_id = t.customer_id
ORDER BY t.ticket_id
LIMIT 5;

-- Tickets that mention a tracking number that does NOT exist (LEFT JOIN keeps every ticket; no match gives NULLs)
SELECT t.ticket_id, t.shipment_id AS typed_tracking_number, t.subject
FROM tickets AS t
LEFT JOIN shipments AS s ON s.shipment_id = t.shipment_id
WHERE t.shipment_id IS NOT NULL
  AND s.shipment_id IS NULL
ORDER BY t.ticket_id
LIMIT 5;

-- Three tables: delayed shipments that caused a ticket, with the customer's name
SELECT t.ticket_id, c.name AS customer, s.shipment_id, s.status, s.promised_date
FROM tickets AS t
JOIN shipments AS s ON s.shipment_id = t.shipment_id
JOIN customers AS c ON c.customer_id = s.customer_id
WHERE s.status = 'delayed'
ORDER BY s.promised_date, t.ticket_id
LIMIT 5;
