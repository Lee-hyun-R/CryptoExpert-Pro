import sqlite3

conn = sqlite3.connect("resources/test.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    cursor.execute(f"DELETE FROM {table_name}")
    print(f"Deleted all from {table_name}")

conn.commit()
conn.close()
print("Database cleared!")