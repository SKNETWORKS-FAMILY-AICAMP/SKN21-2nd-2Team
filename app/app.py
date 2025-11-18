"""
app.py (Flask API)
Auth: 박수빈
Date: 2025-11-18
Description:
- User Table CRUD
- CSV 단발성 삽입 지원
"""

import sys
import os

# -------------------------------------------------------------
# 프로젝트 루트를 Python 경로에 추가 (utils import 가능)
# -------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, request
from utils.constants import get_connection
from utils.user_insert import load_users_from_csv

app = Flask(__name__)


# -------------------------------------------------------------
# 0) 초기 테이블 생성
# -------------------------------------------------------------
@app.route("/api/init_user_table")
def init_user_table():
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        favorite_music VARCHAR(50),
        password VARCHAR(200) NOT NULL,
        join_date DATE,
        modify_date DATE,
        grade CHAR(2) NOT NULL
    )
    """

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "User table created"})


# -------------------------------------------------------------
# 1) CSV 데이터 단발성 삽입
# -------------------------------------------------------------
@app.route("/api/import_users_from_csv")
def import_users_from_csv():
    csv_path = os.path.join("data", "user_data.csv")

    try:
        load_users_from_csv(csv_path)
        return jsonify({"message": "CSV imported to DB"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------
# 2) USER CRUD REST API
# -------------------------------------------------------------

# READ ALL
@app.route("/api/users", methods=["GET"])
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)


# READ ONE
@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(row)


# CREATE
@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO users
    (name, favorite_music, password, join_date, modify_date, grade)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (
        data["name"],
        data["favorite_music"],
        data["password"],
        data["join_date"],
        data["modify_date"],
        data["grade"]
    ))

    conn.commit()
    new_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({"message": "User created", "user_id": new_id})


# UPDATE
@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE users
    SET name=%s, favorite_music=%s, password=%s, join_date=%s, modify_date=%s, grade=%s
    WHERE user_id=%s
    """

    cursor.execute(sql, (
        data["name"],
        data["favorite_music"],
        data["password"],
        data["join_date"],
        data["modify_date"],
        data["grade"],
        user_id
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "User updated"})


# DELETE
@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "User deleted"})


# -------------------------------------------------------------
# Flask 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
