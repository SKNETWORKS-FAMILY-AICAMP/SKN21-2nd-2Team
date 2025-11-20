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
import bcrypt

# -------------------------------------------------------------
# 프로젝트 루트를 Python 경로에 추가 (utils import 가능)
# -------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, request
from utils.constants import get_connection
from utils.user_insert import load_users_from_csv
from pymysql.cursors import DictCursor

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

# -------------------------------------------------------------
# READ ALL
# -------------------------------------------------------------
@app.route("/api/users", methods=["GET"])
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)

# -------------------------------------------------------------
# READ ONE
# -------------------------------------------------------------
@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(row)

# -------------------------------------------------------------
# USER PAGING 조회 API (신규 추가)
# -------------------------------------------------------------
@app.route("/api/users_paged", methods=["GET"])
def get_users_paged():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        offset = (page - 1) * page_size

        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        # 전체 개수 조회
        cursor.execute("SELECT COUNT(*) AS cnt FROM users")
        total_rows = cursor.fetchone()["cnt"]

        # 페이징 데이터 조회
        cursor.execute("""
            SELECT user_id, name, favorite_music, grade, join_date
            FROM users
            ORDER BY user_id ASC
            LIMIT %s OFFSET %s
        """, (page_size, offset))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": (total_rows + page_size - 1) // page_size,
            "rows": rows
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
# -------------------------------------------------------------
# USER 조건 검색
# -------------------------------------------------------------  
@app.route("/api/users_search", methods=["GET"])
def users_search():
    try:
        # 검색 파라미터
        name = request.args.get("name", "").strip()
        user_id = request.args.get("user_id", "").strip()
        favorite_music = request.args.get("favorite_music", "").strip()
        grade = request.args.get("grade", "").strip()

        # 페이징 파라미터
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        offset = (page - 1) * page_size

        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        # ----------------------------
        # 동적 WHERE 조건 생성
        # ----------------------------
        conditions = []
        params = []

        if name:
            conditions.append("name LIKE %s")
            params.append(f"%{name}%")

        if user_id.isdigit():
            conditions.append("user_id = %s")
            params.append(int(user_id))

        if favorite_music:
            conditions.append("favorite_music LIKE %s")
            params.append(f"%{favorite_music}%")

        if grade:
            conditions.append("grade = %s")
            params.append(grade)

        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause

        # ----------------------------
        # 전체 개수 조회
        # ----------------------------
        count_sql = f"SELECT COUNT(*) AS cnt FROM users {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total_rows = cursor.fetchone()["cnt"]

        # ----------------------------
        # 페이징된 데이터 조회
        # ----------------------------
        query_sql = f"""
            SELECT user_id, name, favorite_music, join_date, grade
            FROM users
            {where_clause}
            ORDER BY user_id
            LIMIT %s OFFSET %s
        """

        cursor.execute(query_sql, tuple(params) + (page_size, offset))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": (total_rows + page_size - 1) // page_size,
            "rows": rows
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# -------------------------------------------------------------
# CREATE
# -------------------------------------------------------------  
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


# -------------------------------------------------------------
# CREATE (회원가입)
# -------------------------------------------------------------  
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json

    user_id = data.get("user_id")
    name = data.get("name")
    favorite_music = data.get("favorite_music", "")
    password = data.get("password")
    grade = "01"  # 기본 사용자 등급

    if not user_id or not name or not password:
        return jsonify({"success": False, "message": "필수 항목이 누락되었습니다."}), 400

    # ID 숫자 체크
    if not str(user_id).isdigit():
        return jsonify({"success": False, "message": "ID는 숫자만 가능합니다."}), 400

    # 비밀번호 bcrypt 해싱
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cursor = conn.cursor()

    # ID 중복 체크
    cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE user_id = %s", (user_id,))
    if cursor.fetchone()["cnt"] > 0:
        return jsonify({"success": False, "message": "이미 존재하는 ID입니다."})

    # 회원 생성
    sql = """
        INSERT INTO users (user_id, name, favorite_music, password, join_date, modify_date, grade)
        VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
    """
    cursor.execute(sql, (user_id, name, favorite_music, hashed_pw, grade))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "회원가입 완료"})

# -------------------------------------------------------------
# UPDATE
# -------------------------------------------------------------  
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

# -------------------------------------------------------------
# UPDATE_USER_DATA
# -------------------------------------------------------------  
@app.route("/api/update_user_data", methods=["POST"])
def update_user_data():
    try:
        data = request.json

        user_id = data.get("user_id")
        name = data.get("name")
        favorite_music = data.get("favorite_music")
        grade = data.get("grade")

        if not user_id:
            return jsonify({"success": False, "error": "user_id가 필요합니다."})

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE users
            SET name = %s,
                favorite_music = %s,
                grade = %s
            WHERE user_id = %s
        """

        cursor.execute(sql, (name, favorite_music, grade, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "사용자 정보가 수정되었습니다."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# -------------------------------------------------------------
# DELETE
# -------------------------------------------------------------  
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
# LOGIN (bcrypt 적용)
# -------------------------------------------------------------  
@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor(DictCursor)

    cursor.execute("""
        SELECT user_id, name, favorite_music, password, join_date, modify_date, grade
        FROM users
        WHERE user_id = %s
    """, (data['user_id'],))
    
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "아이디 없음"}), 401

    if bcrypt.checkpw(data['password'].encode("utf-8"), row['password'].encode("utf-8")):
        return jsonify({
            "success": True,
            "user_id": row['user_id'],
            "name": row['name'],
            "grade": row['grade']
        })

    return jsonify({"success": False, "message": "비밀번호 틀림"}), 401

# -------------------------------------------------------------
# ID 중복확인 API
# -------------------------------------------------------------
@app.route("/api/check_user_id", methods=["GET"])
def check_user_id():
    user_id = request.args.get("user_id", "").strip()

    if not user_id.isdigit():
        return jsonify({"success": False, "exists": False, "msg": "ID는 숫자만 가능합니다."})

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE user_id = %s", (user_id,))
    cnt = cursor.fetchone()["cnt"]

    cursor.close()
    conn.close()

    return jsonify({"success": True, "exists": cnt > 0})

# -------------------------------------------------------------
# Flask 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000)
