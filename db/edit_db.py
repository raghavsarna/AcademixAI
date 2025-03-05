import sqlite3

conn = sqlite3.connect("research.db")
cursor = conn.cursor()

# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# print("Tables in database:", cursor.fetchall())

# cursor.execute("SELECT * FROM newsletter;")
cursor.execute('''SELECT picture FROM newsletter;''')

print(cursor.fetchall())

conn.close()
