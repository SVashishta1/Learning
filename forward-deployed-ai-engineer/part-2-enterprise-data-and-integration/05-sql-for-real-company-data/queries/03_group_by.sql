-- 03_group_by.sql: GROUP BY, aggregate functions, HAVING. Works in SQLite and PostgreSQL.

-- Tickets per category AS TYPED: look how messy it is (16 spellings plus NULL, for 5 real categories)
SELECT category, COUNT(*) AS tickets
FROM tickets
GROUP BY category
ORDER BY tickets DESC;

-- Customers per country as typed
SELECT country, COUNT(*) AS customers
FROM customers
GROUP BY country
ORDER BY country;

-- Destinations with more than 100,000 EUR of shipments (HAVING filters groups; WHERE filters rows)
SELECT destination,
       COUNT(*)                AS shipments,
       ROUND(SUM(price_eur), 0) AS revenue_eur,
       ROUND(AVG(weight_kg), 1) AS avg_weight_kg
FROM shipments
WHERE weight_kg > 0
GROUP BY destination
HAVING SUM(price_eur) > 100000
ORDER BY revenue_eur DESC;
