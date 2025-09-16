import mysql.connector
import os

# DB config
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "mini_browser")

# Connect to DB
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
)

cursor = conn.cursor()

# Get all tables
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()

for (table_name,) in tables:
    print(f"\nData from table `{table_name}`:")
    cursor.execute(f"SELECT * FROM `{table_name}`;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No data found.")

# Close connection
cursor.close()
conn.close()
