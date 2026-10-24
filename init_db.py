
import sqlite3

# Connect to the database
conn = sqlite3.connect('students.db')
cursor = conn.cursor()

# Create the students table
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL
)
''')

# Clear existing records
cursor.execute("DELETE FROM students")

# Five sample student records
students = [
    ('2026-00123', 'Adrian Bunayos', 'BSIT', 3, 'A'),
    ('2026-00124', 'Neca Mae Herbaliga', 'BSIT', 3, 'B'),
    ('2026-00125', 'Pedro Reyes', 'BSIT', 2, 'A'),
    ('2026-00126', 'Ana Garcia', 'BSIT', 3, 'B'),
    ('2026-00127', 'Mark Villanueva', 'BSIT', 4, 'A')
]

# Insert student records into the database
cursor.executemany('''
INSERT INTO students (student_id, name, program, year, section)
VALUES (?, ?, ?, ?, ?)
''', students)

# Save changes and close the database
conn.commit()
conn.close()

print("Database created successfully!")
print("5 student records inserted successfully.")
