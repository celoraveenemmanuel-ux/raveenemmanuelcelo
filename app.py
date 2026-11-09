
import sqlite3
import requests
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = Path(__file__).resolve().parent / "students.db"

# Clark's deployed Student API
CLASSMATE_API = "https://labrador-clark.onrender.com/api/students"


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


# INITIALIZE DATABASE
def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(students)").fetchall()
    ]

    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT DEFAULT 'Local'
        """)

    conn.execute("""
        UPDATE students
        SET source = 'Local'
        WHERE source IS NULL OR TRIM(source) = ''
    """)

    conn.commit()
    conn.close()


initialize_database()


# VALIDATE STUDENT DATA
def validate_student_data(data):
    if not isinstance(data, dict):
        return "Invalid JSON data."

    fields = ["student_id", "name", "program", "year", "section"]

    for field in fields:
        if field not in data or str(data[field]).strip() == "":
            return f"{field} is required."

    try:
        year = int(data["year"])
    except (ValueError, TypeError):
        return "Year must be a valid number."

    if year < 1 or year > 4:
        return "Year must be between 1 and 4."

    return None


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# STUDENT INFORMATION API
@app.route("/student", methods=["GET"])
def get_student():
    return jsonify({
        "student_id": "2026-001",
        "name": "Raveen",
        "program": "BSIT",
        "year": 2,
        "section": "A"
    })


# GREETING API
@app.route("/hello", methods=["GET"])
def hello():
    name = request.args.get("name", "").strip()

    if name:
        return jsonify({
            "message": f"Hello, {name}! Welcome to Raveen's API."
        })

    return jsonify({
        "message": "Hello! Welcome to Raveen's Student API."
    })


# MOTORCYCLE API
@app.route("/motorcycle", methods=["GET"])
def motorcycle():
    return jsonify({
        "brand": "Honda",
        "model": "Click 125",
        "type": "Scooter"
    })


# GET ALL STUDENTS
@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# GET ONE STUDENT
@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
def get_one_student(id):
    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "Student not found."}), 404

    return jsonify(dict(student))


# SEARCH STUDENTS BY YEAR
@app.route("/students/year/<int:year>", methods=["GET"])
def get_students_by_year(year):
    if year < 1 or year > 4:
        return jsonify({"error": "Invalid year level."}), 400

    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students WHERE year = ? ORDER BY id DESC",
        (year,)
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ADD STUDENT / RECEIVE EXTERNAL STUDENT
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    source = str(data.get("source") or "External API").strip()

    if not source:
        source = "External API"

    student_id = data["student_id"].strip()

    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing:
            return jsonify({
                "error": "Student ID already exists in your database.",
                "student_id": student_id
            }), 409

        cursor = conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip(),
            source
        ))

        conn.commit()

        return jsonify({
            "message": "Student record successfully received and saved!",
            "id": cursor.lastrowid,
            "student_id": student_id,
            "source": source
        }), 201

    except sqlite3.Error as error:
        return jsonify({
            "error": "Database error.",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# UPDATE STUDENT
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "Student not found."}), 404

        duplicate = conn.execute("""
            SELECT id FROM students
            WHERE student_id = ? AND id != ?
        """, (data["student_id"].strip(), id)).fetchone()

        if duplicate:
            return jsonify({
                "error": "Student ID already belongs to another record."
            }), 409

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip(),
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully!"
        })

    except sqlite3.Error as error:
        return jsonify({
            "error": "Database error.",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# DELETE STUDENT
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "Student not found."}), 404

        conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully!"
        })

    except sqlite3.Error as error:
        return jsonify({
            "error": "Database error.",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# RETRIEVE CLARK'S RECORDS
@app.route("/classmate-records", methods=["GET"])
def get_classmate_students():
    try:
        response = requests.get(
            CLASSMATE_API,
            timeout=30
        )

        response.raise_for_status()
        records = response.json()

        if isinstance(records, dict):
            records = records.get(
                "students",
                records.get("data", records)
            )

        if not isinstance(records, list):
            return jsonify({
                "error": "Clark's API did not return a list of students.",
                "partner_response": records
            }), 502

        return jsonify(records)

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Clark's API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to connect to Clark's API.",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Clark's API returned invalid JSON."
        }), 502


# IMPORT CLARK'S SELECTED RECORD
@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True)
    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    student_id = data["student_id"].strip()
    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing:
            return jsonify({
                "error": "This student record already exists.",
                "student_id": student_id
            }), 409

        cursor = conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip(),
            "Classmate API"
        ))

        conn.commit()

        return jsonify({
            "message": "Clark's student record imported successfully!",
            "id": cursor.lastrowid,
            "student_id": student_id,
            "source": "Classmate API"
        }), 201

    except sqlite3.Error as error:
        return jsonify({
            "error": "Database error.",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# SEND A PRACTICE RECORD TO CLARK
# MATCHED WITH CLARK'S SEND-TO-PARTNER LOGIC
@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    record = request.get_json(silent=True)

    error = validate_student_data(record)

    if error:
        return jsonify({"error": error}), 400

    record = {
        "student_id": record["student_id"].strip(),
        "name": record["name"].strip(),
        "program": record["program"].strip(),
        "year": int(record["year"]),
        "section": record["section"].strip(),
        "source": record.get("source", "Partner API")
    }

    try:
        response = requests.post(
            CLASSMATE_API,
            json=record,
            timeout=15
        )

        try:
            partner_result = response.json()
        except ValueError:
            partner_result = response.text

        return jsonify({
            "message": (
                "Partner accepted the record."
                if response.ok else "Partner rejected the record."
            ),
            "status_code": response.status_code,
            "partner_response": partner_result,
            "sent_record": record
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Partner API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to send record to partner.",
            "details": str(error)
        }), 502


# API 404 HANDLER
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "API endpoint not found."
        }), 404

    return "Page not found.", 404


if __name__ == "__main__":
    app.run(debug=True)
