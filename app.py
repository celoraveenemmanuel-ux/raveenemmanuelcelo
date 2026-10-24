
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/')
def home():
    return "Welcome to my first API!"


@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "24-00194",
        "name": "Raveen Emmanuel Celo",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })


@app.route('/motorcycle')
def get_motorcycle():
    return jsonify({
        "motorcycle_name": "Honda Click 125i",
        "brand": "Honda",
        "engine_cc": 125,
        "price": 79900,
        "available": True
    })


@app.route('/area')
def calculate_area():
    length = request.args.get('length', type=float)
    width = request.args.get('width', type=float)

    if length is None or width is None:
        return jsonify({
            "error": "Please provide length and width."
        }), 400

    return jsonify({
        "length": length,
        "width": width,
        "area": length * width
    })


if __name__ == '__main__':
    app.run(debug=True)
