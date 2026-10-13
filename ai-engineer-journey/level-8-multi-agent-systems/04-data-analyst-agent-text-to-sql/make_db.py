"""Builds shop.db: a small online shop with customers, products, orders and order_items (about 2,000 orders)."""
import random
import sqlite3
from datetime import date, timedelta


def build(path="shop.db", seed=4):
    rng = random.Random(seed)
    con = sqlite3.connect(path)
    con.executescript("""
    DROP TABLE IF EXISTS order_items; DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS products; DROP TABLE IF EXISTS customers;
    CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT, signup_date TEXT);
    CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
    CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), order_date TEXT, status TEXT);
    CREATE TABLE order_items (order_id INTEGER REFERENCES orders(id), product_id INTEGER REFERENCES products(id), quantity INTEGER);
    """)
    countries = ["India", "USA", "Germany", "Brazil", "UK", "Japan"]
    con.executemany("INSERT INTO customers VALUES (?,?,?,?)", [
        (i, f"Customer {i}", rng.choices(countries, [5, 4, 2, 2, 2, 1])[0], str(date(2025, 1, 1) + timedelta(rng.randint(0, 500))))
        for i in range(1, 401)])
    products = [("Wireless Mouse", "Electronics", 25), ("Mechanical Keyboard", "Electronics", 89), ("USB-C Hub", "Electronics", 39),
                ("Noise-Cancelling Headphones", "Electronics", 199), ("Desk Lamp", "Home", 35), ("Ergonomic Chair", "Home", 249),
                ("Standing Desk", "Home", 399), ("Python Crash Course", "Books", 32), ("Deep Learning Book", "Books", 55),
                ("Coffee Beans 1kg", "Grocery", 18), ("Green Tea", "Grocery", 9), ("Water Bottle", "Sports", 15)]
    con.executemany("INSERT INTO products VALUES (?,?,?,?)", [(i + 1, *p) for i, p in enumerate(products)])
    for oid in range(1, 2001):
        d = date(2026, 1, 1) + timedelta(rng.randint(0, 272))
        con.execute("INSERT INTO orders VALUES (?,?,?,?)", (oid, rng.randint(1, 400), str(d), rng.choices(["completed", "refunded", "cancelled"], [90, 6, 4])[0]))
        for pid in rng.sample(range(1, 13), rng.randint(1, 3)):
            con.execute("INSERT INTO order_items VALUES (?,?,?)", (oid, pid, rng.choices([1, 2, 3], [80, 15, 5])[0]))
    con.commit(); con.close()


if __name__ == "__main__":
    build()
    print("Built shop.db")
