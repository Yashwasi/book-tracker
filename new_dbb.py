import sqlite3

conn = sqlite3.connect('books.db')
cursor = conn.cursor()

# Add the new column "notes"
cursor.execute("ALTER TABLE books ADD COLUMN notes TEXT")

conn.commit()
conn.close()

print("✅ Notes column added successfully.")
