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
import pandas as pd

# -------------------------------------------------------------
# 프로젝트 루트를 Python 경로에 추가 (utils import 가능)
# -------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, request, Response
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
# 0-1) user_prediction 테이블 생성 (이탈 예측 결과 저장용)
# -------------------------------------------------------------
@app.route("/api/init_user_prediction_table")
def init_user_prediction_table():
    """
    이탈 예측 결과를 저장할 user_prediction 테이블을 생성합니다.

    - user_id 기준 UNIQUE 제약을 걸어, 한 유저당 1행만 유지
    - /api/predict_churn_6feat 호출 시 INSERT OR UPDATE 로 갱신
    """
    conn = get_connection()
    cursor = conn.cursor()

    # NOTE:
    # - churn_rate : INT (0~100, 이탈 확률 % 단위)
    # - risk_score : VARCHAR (예: 'LOW', 'MEDIUM', 'HIGH' 또는 '낮음', '보통', '높음')
    # - update_date: DATE (예측 실행 일자)
    sql = """
    CREATE TABLE IF NOT EXISTS user_prediction (
        user_id INT NOT NULL PRIMARY KEY,
        churn_rate INT NOT NULL,
        risk_score VARCHAR(20) NOT NULL,
        update_date DATE NOT NULL
    )
    """

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "user_prediction table created"})


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
    cursor = conn.cursor(DictCursor)

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

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
# UPDATE_USER_DATA (트랜잭션 적용)
# -------------------------------------------------------------  
@app.route("/api/update_user_data", methods=["POST"])
def update_user_data():
    conn = None
    cursor = None
    try:
        data = request.json

        user_id = data.get("user_id")
        name = data.get("name")
        favorite_music = data.get("favorite_music")
        grade = data.get("grade")

        if not user_id:
            return jsonify({"success": False, "error": "user_id가 필요합니다."}), 400

        # 입력값 검증
        if not name or not name.strip():
            return jsonify({"success": False, "error": "이름은 필수 입력 항목입니다."}), 400

        if grade not in ["01", "99"]:
            return jsonify({"success": False, "error": "등급은 01 또는 99만 가능합니다."}), 400

        # 데이터베이스 연결
        conn = get_connection()
        cursor = conn.cursor()

        # 트랜잭션 시작 (autocommit 비활성화)
        conn.autocommit(False)

        # 사용자 존재 여부 확인
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            conn.rollback()
            return jsonify({"success": False, "error": "사용자를 찾을 수 없습니다."}), 404

        # UPDATE 쿼리 실행
        sql = """
            UPDATE users
            SET name = %s,
                favorite_music = %s,
                grade = %s,
                modify_date = NOW()
            WHERE user_id = %s
        """

        cursor.execute(sql, (name.strip(), favorite_music.strip() if favorite_music else "", grade, user_id))
        
        # 영향받은 행 수 확인
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"success": False, "error": "수정된 데이터가 없습니다."}), 400

        # 트랜잭션 커밋
        conn.commit()

        return jsonify({
            "success": True, 
            "message": "사용자 정보가 수정되었습니다.",
            "data": {
                "user_id": user_id,
                "name": name.strip(),
                "favorite_music": favorite_music.strip() if favorite_music else "",
                "grade": grade
            }
        })

    except Exception as e:
        # 트랜잭션 롤백
        if conn:
            conn.rollback()
        return jsonify({"success": False, "error": f"데이터베이스 오류: {str(e)}"}), 500
    finally:
        # 리소스 정리
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
# ML 데이터 조회 API (관리자 시뮬레이션용)
# -------------------------------------------------------------
@app.route("/api/user_features/<int:user_id>", methods=["GET"])
def get_user_features(user_id):
    """
    특정 user_id의 ML 학습용 전체 피처 데이터를 CSV에서 조회해 반환합니다.
    관리자 페이지에서 '불러오기' 후 '수치 조정(시뮬레이션)'을 할 때 사용합니다.
    """
    try:
        # 1순위: churn_prob.py 로 생성된 최신 분석 결과 파일
        csv_path = os.path.join("data", "enhanced_data_with_lgbm_churn_prob.csv")
        
        # 2순위: 학습에 쓰인 원본 데이터
        if not os.path.exists(csv_path):
            csv_path = os.path.join("data", "enhanced_data_not_clean_FE_delete.csv")
            
        if not os.path.exists(csv_path):
             return jsonify({"success": False, "error": "ML 데이터 파일이 없습니다."}), 404

        # CSV 로드 (운영 환경에선 DB 조회가 더 적합)
        df = pd.read_csv(csv_path)
        
        # user_id 검색
        user_row = df[df["user_id"] == user_id]
        
        if user_row.empty:
             return jsonify({"success": False, "error": f"ML 데이터에서 user_id={user_id}를 찾을 수 없습니다."}), 404
             
        # dict로 변환 (NaN -> 0 or null)
        user_data = user_row.fillna(0).iloc[0].to_dict()
        
        return jsonify({"success": True, "data": user_data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 예측 API (전체 모델 이탈 확률 조회용 - 풀 피처)
# -------------------------------------------------------------
@app.route("/api/predict_churn", methods=["POST"])
def api_predict_churn():
    """
    전체 피처 + 사용할 모델 이름을 받아
    - 이탈 확률(churn_prob)
    - 위험도 레벨(risk_level)
    을 반환하는 API.

    내부적으로 backend.inference.predict_churn 를 사용하며,
    전처리 파이프라인 + config.DEFAULT_MODEL_NAME 기반의 "풀 모델"을 호출합니다.

    Request JSON 예시:
    {
      "model_name": "hgb",        # 선택 사항 (미입력 시 config.DEFAULT_MODEL_NAME 사용)
      "features": {
        "user_id": 123,           # 선택적, 필요 시 사용
        "listening_time": 180,
        "songs_played_per_day": 40,
        "payment_failure_count": 1,
        "app_crash_count_30d": 0,
        "subscription_type": "Premium",
        "customer_support_contact": 0,
        "...": "전처리 파이프라인에 정의된 나머지 피처들"
      }
    }

    응답 예시:
    {
      "success": true,
      "model_name": "hgb",
      "churn_prob": 0.73,
      "risk_level": "HIGH"
    }
    """
    try:
        payload = request.get_json(force=True) or {}
        model_name = payload.get("model_name")
        features = payload.get("features") or {}

        if not isinstance(features, dict):
            return jsonify({"success": False, "error": "features 필드는 dict 형태여야 합니다."}), 400

        from backend.inference import predict_churn as _predict_churn

        result = _predict_churn(user_features=features, model_name=model_name)

        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"success": False, "error": f"예측 중 오류 발생: {str(e)}"}), 500


# -------------------------------------------------------------
# 예측 API (6개 피처 전용 LGBM 단조제약 시뮬레이터)
# -------------------------------------------------------------
@app.route("/api/predict_churn_6feat", methods=["POST"])
def api_predict_churn_6feat():
    """
    6개 시뮬레이터용 피처만 받아
    - 이탈 확률(churn_prob)
    - 위험도 레벨(risk_level)
    을 반환하는 API.

    내부적으로 backend.inference_sim_6feat_lgbm.predict_churn_6feat_lgbm 를 사용하며,
    models/lgbm_sim_6feat_mono.pkl (단조 제약 LGBM) 을 호출합니다.

    또한, 예측 결과는 user_prediction 테이블에 user_id 기준으로 INSERT OR UPDATE 됩니다.

    Request JSON 예시:
    {
      "user_id": 123,
      "features": {
        "app_crash_count_30d": 2,
        "skip_rate_increase_7d": 10.0,
        "days_since_last_login": 7,
        "listening_time_trend_7d": -10.0,
        "freq_of_use_trend_14d": -5.0,
        "login_frequency_30d": 12
      }
    }
    """
    try:
        payload = request.get_json(force=True) or {}
        user_id = payload.get("user_id")
        features = payload.get("features") or {}

        if not isinstance(features, dict):
            return jsonify({"success": False, "error": "features 필드는 dict 형태여야 합니다."}), 400

        if not user_id:
            return jsonify({"success": False, "error": "user_id 필드는 필수입니다."}), 400

        from backend.inference_sim_6feat_lgbm import predict_churn_6feat_lgbm

        result = predict_churn_6feat_lgbm(features)

        if not result.get("success"):
            return jsonify(result), 500

        # 모델 내부 확률(0.0~1.0)을 % 단위 INT 로 변환
        churn_prob = float(result["churn_prob"])
        churn_rate = int(round(churn_prob * 100))  # 0~100 (%)

        # risk_level 은 "LOW" / "MEDIUM" / "HIGH" 이므로,
        # DB 에는 그대로 저장하거나, 필요시 한글 레이블로 매핑 가능.
        risk_score = result["risk_level"]

        # user_prediction 테이블에 INSERT OR UPDATE (user_id 기준 1행 유지)
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
        VALUES (%s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            churn_rate = VALUES(churn_rate),
            risk_score = VALUES(risk_score),
            update_date = CURDATE()
        """
        cursor.execute(sql, (user_id, churn_rate, risk_score))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": user_id,
            "churn_rate": churn_rate,     # 정수 (%) 단위
            "risk_score": risk_score,
            "update_date": pd.Timestamp.now().date().isoformat(),
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"6피처 예측 중 오류 발생: {str(e)}"}), 500


# -------------------------------------------------------------
# user_prediction 조회 API (TB에서 위험도 및 userData 호출)
# -------------------------------------------------------------
@app.route("/api/user_prediction/<int:user_id>", methods=["GET"])
def get_user_prediction(user_id):
    """
    user_prediction 테이블에서 특정 user_id의
    - user_id
    - churn_rate
    - risk_score
    - update_date
    를 조회해서 반환합니다.

    화면에서 입력받은 User PK 값으로 호출하는 용도입니다.

    Response 예시:
    {
      "success": true,
      "data": {
        "user_id": 123,
        "churn_rate": 0.3197,
        "risk_score": "MEDIUM",
        "update_date": "2025-11-24T12:34:56"
      }
    }
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        cursor.execute(
            """
            SELECT user_id, churn_rate, risk_score, update_date
            FROM user_prediction
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({
                "success": False,
                "error": f"user_prediction 에 user_id={user_id} 기록이 없습니다."
            }), 404

        # DATETIME → ISO 문자열 변환 (프론트에서 다루기 쉽게)
        if "update_date" in row and row["update_date"] is not None:
            row["update_date"] = row["update_date"].isoformat()

        return jsonify({"success": True, "data": row}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"user_prediction 조회 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# CSV 업로드 API (여러 유저 위험도 일괄 예측)
# -------------------------------------------------------------
@app.route("/api/upload_prediction_csv", methods=["POST"])
def upload_prediction_csv():
    """
    위험도 예측 화면에서 CSV 파일을 업로드하면,
    각 행의 user_id + 6개 피처를 사용해 LGBM(단조 제약) 모델로 이탈 확률을 계산하고
    user_prediction 테이블에 INSERT OR UPDATE 합니다.

    기대 CSV 컬럼:
    - user_id
    - app_crash_count_30d
    - skip_rate_increase_7d
    - days_since_last_login
    - listening_time_trend_7d
    - freq_of_use_trend_14d
    - login_frequency_30d
    """
    try:
        file = request.files.get("file")
        if file is None:
            return jsonify({"success": False, "error": "file 필드에 CSV 파일을 업로드해야 합니다."}), 400

        df = pd.read_csv(file)

        required_cols = [
            "user_id",
            "app_crash_count_30d",
            "skip_rate_increase_7d",
            "days_since_last_login",
            "listening_time_trend_7d",
            "freq_of_use_trend_14d",
            "login_frequency_30d",
        ]
        for col in required_cols:
            if col not in df.columns:
                return jsonify({"success": False, "error": f"CSV에 '{col}' 컬럼이 필요합니다."}), 400

        from backend.inference_sim_6feat_lgbm import predict_churn_6feat_lgbm

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
        VALUES (%s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            churn_rate = VALUES(churn_rate),
            risk_score = VALUES(risk_score),
            update_date = CURDATE()
        """

        processed = 0

        for _, row in df.iterrows():
            user_id = row["user_id"]
            try:
                user_id_int = int(user_id)
            except Exception:
                # user_id 가 숫자가 아니면 스킵
                continue

            features = {col: row[col] for col in required_cols if col != "user_id"}
            result = predict_churn_6feat_lgbm(features)
            if not result.get("success"):
                continue

            churn_prob = float(result["churn_prob"])
            churn_rate = int(round(churn_prob * 100))
            risk_score = result["risk_level"]

            cursor.execute(sql, (user_id_int, churn_rate, risk_score))
            processed += 1

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "processed_rows": processed
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"CSV 업로드 처리 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# CSV 다운로드 API (user_prediction 전체를 CSV로 반환)
# -------------------------------------------------------------
@app.route("/api/download_prediction_csv", methods=["GET"])
def download_prediction_csv():
    """
    user_prediction 테이블의 내용을
    - user_id
    - churn_rate
    - risk_score
    - update_date
    컬럼으로 구성된 CSV 파일로 반환합니다.

    위험도 예측 화면의 "CSV 다운로드" 버튼에서 호출하는 용도입니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        cursor.execute(
            """
            SELECT user_id, churn_rate, risk_score, update_date
            FROM user_prediction
            ORDER BY user_id ASC
            """
        )
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # pandas DataFrame으로 변환 후 CSV 문자열 생성
        df = pd.DataFrame(rows, columns=["user_id", "churn_rate", "risk_score", "update_date"])
        if not df.empty:
            # DATE → 문자열
            df["update_date"] = df["update_date"].astype(str)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=user_prediction.csv"
            },
        )

    except Exception as e:
        return jsonify({"success": False, "error": f"CSV 다운로드 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# Flask 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000)
