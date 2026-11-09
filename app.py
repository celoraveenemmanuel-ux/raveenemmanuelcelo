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

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                source TEXT DEFAULT 'Local'
            )
        """)

        columns = {
            column["name"]
            for column in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        }

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

    finally:
        conn.close()


initialize_database()


# VALIDATE STUDENT DATA
def validate_student_data(data):
    if not isinstance(data, dict):
        return "Invalid JSON data."

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        if field not in data or str(data[field]).strip() == "":
            return f"{field} is required."

    try:
        year = int(data["year"])

        if year < 1 or year > 4:
            return "Year must be between 1 and 4."

    except (ValueError, TypeError):
        return "Invalid year."

    return None


# INSERT STUDENT
def insert_student(data, source):
    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            int(data["year"]),
            str(data["section"]).strip(),
            source
        ))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


# GET STUDENTS BY SOURCE
def get_students_by_source(source):
    conn = get_db_connection()

    try:
        rows = conn.execute("""
            SELECT * FROM students
            WHERE source = ?
            ORDER BY id DESC
        """, (source,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# STUDENT INFORMATION API
@app.route("/student", methods=["GET"])
def get_student():
    return jsonify({
        "student_id": "24-00063",
        "name": "Raveen Emmanuel Celo",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# GREETING API
@app.route("/hello", methods=["GET"])
def say_hello():
    name = request.args.get("name", "Student")

    return jsonify({
        "message": f"Hello, {name}!"
    })


# MOTORCYCLE API
@app.route("/motorcycle", methods=["GET"])
def get_motorcycle():
    return jsonify({
        "brand": "Yamaha",
        "model": "Motorcycle",
        "type": "Sample API"
    })


# GET ALL STUDENTS
@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            ORDER BY id DESC
        """).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET ONE STUDENT
@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute("""
            SELECT * FROM students
            WHERE id = ?
        """, (id,)).fetchone()

        if student is None:
            return jsonify({"error": "Student not found."}), 404

        return jsonify(dict(student))

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# GET STUDENTS BY YEAR
@app.route("/students/year/<int:year>", methods=["GET"])
def get_students_by_year(year):
    if year < 1 or year > 4:
        return jsonify({
            "error": "Year must be between 1 and 4."
        }), 400

    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            WHERE year = ?
            ORDER BY id DESC
        """, (year,)).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# ADD STUDENT
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    # Records from the local form explicitly send Local.
    # Incoming API records without a source become External API.
    source = str(data.get("source", "External API")).strip()

    allowed_sources = [
        "Local",
        "Imported",
        "External API",
        "Partner API",
        "Classmate API"
    ]

    if source not in allowed_sources:
        return jsonify({
            "error": "Invalid student source.",
            "received_source": source,
            "allowed_sources": allowed_sources
        }), 400

    try:
        new_id = insert_student(data, source)

        return jsonify({
            "message": "Student added successfully!",
            "id": new_id,
            "source": source
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500


# UPDATE STUDENT
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)

    error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute("""
            SELECT id FROM students WHERE id = ?
        """, (id,)).fetchone()

        if existing is None:
            return jsonify({"error": "Student not found."}), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            int(data["year"]),
            str(data["section"]).strip(),
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
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            DELETE FROM students WHERE id = ?
        """, (id,))

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found."}), 404

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully!"
        })

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# INTEGRATION DASHBOARD DATA
@app.route("/api/integration-dashboard", methods=["GET"])
def integration_dashboard():
    conn = get_db_connection()

    try:
        local_records = conn.execute("""
            SELECT * FROM students
            WHERE source = 'Local'
            ORDER BY id DESC
        """).fetchall()

        imported_records = conn.execute("""
            SELECT * FROM students
            WHERE source IN (
                'Classmate API',
                'Imported'
            )
            ORDER BY id DESC
        """).fetchall()

        external_records = conn.execute("""
            SELECT * FROM students
            WHERE source IN (
                'External API',
                'Partner API'
            )
            ORDER BY id DESC
        """).fetchall()

        return jsonify({
            "local_records": [
                dict(row) for row in local_records
            ],
            "imported_records": [
                dict(row) for row in imported_records
            ],
            "other_api_records": [
                dict(row) for row in external_records
            ],
            "counts": {
                "local": len(local_records),
                "imported": len(imported_records),
                "other_api": len(external_records)
            }
        })

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# RETRIEVE CLARK'S STUDENT RECORDS
@app.route("/classmate-records", methods=["GET"])
@app.route("/partner-records", methods=["GET"])
def get_classmate_records():
    try:
        response = requests.get(
            CLASSMATE_API,
            timeout=30
        )

        response.raise_for_status()
        records = response.json()

        if not isinstance(records, list):
            return jsonify({
                "error": "Clark's API did not return a student list."
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


# IMPORT SELECTED STUDENT FROM CLARK
@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True) or {}
    selected_id = data.get("id")

    if selected_id is None:
        return jsonify({
            "error": "Student ID is required."
        }), 400

    try:
        response = requests.get(
            CLASSMATE_API,
            timeout=30
        )

        response.raise_for_status()
        records = response.json()

        if not isinstance(records, list):
            return jsonify({
                "error": "Invalid student list from Clark."
            }), 502

        selected_student = next(
            (
                student for student in records
                if str(student.get("id")) == str(selected_id)
                or str(student.get("student_id")) == str(selected_id)
            ),
            None
        )

        if selected_student is None:
            return jsonify({
                "error": "Selected student not found."
            }), 404

        error = validate_student_data(selected_student)

        if error:
            return jsonify({"error": error}), 400

        new_id = insert_student(
            selected_student,
            "Classmate API"
        )

        return jsonify({
            "message": "Student imported successfully!",
            "id": new_id,
            "source": "Classmate API"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists in your database."
        }), 409

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to retrieve Clark's records.",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Clark's API returned invalid JSON."
        }), 502

    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500


# SEND PRACTICE RECORD TO CLARK
@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    record = {
        "student_id": "EXT-RAVEEN-001",
        "name": "Raveen Sample Exchange Record",
        "program": "BSIT",
        "year": 1,
        "section": "A",
        "source": "Partner API"
    }

    error = validate_student_data(record)

    if error:
        return jsonify({"error": error}), 400

    try:
        response = requests.post(
            CLASSMATE_API,
            json=record,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )

        try:
            partner_result = response.json()
        except ValueError:
            partner_result = response.text

        if response.status_code in (200, 201):
            return jsonify({
                "message": "Practice record successfully sent to Clark!",
                "status_code": response.status_code,
                "partner_response": partner_result,
                "sent_record": record
            }), 200

        return jsonify({
            "message": "Clark's API rejected the record.",
            "status_code": response.status_code,
            "partner_response": partner_result,
            "sent_record": record,
            "destination": CLASSMATE_API
        }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Clark's API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to send the practice record to Clark.",
            "details": str(error),
            "destination": CLASSMATE_API
        }), 502


# 404 ERROR HANDLER
@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "API endpoint not found."
        }), 404

    return "Page not found.", 404


if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )