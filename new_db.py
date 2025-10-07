import sqlite3

conn = sqlite3.connect('books.db')
c = conn.cursor()

c.execute("""
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    description TEXT,
    genre TEXT,
    user_email TEXT NOT NULL,
    review TEXT,
    thumbnail TEXT
)
""")

conn.commit()
conn.close()

print("✅ New database and table created successfully!")
