-- 04_cleaning.sql: CASE, LOWER, TRIM, LIKE, SUBSTR, COALESCE. Works in SQLite and PostgreSQL.

-- Clean the ticket category: many spellings -> one name. Empty ones are guessed from the subject line.
SELECT
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
    END AS clean_category,
    COUNT(*) AS tickets
FROM tickets
GROUP BY 1
ORDER BY tickets DESC;

-- Clean the shipment status
SELECT
    CASE
        WHEN LOWER(TRIM(status)) IN ('delivered', 'delivred') THEN 'delivered'
        WHEN LOWER(TRIM(status)) IN ('in_transit', 'in transit') THEN 'in_transit'
        WHEN LOWER(TRIM(status)) = 'delayed' THEN 'delayed'
        ELSE 'unknown'
    END AS clean_status,
    COUNT(*) AS shipments
FROM shipments
GROUP BY 1
ORDER BY shipments DESC;

-- Clean the country into ISO codes
SELECT
    CASE UPPER(TRIM(country))
        WHEN 'NETHERLANDS' THEN 'NL'
        WHEN 'POLAND'      THEN 'PL'
        WHEN 'GERMANY'     THEN 'DE'
        WHEN 'BELGIUM'     THEN 'BE'
        WHEN 'FRANCE'      THEN 'FR'
        ELSE UPPER(TRIM(country))
    END AS country_code,
    COUNT(*) AS customers
FROM customers
GROUP BY 1
ORDER BY 1;

-- Customers per tier; a missing tier (NULL) is shown as 'unknown' with COALESCE (= "first value that is not NULL")
SELECT COALESCE(LOWER(tier), 'unknown') AS tier,
       COUNT(*) AS customers
FROM customers
GROUP BY 1
ORDER BY customers DESC;

-- Possible duplicate customers: same name after lower-casing, trimming and dropping ' B.V.'
SELECT TRIM(REPLACE(LOWER(name), ' b.v.', '')) AS name_key,
       COUNT(*)                                AS copies,
       MIN(customer_id)                        AS keep_id,
       MAX(customer_id)                        AS duplicate_id
FROM customers
GROUP BY 1
HAVING COUNT(*) > 1
ORDER BY 1
LIMIT 5;

-- Dates typed as DD/MM/YYYY, rewritten as YYYY-MM-DD ('_' in LIKE means "exactly one character")
SELECT shipment_id,
       promised_date AS as_typed,
       CASE
           WHEN promised_date LIKE '__/__/____'
           THEN SUBSTR(promised_date, 7, 4) || '-' || SUBSTR(promised_date, 4, 2) || '-' || SUBSTR(promised_date, 1, 2)
           ELSE promised_date
       END AS iso_date
FROM shipments
WHERE promised_date LIKE '__/__/____'
ORDER BY shipment_id
LIMIT 5;
