
import sqlite3

# Connect to the database
conn = sqlite3.connect('students.db')
cursor = conn.cursor()

# Create the students table if it does not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL,
    source TEXT DEFAULT 'Local'
)
''')

# Check existing table columns
cursor.execute("PRAGMA table_info(students)")
columns = [column[1] for column in cursor.fetchall()]

# Add source column if it does not exist
if 'source' not in columns:
    cursor.execute("""
        ALTER TABLE students
        ADD COLUMN source TEXT DEFAULT 'Local'
    """)
    print("Source column added successfully!")

# Clear existing records
cursor.execute("DELETE FROM students")

# Reset auto-increment counter
cursor.execute("DELETE FROM sqlite_sequence WHERE name='students'")

# Five sample student records
students = [
    ('2026-00123', 'Adrian Bunayos', 'BSIT', 3, 'A', 'Local'),
    ('2026-00124', 'Neca Mae Herbaliga', 'BSIT', 3, 'B', 'Local'),
    ('2026-00125', 'Pedro Reyes', 'BSIT', 2, 'A', 'Local'),
    ('2026-00126', 'Ana Garcia', 'BSIT', 3, 'B', 'Local'),
    ('2026-00127', 'Mark Villanueva', 'BSIT', 4, 'A', 'Local')
]

# Insert student records
cursor.executemany('''
INSERT INTO students
(student_id, name, program, year, section, source)
VALUES (?, ?, ?, ?, ?, ?)
''', students)

# Save and close database
conn.commit()
conn.close()

print("Database created successfully!")
print("5 local student records inserted successfully.")
