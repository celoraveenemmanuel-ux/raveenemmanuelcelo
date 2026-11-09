
import requests
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATABASE = Path(__file__).resolve().parent / 'students.db'

# IMPORTANT: Replace this with your classmate's actual deployed API URL.
CLASSMATE_API = "https://labrador-clark.onrender.com/api/students"


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# INITIALIZE DATABASE
def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# VALIDATE STUDENT DATA
def validate_student_data(data):
    if not isinstance(data, dict):
        return "Invalid JSON data."

    fields = ['student_id', 'name', 'program', 'year', 'section']

    for field in fields:
        if field not in data or str(data[field]).strip() == '':
            return f'{field} is required.'

    try:
        year = int(data['year'])
        if year < 1:
            return 'Year must be a positive number.'
    except (ValueError, TypeError):
        return 'Year must be a valid number.'

    return None


# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')


# SINGLE STUDENT INFORMATION
@app.route('/student', methods=['GET'])
def get_student():
    return jsonify({
        "student_id": "24-00194",
        "name": "Raveen Emmanuel Celo",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# GREETING API
@app.route('/hello', methods=['GET'])
def say_hello():
    name = request.args.get('name', 'Student')

    return jsonify({
        "message": f"Hello, {name}!"
    })


# MOTORCYCLE API
@app.route('/motorcycle', methods=['GET'])
def get_motorcycle():
    return jsonify({
        "motorcycle_name": "Honda Click 125i",
        "brand": "Honda",
        "engine_cc": 125,
        "price": 79900,
        "available": True
    })


# GET ALL STUDENTS
@app.route('/students', methods=['GET'])
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students ORDER BY id DESC'
        ).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET STUDENT BY DATABASE ID
@app.route('/students/<int:id>', methods=['GET'])
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            'SELECT * FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found."}), 404

        return jsonify(dict(student))

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET STUDENTS BY YEAR LEVEL
@app.route('/students/year/<int:year>', methods=['GET'])
def get_students_by_year(year):
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students WHERE year = ? ORDER BY id DESC',
            (year,)
        ).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# ADD STUDENT
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            int(data['year']),
            data['section'].strip()
        ))

        conn.commit()

        return jsonify({
            "message": "Student added successfully!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# UPDATE STUDENT
@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            'SELECT id FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            int(data['year']),
            data['section'].strip(),
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully!"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# DELETE STUDENT
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            'DELETE FROM students WHERE id = ?',
            (id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully!"
        })

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# STEP 8: GET CLASSMATE'S STUDENT RECORDS
@app.route('/classmate-records', methods=['GET'])
def get_classmate_students():
    try:
        response = requests.get(CLASSMATE_API, timeout=30)
        response.raise_for_status()

        records = response.json()

        if not isinstance(records, list):
            return jsonify({
                "error": "Classmate API did not return a list of student records."
            }), 502

        return jsonify(records)

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Classmate API request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to connect to classmate API.",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Classmate API returned invalid JSON."
        }), 502


# JSON ERROR FOR UNKNOWN API ROUTES
@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "API endpoint not found."}), 404

    return "Page not found.", 404


# RUN APPLICATION
if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)

import requests
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATABASE = Path(__file__).resolve().parent / 'students.db'

# IMPORTANT: Replace this with your classmate's actual deployed API URL.
CLASSMATE_API = "https://CLASSMATE-APP.onrender.com/api/students"


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# INITIALIZE DATABASE
def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# VALIDATE STUDENT DATA
def validate_student_data(data):
    if not isinstance(data, dict):
        return "Invalid JSON data."

    fields = ['student_id', 'name', 'program', 'year', 'section']

    for field in fields:
        if field not in data or str(data[field]).strip() == '':
            return f'{field} is required.'

    try:
        year = int(data['year'])
        if year < 1:
            return 'Year must be a positive number.'
    except (ValueError, TypeError):
        return 'Year must be a valid number.'

    return None


# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')


# SINGLE STUDENT INFORMATION
@app.route('/student', methods=['GET'])
def get_student():
    return jsonify({
        "student_id": "24-00194",
        "name": "Raveen Emmanuel Celo",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# GREETING API
@app.route('/hello', methods=['GET'])
def say_hello():
    name = request.args.get('name', 'Student')

    return jsonify({
        "message": f"Hello, {name}!"
    })


# MOTORCYCLE API
@app.route('/motorcycle', methods=['GET'])
def get_motorcycle():
    return jsonify({
        "motorcycle_name": "Honda Click 125i",
        "brand": "Honda",
        "engine_cc": 125,
        "price": 79900,
        "available": True
    })


# GET ALL STUDENTS
@app.route('/students', methods=['GET'])
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students ORDER BY id DESC'
        ).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET STUDENT BY DATABASE ID
@app.route('/students/<int:id>', methods=['GET'])
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            'SELECT * FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found."}), 404

        return jsonify(dict(student))

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET STUDENTS BY YEAR LEVEL
@app.route('/students/year/<int:year>', methods=['GET'])
def get_students_by_year(year):
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students WHERE year = ? ORDER BY id DESC',
            (year,)
        ).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# ADD STUDENT
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            int(data['year']),
            data['section'].strip()
        ))

        conn.commit()

        return jsonify({
            "message": "Student added successfully!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# UPDATE STUDENT
@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            'SELECT id FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            int(data['year']),
            data['section'].strip(),
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully!"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# DELETE STUDENT
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            'DELETE FROM students WHERE id = ?',
            (id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully!"
        })

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# STEP 8: GET CLASSMATE'S STUDENT RECORDS
@app.route('/classmate-records', methods=['GET'])
def get_classmate_students():
    try:
        response = requests.get(CLASSMATE_API, timeout=30)
        response.raise_for_status()

        records = response.json()

        if not isinstance(records, list):
            return jsonify({
                "error": "Classmate API did not return a list of student records."
            }), 502

        return jsonify(records)

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Classmate API request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to connect to classmate API.",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Classmate API returned invalid JSON."
        }), 502


# JSON ERROR FOR UNKNOWN API ROUTES
@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "API endpoint not found."}), 404

    return "Page not found.", 404


# RUN APPLICATION
if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
