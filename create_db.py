import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("sales.db")


def main() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                city TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                order_date TEXT NOT NULL
            );

            INSERT OR REPLACE INTO customers (id, name, email, city)
            VALUES
                (1, 'Aarav Sharma', 'aarav.sharma@example.com', 'Mumbai'),
                (2, 'Diya Patel', 'diya.patel@example.com', 'Delhi'),
                (3, 'Arjun Reddy', 'arjun.reddy@example.com', 'Bangalore'),
                (4, 'Ananya Iyer', 'ananya.iyer@example.com', 'Chennai'),
                (5, 'Vivaan Rao', 'vivaan.rao@example.com', 'Hyderabad');

            INSERT OR REPLACE INTO orders
                (id, customer_id, product, amount, order_date)
            VALUES
                (1, 1, 'Laptop', 64999.00, '2025-01-12'),
                (2, 1, 'Phone', 24999.00, '2025-01-20'),
                (3, 2, 'Tablet', 32999.00, '2025-02-03'),
                (4, 2, 'Phone', 18999.00, '2025-02-11'),
                (5, 3, 'Laptop', 72999.00, '2025-02-18'),
                (6, 3, 'Tablet', 27999.00, '2025-03-01'),
                (7, 4, 'Phone', 31999.00, '2025-03-09'),
                (8, 4, 'Laptop', 58999.00, '2025-03-17'),
                (9, 5, 'Tablet', 35999.00, '2025-04-02'),
                (10, 5, 'Phone', 21999.00, '2025-04-14');
            """
        )
    print(f"Sales database created successfully: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
