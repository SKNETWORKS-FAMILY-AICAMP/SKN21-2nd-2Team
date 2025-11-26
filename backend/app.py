"""
app.py (Flask API 서버)
Auth: 박수빈
Date: 2025-11-18
Description
- 데이터베이스 테이블 초기화 (users, user_prediction, user_features, log, achievements 등)
- 사용자 CRUD API (생성, 조회, 수정, 삭제)
- 사용자 로그인 및 인증
- 구독해지 처리
- 이탈 예측 API (단일/배치/6피처)
- 예측 결과 조회 및 관리
- CSV 데이터 import/export
- Spotify 음악 검색 API
- 음악 재생 로그 기록
- 도전과제 관리 API
- 사용자 활동 로그 관리
- 테스트 계정 설정
"""

import sys
import os
import bcrypt
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, request, jsonify, redirect, Response
import requests
import pymysql.cursors

# backend 디렉토리에서 실행할 때 상위 디렉토리를 sys.path에 추가
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.constants import get_connection
from utils.user_insert import load_users_from_csv

DictCursor = pymysql.cursors.DictCursor

load_dotenv()
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

    # selected_achievement_id 컬럼 추가 (이미 있으면 무시)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN selected_achievement_id INT")
    except Exception:
        pass  # 컬럼이 이미 존재하는 경우 무시
    
    # 외래키 제약조건 추가 (achievements 테이블이 존재하는 경우에만)
    try:
        cursor.execute("""
            ALTER TABLE users 
            ADD CONSTRAINT fk_users_selected_achievement 
            FOREIGN KEY (selected_achievement_id) 
            REFERENCES achievements(achievement_id) 
            ON DELETE SET NULL
        """)
    except Exception:
        pass  # 제약조건이 이미 존재하거나 achievements 테이블이 없는 경우 무시
    
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
# 0-2) user_features 테이블 생성 (CSV 피처 데이터 저장용)
# -------------------------------------------------------------
@app.route("/api/init_user_features_table")
def init_user_features_table():
    """
    enhanced_data_not_clean_FE_delete.csv의 피처 데이터를 저장할 user_features 테이블을 생성합니다.
    
    users 테이블에 없는 컬럼들을 저장하며, user_id로 join하여 사용합니다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS user_features (
        user_id INT NOT NULL PRIMARY KEY,
        gender VARCHAR(20),
        age INT,
        country VARCHAR(50),
        subscription_type VARCHAR(50),
        listening_time FLOAT,
        songs_played_per_day FLOAT,
        skip_rate FLOAT,
        device_type VARCHAR(50),
        ads_listened_per_week INT,
        offline_listening INT,
        is_churned INT,
        listening_time_trend_7d FLOAT,
        login_frequency_30d INT,
        days_since_last_login INT,
        skip_rate_increase_7d FLOAT,
        freq_of_use_trend_14d FLOAT,
        customer_support_contact INT,
        payment_failure_count INT,
        promotional_email_click INT,
        app_crash_count_30d INT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "user_features table created"})


# -------------------------------------------------------------
# 0-3) log 테이블 생성 (사용자 활동 로그 저장용)
# -------------------------------------------------------------
@app.route("/api/init_log_table")
def init_log_table():
    """
    사용자 활동 로그를 저장할 log 테이블을 생성합니다.
    
    - user_id: 사용자 ID (외래키)
    - action_type: 활동 유형 ('LOGIN', 'PAGE_VIEW', 'UNSUBSCRIBE' 등)
    - page_name: 접근한 페이지 이름
    - created_at: 기록 시간
    - additional_info: 추가 정보 (JSON 형태)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        CREATE TABLE IF NOT EXISTS log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            page_name VARCHAR(100),
            additional_info TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_action_type (action_type),
            INDEX idx_created_at (created_at)
        )
        """

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "log table created"})
    except Exception as e:
        return jsonify({"success": False, "error": f"테이블 생성 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 0-3-1) achievements 테이블 생성 (도전과제 정의)
# -------------------------------------------------------------
@app.route("/api/init_achievements_table")
def init_achievements_table():
    """
    도전과제 정의를 저장할 achievements 테이블을 생성합니다.
    
    - achievement_id: 도전과제 ID
    - title: 도전과제 제목
    - description: 도전과제 설명
    - achievement_type: 도전과제 유형 ('TRACK_PLAY', 'GENRE_PLAY' 등)
    - target_value: 목표 값 (예: 재생 횟수)
    - target_track_uri: 목표 트랙 URI (TRACK_PLAY 타입인 경우)
    - target_genre: 목표 장르 (GENRE_PLAY 타입인 경우)
    - reward_points: 보상 포인트
    - is_active: 활성화 여부
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            achievement_type VARCHAR(50) NOT NULL,
            target_value INT NOT NULL,
            target_track_uri VARCHAR(200),
            target_genre VARCHAR(100),
            reward_points INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_achievement_type (achievement_type),
            INDEX idx_is_active (is_active)
        )
        """

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "achievements table created"})
    except Exception as e:
        return jsonify({"success": False, "error": f"테이블 생성 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 0-3-2) user_achievements 테이블 생성 (사용자별 도전과제 진행 상황)
# -------------------------------------------------------------
@app.route("/api/init_user_achievements_table")
def init_user_achievements_table():
    """
    사용자별 도전과제 진행 상황을 저장할 user_achievements 테이블을 생성합니다.
    
    - user_achievement_id: 사용자 도전과제 ID
    - user_id: 사용자 ID (외래키)
    - achievement_id: 도전과제 ID (외래키)
    - current_progress: 현재 진행도
    - is_completed: 완료 여부
    - completed_at: 완료 시간
    - created_at: 시작 시간
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_achievement_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            achievement_id INT NOT NULL,
            current_progress INT DEFAULT 0,
            is_completed BOOLEAN DEFAULT FALSE,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id),
            INDEX idx_user_id (user_id),
            INDEX idx_achievement_id (achievement_id),
            INDEX idx_is_completed (is_completed)
        )
        """

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "user_achievements table created"})
    except Exception as e:
        return jsonify({"success": False, "error": f"테이블 생성 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 0-3-3) music_playback_log 테이블 생성 (노래 재생 로그)
# -------------------------------------------------------------
@app.route("/api/init_music_playback_log_table")
def init_music_playback_log_table():
    """
    노래 재생 로그를 저장할 music_playback_log 테이블을 생성합니다.
    
    - playback_id: 재생 로그 ID
    - user_id: 사용자 ID (외래키)
    - track_uri: 트랙 URI
    - track_name: 트랙 이름
    - artist_name: 아티스트 이름
    - genre: 장르 (선택적)
    - playback_duration: 재생 시간 (초)
    - created_at: 재생 시간
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        CREATE TABLE IF NOT EXISTS music_playback_log (
            playback_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            track_uri VARCHAR(200) NOT NULL,
            track_name VARCHAR(200),
            artist_name VARCHAR(200),
            genre VARCHAR(100),
            playback_duration INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_track_uri (track_uri),
            INDEX idx_genre (genre),
            INDEX idx_user_track (user_id, track_uri),
            INDEX idx_user_genre (user_id, genre),
            INDEX idx_created_at (created_at)
        )
        """

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "music_playback_log table created"})
    except Exception as e:
        return jsonify({"success": False, "error": f"테이블 생성 중 오류: {str(e)}"}), 500
# -------------------------------------------------------------
# 0-4) 로그 기록 API
# -------------------------------------------------------------
@app.route("/api/log", methods=["POST"])
def create_log():
    """
    사용자 활동 로그를 기록합니다.
    
    Request JSON:
    {
        "user_id": 123,
        "action_type": "LOGIN" | "PAGE_VIEW" | "UNSUBSCRIBE" 등,
        "page_name": "개인정보 수정",
        "additional_info": "추가 정보 (선택적)"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        action_type = data.get("action_type")
        page_name = data.get("page_name")
        additional_info = data.get("additional_info")
        
        if not user_id or not action_type:
            return jsonify({"success": False, "error": "user_id와 action_type은 필수입니다."}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO log (user_id, action_type, page_name, additional_info)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(sql, (user_id, action_type, page_name, additional_info))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "로그가 기록되었습니다."})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"로그 기록 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 0-5) 로그 조회 API
# -------------------------------------------------------------
@app.route("/api/logs", methods=["GET"])
def get_logs():
    """
    로그를 조회합니다.
    
    Query Parameters:
    - user_id: 특정 사용자의 로그만 조회 (선택적)
    - action_type: 특정 액션 타입만 조회 (선택적)
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 50)
    """
    try:
        user_id = request.args.get("user_id", "").strip()
        action_type = request.args.get("action_type", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        offset = (page - 1) * page_size
        
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # WHERE 조건 생성
        conditions = []
        params = []
        
        if user_id and user_id.isdigit():
            conditions.append("l.user_id = %s")
            params.append(int(user_id))
        
        if action_type:
            conditions.append("l.action_type = %s")
            params.append(action_type)
        
        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # 전체 개수 조회
        count_sql = f"""
        SELECT COUNT(*) AS cnt
        FROM log l
        {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total_rows = cursor.fetchone()["cnt"]
        
        # 페이징된 데이터 조회
        query_sql = f"""
        SELECT l.log_id, l.user_id, u.name AS user_name, l.action_type, 
               l.page_name, l.additional_info, l.created_at
        FROM log l
        LEFT JOIN users u ON l.user_id = u.user_id
        {where_clause}
        ORDER BY l.created_at DESC
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
        return jsonify({"success": False, "error": f"로그 조회 중 오류: {str(e)}"}), 500


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
# 1-1) user_features CSV 데이터 삽입
# -------------------------------------------------------------
@app.route("/api/import_user_features_from_csv", methods=["POST"])
def import_user_features_from_csv():
    """
    CSV 파일을 읽어서 user_features 테이블에 삽입합니다.
    
    두 가지 방식 지원:
    1. 파일 업로드: multipart/form-data로 CSV 파일 전송
    2. JSON 데이터: request.json에 rows 배열로 데이터 전송
    3. 기본 경로: 파일이 없으면 data/processed/enhanced_data_not_clean_FE_delete.csv 사용
    """
    try:
        df = None
        
        # 1. 파일 업로드 방식 확인
        if 'file' in request.files:
            uploaded_file = request.files['file']
            if uploaded_file.filename:
                df = pd.read_csv(uploaded_file)
        
        # 2. JSON 데이터 방식 확인
        elif request.is_json:
            payload = request.get_json()
            if 'rows' in payload and isinstance(payload['rows'], list):
                df = pd.DataFrame(payload['rows'])
        
        # 3. 기본 경로 사용
        if df is None:
            csv_path = os.path.join("data", "processed", "enhanced_data_not_clean_FE_delete.csv")
            if not os.path.exists(csv_path):
                return jsonify({"success": False, "error": f"CSV 파일을 찾을 수 없습니다. 파일을 업로드하거나 {csv_path} 파일이 존재해야 합니다."}), 404
            df = pd.read_csv(csv_path)
        
        if df is None or df.empty:
            return jsonify({"success": False, "error": "데이터가 없습니다."}), 400
        
        # 필수 컬럼 확인
        required_columns = ['user_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({"success": False, "error": f"필수 컬럼이 없습니다: {', '.join(missing_columns)}"}), 400
        
        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # INSERT OR UPDATE (ON DUPLICATE KEY UPDATE)
        sql = """
        INSERT INTO user_features (
            user_id, gender, age, country, subscription_type, listening_time,
            songs_played_per_day, skip_rate, device_type, ads_listened_per_week,
            offline_listening, is_churned, listening_time_trend_7d, login_frequency_30d,
            days_since_last_login, skip_rate_increase_7d, freq_of_use_trend_14d,
            customer_support_contact, payment_failure_count, promotional_email_click,
            app_crash_count_30d
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            gender = VALUES(gender),
            age = VALUES(age),
            country = VALUES(country),
            subscription_type = VALUES(subscription_type),
            listening_time = VALUES(listening_time),
            songs_played_per_day = VALUES(songs_played_per_day),
            skip_rate = VALUES(skip_rate),
            device_type = VALUES(device_type),
            ads_listened_per_week = VALUES(ads_listened_per_week),
            offline_listening = VALUES(offline_listening),
            is_churned = VALUES(is_churned),
            listening_time_trend_7d = VALUES(listening_time_trend_7d),
            login_frequency_30d = VALUES(login_frequency_30d),
            days_since_last_login = VALUES(days_since_last_login),
            skip_rate_increase_7d = VALUES(skip_rate_increase_7d),
            freq_of_use_trend_14d = VALUES(freq_of_use_trend_14d),
            customer_support_contact = VALUES(customer_support_contact),
            payment_failure_count = VALUES(payment_failure_count),
            promotional_email_click = VALUES(promotional_email_click),
            app_crash_count_30d = VALUES(app_crash_count_30d)
        """
        
        inserted_count = 0
        error_count = 0
        error_messages = []
        
        for idx, row in df.iterrows():
            try:
                # user_id는 필수
                user_id = int(row['user_id']) if pd.notna(row['user_id']) else None
                if user_id is None:
                    error_count += 1
                    continue
                
                values = (
                    user_id,
                    str(row['gender']) if pd.notna(row.get('gender')) else None,
                    int(row['age']) if pd.notna(row.get('age')) else None,
                    str(row['country']) if pd.notna(row.get('country')) else None,
                    str(row['subscription_type']) if pd.notna(row.get('subscription_type')) else None,
                    float(row['listening_time']) if pd.notna(row.get('listening_time')) else None,
                    float(row['songs_played_per_day']) if pd.notna(row.get('songs_played_per_day')) else None,
                    float(row['skip_rate']) if pd.notna(row.get('skip_rate')) else None,
                    str(row['device_type']) if pd.notna(row.get('device_type')) else None,
                    int(row['ads_listened_per_week']) if pd.notna(row.get('ads_listened_per_week')) else None,
                    int(row['offline_listening']) if pd.notna(row.get('offline_listening')) else None,
                    int(row['is_churned']) if pd.notna(row.get('is_churned')) else None,
                    float(row['listening_time_trend_7d']) if pd.notna(row.get('listening_time_trend_7d')) else None,
                    int(row['login_frequency_30d']) if pd.notna(row.get('login_frequency_30d')) else None,
                    int(row['days_since_last_login']) if pd.notna(row.get('days_since_last_login')) else None,
                    float(row['skip_rate_increase_7d']) if pd.notna(row.get('skip_rate_increase_7d')) else None,
                    float(row['freq_of_use_trend_14d']) if pd.notna(row.get('freq_of_use_trend_14d')) else None,
                    int(row['customer_support_contact']) if pd.notna(row.get('customer_support_contact')) else None,
                    int(row['payment_failure_count']) if pd.notna(row.get('payment_failure_count')) else None,
                    int(row['promotional_email_click']) if pd.notna(row.get('promotional_email_click')) else None,
                    int(row['app_crash_count_30d']) if pd.notna(row.get('app_crash_count_30d')) else None,
                )
                cursor.execute(sql, values)
                inserted_count += 1
            except Exception as e:
                error_count += 1
                if len(error_messages) < 5:  # 최대 5개까지만 저장
                    error_messages.append(f"행 {idx+1}: {str(e)}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        result_message = f"CSV 데이터 import 완료: {inserted_count}개 행 처리됨"
        if error_count > 0:
            result_message += f", {error_count}개 행 오류 발생"
        
        return jsonify({
            "success": True,
            "message": result_message,
            "inserted_count": inserted_count,
            "error_count": error_count,
            "errors": error_messages if error_messages else None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"CSV import 중 오류: {str(e)}"}), 500


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
        risk_score = request.args.get("risk_score", "").strip()

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
            conditions.append("u.name LIKE %s")
            params.append(f"%{name}%")

        if user_id.isdigit():
            conditions.append("u.user_id = %s")
            params.append(int(user_id))

        if favorite_music:
            conditions.append("u.favorite_music LIKE %s")
            params.append(f"%{favorite_music}%")

        if grade:
            conditions.append("u.grade = %s")
            params.append(grade)

        if risk_score:
            conditions.append("COALESCE(up.risk_score, 'UNKNOWN') = %s")
            params.append(risk_score)

        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause

        # ----------------------------
        # 전체 개수 조회 (JOIN 포함)
        # ----------------------------
        count_sql = f"""
            SELECT COUNT(*) AS cnt 
            FROM users u
            LEFT JOIN user_prediction up ON u.user_id = up.user_id
            {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total_rows = cursor.fetchone()["cnt"]

        # ----------------------------
        # 페이징된 데이터 조회 (위험도 포함)
        # ----------------------------
        query_sql = f"""
            SELECT u.user_id, u.name, u.favorite_music, u.join_date, u.grade,
                   COALESCE(up.risk_score, 'UNKNOWN') AS risk_score,
                   COALESCE(up.churn_rate, 0) AS churn_rate
            FROM users u
            LEFT JOIN user_prediction up ON u.user_id = up.user_id
            {where_clause}
            ORDER BY u.user_id
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
    
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "아이디 없음"}), 401

    if bcrypt.checkpw(data['password'].encode("utf-8"), row['password'].encode("utf-8")):
        # 등급이 '00' (휴면 유저)인 경우 로그인 차단
        if row['grade'] == '00':
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "구독해지된 계정입니다. 로그인할 수 없습니다."}), 403
        
        # 로그인 성공 시 로그 기록
        try:
            log_sql = """
            INSERT INTO log (user_id, action_type, page_name, additional_info)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(log_sql, (row['user_id'], 'LOGIN', '로그인', None))
            conn.commit()
        except Exception as e:
            # 로그 기록 실패해도 로그인은 성공 처리
            pass
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "user_id": row['user_id'],
            "name": row['name'],
            "grade": row['grade']
        })

    cursor.close()
    conn.close()
    return jsonify({"success": False, "message": "비밀번호 틀림"}), 401

# -------------------------------------------------------------
# 구독해지 API
# -------------------------------------------------------------
@app.route("/api/unsubscribe", methods=["POST"])
def unsubscribe_user():
    """
    사용자 구독해지 처리
    - users 테이블의 grade를 '00'으로 변경 (휴면 유저)
    - user_prediction 테이블의 risk_score를 'HIGH'로 업데이트
    - log 테이블에 구독해지 기록
    """
    conn = None
    cursor = None
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        reason = data.get("reason", "")
        feedback = data.get("feedback", "")
        
        if not user_id:
            return jsonify({"success": False, "error": "user_id는 필수입니다."}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # users 테이블의 grade를 '00'으로 변경 (휴면 유저)
        sql_user = """
        UPDATE users
        SET grade = '00', modify_date = NOW()
        WHERE user_id = %s
        """
        cursor.execute(sql_user, (user_id,))
        
        # user_prediction 테이블의 risk_score를 HIGH로 업데이트
        # 테이블에 레코드가 없으면 생성
        sql_prediction = """
        INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
        VALUES (%s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            risk_score = 'HIGH',
            update_date = CURDATE()
        """
        cursor.execute(sql_prediction, (user_id, 100, 'HIGH'))
        
        # log 테이블에 구독해지 기록
        additional_info = f"reason: {reason}, feedback: {feedback}" if reason or feedback else None
        sql_log = """
        INSERT INTO log (user_id, action_type, page_name, additional_info)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_log, (user_id, 'UNSUBSCRIBE', '개인정보 수정', additional_info))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "구독해지가 처리되었습니다. 휴면 유저로 전환되었고 이탈 위험도가 높음으로 설정되었습니다."
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "error": f"구독해지 처리 중 오류: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
    특정 user_id의 ML 학습용 전체 피처 데이터를 user_features 테이블에서 조회해 반환합니다.
    관리자 페이지에서 '불러오기' 후 '수치 조정(시뮬레이션)'을 할 때 사용합니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # user_features 테이블에서 조회
        cursor.execute(
            """
            SELECT *
            FROM user_features
            WHERE user_id = %s
            """,
            (user_id,)
        )
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            # 테이블에 없으면 CSV에서 조회 (하위 호환성)
            csv_path = os.path.join("data", "processed", "enhanced_data_not_clean_FE_delete.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                user_row = df[df["user_id"] == user_id]
                if not user_row.empty:
                    user_data = user_row.fillna(0).iloc[0].to_dict()
                    return jsonify({"success": True, "data": user_data})
            
            return jsonify({"success": False, "error": f"user_features에서 user_id={user_id}를 찾을 수 없습니다."}), 404
        
        # dict로 변환
        user_data = dict(row)
        
        return jsonify({"success": True, "data": user_data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 예측 API (전체 모델 이탈 확률 조회용 - 단일 행 / 풀 피처)
# -------------------------------------------------------------
@app.route("/api/predict_churn", methods=["POST"])
def api_predict_churn():
    """
    단일 유저(1행)의 전체 피처 + 사용할 모델 이름을 받아
    - 이탈 확률(churn_prob)
    - 위험도 레벨(risk_level)
    을 반환하는 API.

    user_id가 제공되면 user_features 테이블에서 조회하여 사용합니다.
    예측 결과는 user_prediction 테이블에 저장됩니다.

    Request JSON 예시 (단일 행):
    {
      "user_id": 123,             # 선택적, 제공 시 user_features에서 조회
      "model_name": "hgb",        # 선택 사항 (미입력 시 config.DEFAULT_MODEL_NAME 사용)
      "features": {               # user_id가 없을 때만 사용
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
        user_id = payload.get("user_id")
        features = payload.get("features") or {}

        # user_id가 제공되면 user_features 테이블에서 조회
        if user_id:
            try:
                conn = get_connection()
                cursor = conn.cursor(DictCursor)
                cursor.execute("SELECT * FROM user_features WHERE user_id = %s", (user_id,))
                db_features = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if db_features:
                    # DB에서 조회한 데이터를 features로 사용
                    features = dict(db_features)
                    # user_id는 제거 (예측 함수에 전달하지 않음)
                    features.pop('user_id', None)
                else:
                    return jsonify({"success": False, "error": f"user_features에서 user_id={user_id}를 찾을 수 없습니다."}), 404
            except Exception as e:
                return jsonify({"success": False, "error": f"user_features 조회 중 오류: {str(e)}"}), 500

        if not isinstance(features, dict):
            return jsonify({"success": False, "error": "features 필드는 dict 형태여야 합니다."}), 400

        from inference import predict_churn as _predict_churn

        result = _predict_churn(user_features=features)

        if not result.get("success"):
            status_code = 500
            return jsonify(result), status_code

        # 예측 결과를 user_prediction 테이블에 저장
        if user_id:
            try:
                churn_prob = result.get("churn_prob", 0.0)
                churn_rate = int(round(churn_prob * 100))  # 0~100 (%)
                risk_score = result.get("risk_level", "UNKNOWN")
                
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
            except Exception as e:
                # 저장 실패해도 예측 결과는 반환
                pass

        # 응답에 model_name 추가 (기본값: "hgb")
        if result.get("success"):
            result["model_name"] = model_name or "hgb"
        
        status_code = 200
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"success": False, "error": f"예측 중 오류 발생: {str(e)}"}), 500


# -------------------------------------------------------------
# 예측 API (전체 모델 - 여러 행 / 배치 예측용)
# -------------------------------------------------------------
@app.route("/api/predict_churn_bulk", methods=["POST"])
def api_predict_churn_bulk():
    """
    여러 행(여러 유저)의 피처 리스트를 받아
    - 각 행의 이탈 확률(churn_prob)
    - 위험도 레벨(risk_level)
    을 한 번에 반환하는 배치 예측 API.

    각 행에 user_id가 있으면 user_features 테이블에서 조회하여 사용합니다.
    예측 결과는 user_prediction 테이블에 저장됩니다.

    Request JSON 예시:
    {
      "model_name": "hgb",          # 선택 사항 (미입력 시 config.DEFAULT_MODEL_NAME 사용)
      "rows": [
        {
          "user_id": 123,           # user_id가 있으면 user_features에서 조회
          "listening_time": 180,    # user_id가 없을 때만 사용
          "songs_played_per_day": 40,
          ...
        },
        {
          "user_id": 124,
          ...
        }
      ]
    }

    Response JSON 예시:
    {
      "success": true,
      "model_name": "hgb",
      "results": [
        {
          "index": 0,
          "user_id": 123,
          "churn_prob": 0.73,
          "risk_level": "HIGH"
        },
        {
          "index": 1,
          "user_id": 124,
          "churn_prob": 0.21,
          "risk_level": "LOW"
        }
      ]
    }
    """
    try:
        payload = request.get_json(force=True) or {}
        model_name = payload.get("model_name")
        rows = payload.get("rows") or []

        if not isinstance(rows, list):
            return jsonify({"success": False, "error": "rows 필드는 리스트 형태여야 합니다."}), 400

        from inference import predict_churn as _predict_churn

        import math
        import numpy as np
        
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        results = []
        prediction_inserts = []  # 배치로 저장할 예측 결과들
        
        total_rows = len(rows)
        print(f"[배치 예측 시작] 총 {total_rows}개 유저 예측 시작")
        
        # 1단계: user_id가 있는 행들을 수집하고, 한 번에 DB에서 조회 (성능 최적화)
        user_ids_to_fetch = []
        row_indices_with_user_id = {}  # {user_id: [index1, index2, ...]}
        rows_with_features = {}  # {index: features_dict}
        rows_without_user_id = {}  # {index: row_dict}
        
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                results.append({
                    "index": idx,
                    "user_id": None,
                    "error": "행이 dict 형태가 아닙니다."
                })
                continue
            
            user_id = row.get("user_id")
            if user_id is not None:
                if user_id not in user_ids_to_fetch:
                    user_ids_to_fetch.append(user_id)
                if user_id not in row_indices_with_user_id:
                    row_indices_with_user_id[user_id] = []
                row_indices_with_user_id[user_id].append(idx)
            else:
                # user_id가 없으면 직접 제공된 features 사용
                rows_without_user_id[idx] = row
        
        # 2단계: 모든 user_id를 한 번에 조회 (배치 쿼리)
        user_features_dict = {}  # {user_id: features_dict}
        if user_ids_to_fetch:
            print(f"[배치 예측] {len(user_ids_to_fetch)}개 유저의 피처를 한 번에 조회 중...")
            placeholders = ','.join(['%s'] * len(user_ids_to_fetch))
            cursor.execute(f"SELECT * FROM user_features WHERE user_id IN ({placeholders})", user_ids_to_fetch)
            db_rows = cursor.fetchall()
            for db_row in db_rows:
                user_id = db_row['user_id']
                features = dict(db_row)
                features.pop('user_id', None)  # 예측 함수에 전달하지 않음
                user_features_dict[user_id] = features
        
        # 3단계: 전처리기와 모델을 한 번만 로드 (성능 최적화)
        import inference
        
        inference._load_artifacts_if_needed()
        effective_model_name = (model_name or inference.DEFAULT_MODEL_NAME).lower()
        model = inference._get_or_train_model(effective_model_name)
        
        if not hasattr(model, "predict_proba"):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"모델 '{effective_model_name}' 은 predict_proba를 지원하지 않습니다."}), 500
        
        # 4단계: 배치 예측 수행
        print(f"[배치 예측] 배치 예측 시작...")
        all_features_list = []
        all_indices = []
        all_user_ids = []
        
        # user_id가 있는 행들 처리
        for user_id, indices in row_indices_with_user_id.items():
            if user_id in user_features_dict:
                features = user_features_dict[user_id]
                for idx in indices:
                    all_features_list.append(features)
                    all_indices.append(idx)
                    all_user_ids.append(user_id)
            else:
                # DB에서 찾을 수 없는 경우
                for idx in indices:
                    results.append({
                        "index": idx,
                        "user_id": user_id,
                        "error": f"user_features에서 user_id={user_id}를 찾을 수 없습니다."
                    })
        
        # user_id가 없는 행들 처리 (직접 제공된 features)
        for idx, row in rows_without_user_id.items():
            cleaned_row = {}
            # NaN, inf, -inf 값 정리
            for key, value in row.items():
                if key == "user_id":
                    continue  # user_id는 제외
                
                if value is None:
                    cleaned_row[key] = None
                elif isinstance(value, (int, float)):
                    if math.isnan(value) or math.isinf(value):
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = value
                else:
                    # pandas의 NaN 체크 (안전하게)
                    try:
                        if pd.isna(value):
                            cleaned_row[key] = None
                        else:
                            cleaned_row[key] = value
                    except (TypeError, ValueError):
                        # pd.isna()가 실패하면 그냥 값 사용
                        cleaned_row[key] = value
            
            all_features_list.append(cleaned_row)
            all_indices.append(idx)
            all_user_ids.append(None)
        
        # 5단계: 모든 유저를 한 번에 전처리 및 예측 (배치 처리)
        if all_features_list:
            try:
                # 모든 유저의 DataFrame 생성
                X_df_list = []
                for features in all_features_list:
                    X_df = inference._build_input_dataframe(features)
                    X_df_list.append(X_df)
                
                # DataFrame들을 합치기
                X_df_batch = pd.concat(X_df_list, ignore_index=True)
                
                # 배치 전처리
                X_transformed = inference._PREPROCESSOR.transform(X_df_batch)
                
                # 배치 예측
                probas = model.predict_proba(X_transformed)[:, 1]
                
                # 결과 처리
                for i, (idx, user_id, proba) in enumerate(zip(all_indices, all_user_ids, probas)):
                    proba = float(proba)
                    if math.isnan(proba) or math.isinf(proba):
                        proba = 0.0
                    proba = max(0.0, min(1.0, proba))
                    
                    risk_level = inference._prob_to_risk_level(proba)
                    
                    results.append({
                        "index": idx,
                        "user_id": user_id,
                        "churn_prob": proba,
                        "risk_level": risk_level
                    })
                    
                    # user_id가 있으면 예측 결과 저장 준비
                    if user_id is not None:
                        try:
                            churn_rate = int(round(proba * 100))
                            prediction_inserts.append((user_id, churn_rate, risk_level))
                        except Exception as e:
                            print(f"예측 결과 저장 준비 중 오류 (user_id={user_id}): {str(e)}")
            
            except Exception as e:
                import traceback
                error_msg = f"배치 예측 실행 중 오류: {str(e)}"
                print(f"배치 예측 오류: {error_msg}")
                print(traceback.format_exc())
                # 오류 발생 시 개별 처리로 폴백
                for idx, user_id in zip(all_indices, all_user_ids):
                    results.append({
                        "index": idx,
                        "user_id": user_id,
                        "error": error_msg
                    })
        
        # 결과를 index 순서로 정렬
        results.sort(key=lambda x: x.get("index", 0))
        
        cursor.close()
        
        # 배치로 user_prediction 테이블에 저장
        saved_count = 0
        if prediction_inserts:
            print(f"[배치 예측 저장] {len(prediction_inserts)}개 예측 결과 DB 저장 시작")
            try:
                cursor = conn.cursor()
                sql = """
                INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
                VALUES (%s, %s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE
                    churn_rate = VALUES(churn_rate),
                    risk_score = VALUES(risk_score),
                    update_date = CURDATE()
                """
                cursor.executemany(sql, prediction_inserts)
                conn.commit()
                saved_count = len(prediction_inserts)
                cursor.close()
                print(f"[배치 예측 저장 완료] {saved_count}개 예측 결과 저장됨")
            except Exception as e:
                # 저장 실패해도 예측 결과는 반환 (에러는 로그에 기록)
                import traceback
                print(f"[배치 예측 저장 오류] {str(e)}")
                print(traceback.format_exc())
        else:
            print(f"[배치 예측 저장] 저장할 예측 결과 없음")
        
        conn.close()
        
        success_count = len([r for r in results if "error" not in r])
        error_count = len([r for r in results if "error" in r])
        print(f"[배치 예측 완료] 총 {total_rows}개 처리 완료 - 성공: {success_count}, 실패: {error_count}, 저장: {saved_count}")

        response_data = {
            "success": True,
            "model_name": (model_name or "default"),
            "results": results,
            "saved_count": saved_count
        }
        return jsonify(response_data), 200

    except Exception as e:
        import traceback
        error_msg = f"배치 예측 중 오류 발생: {str(e)}"
        print(f"배치 예측 전체 오류: {error_msg}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500


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

        from inference_sim_6feat_lgbm import predict_churn_6feat_lgbm

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
# user_prediction 단일행 조회 API (TB에서 위험도 및 userData 호출)
# -------------------------------------------------------------
@app.route("/api/user_prediction/<int:user_id>", methods=["GET"])
def get_user_prediction(user_id):
    """
    user_prediction 테이블에서 특정 user_id(단일 행)의
    - user_id
    - churn_rate
    - risk_score
    - update_date
    를 조회해서 반환합니다.

    화면에서 입력받은 User PK 값으로 단일 행을 조회할 때 사용합니다.

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
        error_msg = str(e)
        # 테이블이 없는 경우 명확한 메시지
        if "doesn't exist" in error_msg.lower() or "table" in error_msg.lower() or "unknown table" in error_msg.lower():
            error_msg = "user_prediction 테이블이 존재하지 않습니다. 먼저 테이블을 생성해주세요. (사용자 데이터 관리 > User Prediction Table 생성)"
        return jsonify({"success": False, "error": f"user_prediction 조회 중 오류: {error_msg}"}), 500


# -------------------------------------------------------------
# user_prediction 다건/전체 조회 API
# -------------------------------------------------------------
@app.route("/api/user_prediction", methods=["GET"])
def get_user_prediction_list():
    """
    user_prediction 테이블에서 여러 행 또는 전체 행을 조회합니다.

    - 쿼리스트링에 user_ids 파라미터를 주면 해당 ID 들만 조회
      예) /api/user_prediction?user_ids=1,5,10
    - user_ids 를 생략하면 user_prediction 전체 행을 반환

    Response 예시:
    {
      "success": true,
      "rows": [
        {
          "user_id": 123,
          "churn_rate": 45,
          "risk_score": "MEDIUM",
          "update_date": "2025-11-24"
        },
        ...
      ]
    }
    """
    try:
        user_ids_param = request.args.get("user_ids", "").strip()

        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        if user_ids_param:
            # user_ids=1,2,3 형태를 파싱
            try:
                id_list = [int(x) for x in user_ids_param.split(",") if x.strip()]
            except ValueError:
                return jsonify({"success": False, "error": "user_ids 는 쉼표로 구분된 정수 목록이어야 합니다."}), 400

            if not id_list:
                return jsonify({"success": True, "rows": []}), 200

            placeholders = ",".join(["%s"] * len(id_list))
            sql = f"""
                SELECT user_id, churn_rate, risk_score, update_date
                FROM user_prediction
                WHERE user_id IN ({placeholders})
                ORDER BY user_id ASC
            """
            cursor.execute(sql, tuple(id_list))
        else:
            # 전체 행 조회
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

        # DATE → 문자열 변환
        for row in rows:
            if "update_date" in row and row["update_date"] is not None:
                row["update_date"] = row["update_date"].isoformat()

        return jsonify({"success": True, "rows": rows}), 200

    except Exception as e:
        error_msg = str(e)
        # 테이블이 없는 경우 명확한 메시지
        if "doesn't exist" in error_msg.lower() or "table" in error_msg.lower():
            error_msg = "user_prediction 테이블이 존재하지 않습니다. 먼저 테이블을 생성해주세요. (사용자 데이터 관리 > User Prediction Table 생성)"
        return jsonify({"success": False, "error": f"user_prediction 목록 조회 중 오류: {error_msg}"}), 500


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

        from inference_sim_6feat_lgbm import predict_churn_6feat_lgbm

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
# -------------------------------------------------------------
# 테스트용: 위험도 설정 및 임시 계정 추가 API
# -------------------------------------------------------------
@app.route("/api/setup_test_accounts", methods=["POST"])
def setup_test_accounts():
    """
    테스트용 계정들의 위험도를 HIGH로 설정하고, 
    다양한 구독 유형의 임시 계정을 추가합니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # test2 계정의 user_id 찾기 (name이 'test2' 또는 'Test User'인 경우)
        cursor.execute("SELECT user_id, name FROM users WHERE name = 'test2' OR name = 'Test User' LIMIT 1")
        test2_user = cursor.fetchone()
        
        results = []
        
        # test2 계정 위험도 HIGH 설정
        if test2_user:
            test2_user_id = test2_user['user_id']
            test2_name = test2_user['name']
            sql = """
            INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
            VALUES (%s, %s, %s, CURDATE())
            ON DUPLICATE KEY UPDATE
                churn_rate = VALUES(churn_rate),
                risk_score = VALUES(risk_score),
                update_date = CURDATE()
            """
            cursor.execute(sql, (test2_user_id, 80, 'HIGH'))
            results.append(f"test2 ({test2_name}, user_id: {test2_user_id}) 위험도 HIGH 설정 완료")
        else:
            # user_id = 1인 계정도 시도 (test2 임시 계정의 기본 user_id)
            cursor.execute("SELECT user_id, name FROM users WHERE user_id = 1 LIMIT 1")
            user_1 = cursor.fetchone()
            if user_1:
                sql = """
                INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
                VALUES (%s, %s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE
                    churn_rate = VALUES(churn_rate),
                    risk_score = VALUES(risk_score),
                    update_date = CURDATE()
                """
                cursor.execute(sql, (1, 80, 'HIGH'))
                results.append(f"user_id=1 ({user_1['name']}) 위험도 HIGH 설정 완료")
            else:
                results.append("test2 계정을 찾을 수 없습니다.")
        
        # 임시 계정들 추가 (다양한 구독 유형)
        test_accounts = [
            {"name": "test_free_high", "password": "test123", "favorite_music": "Pop", "grade": "01", "subscription_type": "Free"},
            {"name": "test_premium_high", "password": "test123", "favorite_music": "Rock", "grade": "01", "subscription_type": "Premium"},
            {"name": "test_free2_high", "password": "test123", "favorite_music": "Jazz", "grade": "01", "subscription_type": "Free"},
            {"name": "test_premium2_high", "password": "test123", "favorite_music": "Classical", "grade": "01", "subscription_type": "Premium"},
        ]
        
        import bcrypt
        from datetime import date
        
        for account in test_accounts:
            # 계정이 이미 존재하는지 확인
            cursor.execute("SELECT user_id FROM users WHERE name = %s", (account["name"],))
            existing = cursor.fetchone()
            
            if existing:
                user_id = existing['user_id']
                results.append(f"{account['name']} 계정이 이미 존재합니다. (user_id: {user_id})")
            else:
                # 새 계정 생성
                hashed_password = bcrypt.hashpw(account["password"].encode("utf-8"), bcrypt.gensalt())
                cursor.execute("""
                    INSERT INTO users (name, favorite_music, password, join_date, modify_date, grade)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    account["name"],
                    account["favorite_music"],
                    hashed_password,
                    date.today(),
                    date.today(),
                    account["grade"]
                ))
                user_id = cursor.lastrowid
                results.append(f"{account['name']} 계정 생성 완료 (user_id: {user_id})")
            
            # user_features 테이블에 구독 유형 추가
            cursor.execute("""
                INSERT INTO user_features (user_id, subscription_type)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE subscription_type = VALUES(subscription_type)
            """, (user_id, account["subscription_type"]))
            
            # user_prediction 테이블에 위험도 HIGH 설정
            cursor.execute("""
                INSERT INTO user_prediction (user_id, churn_rate, risk_score, update_date)
                VALUES (%s, %s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE
                    churn_rate = VALUES(churn_rate),
                    risk_score = VALUES(risk_score),
                    update_date = CURDATE()
            """, (user_id, 75, 'HIGH'))
            results.append(f"  - {account['name']} 위험도 HIGH 설정 완료 (구독 유형: {account['subscription_type']})")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "테스트 계정 설정 완료",
            "results": results
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": f"테스트 계정 설정 중 오류: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500


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
# Spotify Callback
# -------------------------------------------------------------
@app.route('/spotify/callback')
def spotify_callback():
    """
    Spotify 인증 콜백을 처리하고 Streamlit 앱으로 리다이렉트
    """
    code = request.args.get('code')
    error = request.args.get('error')
    
    # Streamlit 앱 URL (환경 변수 또는 기본값)
    STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")
    
    if error:
        return redirect(f"{STREAMLIT_URL}/?error={error}")
    
    if code:
        return redirect(f"{STREAMLIT_URL}/?code={code}")
    
    return redirect(STREAMLIT_URL)

# -------------------------------------------------------------
# Spotify Search Proxy
# -------------------------------------------------------------
@app.route('/api/music/search', methods=['GET'])
def search_music():
    query = request.args.get('q')
    access_token = request.headers.get('Authorization') # Bearer token expected
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
        
    if not access_token:
         # 헤더가 없으면 쿼리 파라미터에서 확인 (선택적)
         access_token = request.args.get('token')
         if access_token and not access_token.startswith("Bearer "):
             access_token = "Bearer " + access_token

    if not access_token:
        return jsonify({"error": "Authorization header or token is required"}), 401

    try:
        # Spotify API 호출
        spotify_url = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": access_token
        }
        params = {
            "q": query,
            "type": "track",
            "limit": request.args.get('limit', 20),
            "offset": request.args.get('offset', 0)
        }
        
        res = requests.get(spotify_url, headers=headers, params=params)
        
        if res.status_code != 200:
            return jsonify(res.json()), res.status_code
            
        data = res.json()
        tracks = data.get("tracks", {}).get("items", [])
        
        return jsonify({"tracks": tracks})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------
# 도전과제 관련 API
# -------------------------------------------------------------

# -------------------------------------------------------------
# 노래 재생 로그 기록 API
# -------------------------------------------------------------
@app.route("/api/music/playback", methods=["POST"])
def log_music_playback():
    """
    노래 재생 로그를 기록하고 도전과제 달성 여부를 체크합니다.
    
    Request JSON:
    {
        "user_id": 123,
        "track_uri": "spotify:track:...",
        "track_name": "노래 제목",
        "artist_name": "아티스트 이름",
        "genre": "Pop" (선택적),
        "playback_duration": 180 (초, 선택적)
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        track_uri = data.get("track_uri")
        track_name = data.get("track_name", "")
        artist_name = data.get("artist_name", "")
        genre = data.get("genre")
        playback_duration = data.get("playback_duration", 0)
        
        if not user_id or not track_uri:
            return jsonify({"success": False, "error": "user_id와 track_uri는 필수입니다."}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 재생 로그 기록 및 도전과제 체크를 하나의 트랜잭션으로 처리
        try:
            # 재생 로그 기록
            sql = """
            INSERT INTO music_playback_log (user_id, track_uri, track_name, artist_name, genre, playback_duration)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, track_uri, track_name, artist_name, genre, playback_duration))
            
            # 도전과제 달성 체크 (같은 트랜잭션 내에서)
            completed_achievements = check_and_update_achievements(
                cursor, conn, user_id, track_uri, genre
            )
            
            # 모든 작업이 성공하면 커밋
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
        return jsonify({
            "success": True,
            "message": "재생 로그가 기록되었습니다.",
            "completed_achievements": completed_achievements
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"재생 로그 기록 중 오류: {str(e)}"}), 500


def check_and_update_achievements(cursor, conn, user_id, track_uri, genre):
    """
    도전과제 달성 여부를 체크하고 업데이트합니다. (최적화: 배치 쿼리 사용)
    
    Returns:
        list: 새로 달성한 도전과제 목록
    """
    completed_achievements = []
    
    try:
        # 활성화된 모든 도전과제 조회
        cursor.execute("""
            SELECT achievement_id, achievement_type, target_value, target_track_uri, target_genre,
                   title, description, reward_points
            FROM achievements
            WHERE is_active = TRUE
        """)
        achievements = cursor.fetchall()
        
        if not achievements:
            return completed_achievements
        
        # 사용자의 모든 도전과제 진행 상황을 한 번에 조회
        achievement_ids = [a[0] for a in achievements]
        placeholders = ','.join(['%s'] * len(achievement_ids))
        cursor.execute(f"""
            SELECT achievement_id, user_achievement_id, current_progress, is_completed
            FROM user_achievements
            WHERE user_id = %s AND achievement_id IN ({placeholders})
        """, (user_id, *achievement_ids))
        
        user_achievements_dict = {row[0]: row for row in cursor.fetchall()}
        
        # 업데이트할 데이터 준비
        updates = []
        inserts = []
        completed_info = []
        
        for achievement in achievements:
            achievement_id = achievement[0]
            achievement_type = achievement[1]
            target_value = achievement[2]
            target_track_uri = achievement[3]
            target_genre = achievement[4]
            title = achievement[5]
            description = achievement[6]
            reward_points = achievement[7]
            
            # 진행도 증가 여부 확인
            should_update = False
            if achievement_type == "TRACK_PLAY" and target_track_uri and track_uri == target_track_uri:
                should_update = True
            elif achievement_type == "GENRE_PLAY" and target_genre and genre and target_genre.lower() == genre.lower():
                should_update = True
            
            if not should_update:
                continue
            
            # 기존 진행 상황 확인
            if achievement_id in user_achievements_dict:
                user_achievement_id, current_progress, is_completed = user_achievements_dict[achievement_id][1:]
                if is_completed:
                    continue  # 이미 완료된 도전과제는 스킵
                current_progress += 1
            else:
                # 새로운 도전과제 시작
                current_progress = 1
                user_achievement_id = None
                is_completed = False
            
            # 완료 여부 확인
            if current_progress >= target_value:
                is_completed = True
                completed_info.append({
                    "achievement_id": achievement_id,
                    "title": title,
                    "description": description,
                    "reward_points": reward_points
                })
            
            # INSERT 또는 UPDATE 데이터 준비
            if user_achievement_id:
                updates.append((current_progress, is_completed, user_achievement_id))
            else:
                inserts.append((user_id, achievement_id, current_progress, is_completed))
        
        # 배치 UPDATE
        if updates:
            cursor.executemany("""
                UPDATE user_achievements
                SET current_progress = %s,
                    is_completed = %s,
                    completed_at = CASE WHEN %s = TRUE AND completed_at IS NULL THEN NOW() ELSE completed_at END
                WHERE user_achievement_id = %s
            """, [(pc, ic, ic, uaid) for pc, ic, uaid in updates])
        
        # 배치 INSERT
        if inserts:
            cursor.executemany("""
                INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed, completed_at)
                VALUES (%s, %s, %s, %s, CASE WHEN %s = TRUE THEN NOW() ELSE NULL END)
            """, [(uid, aid, pc, ic, ic) for uid, aid, pc, ic in inserts])
        
        if updates or inserts:
            conn.commit()
            completed_achievements = completed_info
    
    except Exception as e:
        # 도전과제 체크 실패해도 재생 로그는 기록됨
        print(f"도전과제 체크 중 오류: {str(e)}")
    
    return completed_achievements


# -------------------------------------------------------------
# 도전과제 목록 조회 API
# -------------------------------------------------------------
@app.route("/api/achievements", methods=["GET"])
def get_achievements():
    """
    도전과제 목록을 조회합니다.
    
    Query Parameters:
    - user_id: 특정 사용자의 도전과제 진행 상황 포함 (선택적)
    - is_active: 활성화된 도전과제만 조회 (기본값: true)
    """
    try:
        user_id = request.args.get("user_id", "").strip()
        is_active = request.args.get("is_active", "true").lower() == "true"
        
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # 기본 쿼리
        where_clause = "WHERE 1=1"
        params = []
        
        if is_active:
            where_clause += " AND a.is_active = TRUE"
        
        sql = f"""
        SELECT a.achievement_id, a.title, a.description, a.achievement_type,
               a.target_value, a.target_track_uri, a.target_genre, a.reward_points,
               a.is_active, a.created_at
        FROM achievements a
        {where_clause}
        ORDER BY a.achievement_id ASC
        """
        
        cursor.execute(sql, tuple(params))
        achievements = cursor.fetchall()
        
        # 사용자 ID가 제공된 경우 진행 상황 포함
        if user_id and user_id.isdigit():
            user_id_int = int(user_id)
            for achievement in achievements:
                achievement_id = achievement["achievement_id"]
                cursor.execute("""
                    SELECT current_progress, is_completed, completed_at, created_at
                    FROM user_achievements
                    WHERE user_id = %s AND achievement_id = %s
                """, (user_id_int, achievement_id))
                
                user_progress = cursor.fetchone()
                if user_progress:
                    achievement["user_progress"] = user_progress.get("current_progress", 0)
                    achievement["is_completed"] = user_progress.get("is_completed", False)
                    achievement["completed_at"] = user_progress["completed_at"].isoformat() if user_progress.get("completed_at") else None
                    achievement["started_at"] = user_progress["created_at"].isoformat() if user_progress.get("created_at") else None
                else:
                    achievement["user_progress"] = 0
                    achievement["is_completed"] = False
                    achievement["completed_at"] = None
                    achievement["started_at"] = None
        
        cursor.close()
        conn.close()
        
        # DATETIME → 문자열 변환
        for achievement in achievements:
            if "created_at" in achievement and achievement.get("created_at"):
                achievement["created_at"] = achievement["created_at"].isoformat()
        
        return jsonify({"success": True, "achievements": achievements})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"도전과제 조회 오류: {error_detail}")
        return jsonify({"success": False, "error": f"도전과제 조회 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 사용자 도전과제 진행 상황 조회 API
# -------------------------------------------------------------
@app.route("/api/achievements/<int:achievement_id>/statistics", methods=["GET"])
def get_achievement_statistics(achievement_id):
    """
    특정 도전과제의 달성 통계를 조회합니다.
    
    Returns:
    {
        "achievement_id": 1,
        "total_users": 100,  # 전체 사용자 수
        "completed_count": 15,  # 달성한 사용자 수
        "in_progress_count": 20,  # 진행 중인 사용자 수
        "completion_rate": 15.0,  # 달성률 (%)
        "completed_users": [  # 달성한 사용자 목록
            {"user_id": 1, "name": "홍길동", "completed_at": "2025-01-01"},
            ...
        ]
    }
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # 도전과제 정보 조회
        cursor.execute("""
            SELECT achievement_id, title, target_value
            FROM achievements
            WHERE achievement_id = %s
        """, (achievement_id,))
        
        achievement = cursor.fetchone()
        if not achievement:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "도전과제를 찾을 수 없습니다."}), 404
        
        # 전체 사용자 수
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE grade != '00'")
        total_users = cursor.fetchone()["total"]
        
        # 달성한 사용자 수 및 목록
        cursor.execute("""
            SELECT ua.user_id, u.name, ua.completed_at
            FROM user_achievements ua
            JOIN users u ON ua.user_id = u.user_id
            WHERE ua.achievement_id = %s AND ua.is_completed = TRUE
            ORDER BY ua.completed_at DESC
        """, (achievement_id,))
        completed_users = cursor.fetchall()
        completed_count = len(completed_users)
        
        # 진행 중인 사용자 수
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM user_achievements
            WHERE achievement_id = %s AND is_completed = FALSE
        """, (achievement_id,))
        in_progress_count = cursor.fetchone()["count"]
        
        # 달성률 계산
        completion_rate = (completed_count / total_users * 100) if total_users > 0 else 0
        
        cursor.close()
        conn.close()
        
        # DATETIME → 문자열 변환
        for user in completed_users:
            if user.get("completed_at"):
                user["completed_at"] = user["completed_at"].isoformat()
        
        return jsonify({
            "success": True,
            "achievement_id": achievement_id,
            "title": achievement["title"],
            "target_value": achievement["target_value"],
            "total_users": total_users,
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "completion_rate": round(completion_rate, 2),
            "completed_users": completed_users
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"도전과제 통계 조회 오류: {error_detail}")
        return jsonify({"success": False, "error": f"도전과제 통계 조회 중 오류: {str(e)}"}), 500


@app.route("/api/users/<int:user_id>/achievements", methods=["GET"])
def get_user_achievements(user_id):
    """
    특정 사용자의 도전과제 진행 상황을 조회합니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # 테이블 존재 여부 확인
        try:
            cursor.execute("SELECT 1 FROM achievements LIMIT 1")
        except Exception as table_error:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False, 
                "error": "achievements 테이블이 존재하지 않습니다. 먼저 테이블을 생성해주세요."
            }), 500
        
        sql = """
        SELECT a.achievement_id, a.title, a.description, a.achievement_type,
               a.target_value, a.target_track_uri, a.target_genre, a.reward_points,
               ua.current_progress, ua.is_completed, ua.completed_at, ua.created_at AS started_at
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.achievement_id = ua.achievement_id AND ua.user_id = %s
        WHERE a.is_active = TRUE
        ORDER BY a.achievement_id ASC
        """
        
        cursor.execute(sql, (user_id,))
        achievements = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # DATETIME → 문자열 변환 및 None 값 처리
        for achievement in achievements:
            # None 값 안전하게 처리
            if achievement.get("completed_at") is not None:
                achievement["completed_at"] = achievement["completed_at"].isoformat()
            else:
                achievement["completed_at"] = None
                
            if achievement.get("started_at") is not None:
                achievement["started_at"] = achievement["started_at"].isoformat()
            else:
                achievement["started_at"] = None
                
            if achievement.get("current_progress") is None:
                achievement["current_progress"] = 0
                
            if achievement.get("is_completed") is None:
                achievement["is_completed"] = False
        
        return jsonify({"success": True, "achievements": achievements})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"사용자 도전과제 조회 오류: {error_detail}")
        return jsonify({"success": False, "error": f"사용자 도전과제 조회 중 오류: {str(e)}"}), 500


# -------------------------------------------------------------
# 도전과제 생성 API (관리자용)
# -------------------------------------------------------------
@app.route("/api/achievements/<int:achievement_id>", methods=["DELETE"])
def delete_achievement(achievement_id):
    """
    도전과제를 삭제합니다. (관리자용)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 도전과제 존재 여부 확인
        cursor.execute("SELECT achievement_id FROM achievements WHERE achievement_id = %s", (achievement_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "도전과제를 찾을 수 없습니다."}), 404
        
        # 도전과제 삭제 (CASCADE로 user_achievements도 함께 삭제됨)
        cursor.execute("DELETE FROM achievements WHERE achievement_id = %s", (achievement_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "도전과제가 삭제되었습니다."
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"도전과제 삭제 오류: {error_detail}")
        return jsonify({"success": False, "error": f"도전과제 삭제 중 오류: {str(e)}"}), 500


@app.route("/api/achievements", methods=["POST"])
def create_achievement():
    """
    새로운 도전과제를 생성합니다. (관리자용)
    
    Request JSON:
    {
        "title": "도전과제 제목",
        "description": "도전과제 설명",
        "achievement_type": "TRACK_PLAY" | "GENRE_PLAY",
        "target_value": 10,
        "target_track_uri": "spotify:track:..." (TRACK_PLAY인 경우),
        "target_genre": "Pop" (GENRE_PLAY인 경우),
        "reward_points": 100
    }
    """
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description", "")
        achievement_type = data.get("achievement_type")
        target_value = data.get("target_value")
        target_track_uri = data.get("target_track_uri")
        target_genre = data.get("target_genre")
        reward_points = data.get("reward_points", 0)
        
        if not title or not achievement_type or not target_value:
            return jsonify({"success": False, "error": "title, achievement_type, target_value는 필수입니다."}), 400
        
        if achievement_type == "TRACK_PLAY" and not target_track_uri:
            return jsonify({"success": False, "error": "TRACK_PLAY 타입은 target_track_uri가 필요합니다."}), 400
        
        if achievement_type == "GENRE_PLAY" and not target_genre:
            return jsonify({"success": False, "error": "GENRE_PLAY 타입은 target_genre가 필요합니다."}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO achievements (title, description, achievement_type, target_value, 
                                 target_track_uri, target_genre, reward_points)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(sql, (title, description, achievement_type, target_value,
                            target_track_uri, target_genre, reward_points))
        conn.commit()
        achievement_id = cursor.lastrowid
        
        # 새로 생성된 도전과제에 대해 기존 재생 로그를 기반으로 모든 유저의 진행도 체크
        try:
            result = check_all_users_for_new_achievement(cursor, conn, achievement_id, achievement_type, target_track_uri, target_genre)
            print(f"도전과제 생성 후 기존 유저 진행도 체크 완료: {result.get('processed_users', 0)}명 처리, {result.get('completed_users', 0)}명 즉시 완료")
        except Exception as e:
            import traceback
            print(f"기존 유저 진행도 체크 중 오류 (도전과제는 생성됨): {str(e)}")
            traceback.print_exc()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "도전과제가 생성되었습니다.",
            "achievement_id": achievement_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"도전과제 생성 중 오류: {str(e)}"}), 500


def check_all_users_for_new_achievement(cursor, conn, achievement_id, achievement_type, target_track_uri, target_genre):
    """
    새로 생성된 도전과제에 대해 기존 재생 로그를 기반으로 모든 유저의 진행도를 체크하고 업데이트합니다.
    (배치 쿼리로 최적화)
    
    Args:
        cursor: DB 커서
        conn: DB 연결
        achievement_id: 새로 생성된 도전과제 ID
        achievement_type: 도전과제 타입 ("TRACK_PLAY" 또는 "GENRE_PLAY")
        target_track_uri: 목표 트랙 URI (TRACK_PLAY인 경우)
        target_genre: 목표 장르 (GENRE_PLAY인 경우)
    """
    processed_count = 0
    completed_count = 0
    
    try:
        print(f"[배치 도전과제 체크 시작] achievement_id={achievement_id}, type={achievement_type}")
        
        # 도전과제 정보 가져오기
        cursor.execute("""
            SELECT target_value
            FROM achievements
            WHERE achievement_id = %s
        """, (achievement_id,))
        achievement = cursor.fetchone()
        if not achievement:
            print(f"[배치 도전과제 체크] 도전과제 정보 없음 (achievement_id={achievement_id})")
            return {"processed_users": 0, "completed_users": 0}
        target_value = achievement[0]
        print(f"[배치 도전과제 체크] 목표 값: {target_value}")
        
        # 배치 쿼리로 모든 유저의 진행도 한 번에 계산
        if achievement_type == "TRACK_PLAY" and target_track_uri:
            print(f"[배치 도전과제 체크] 트랙 재생 횟수 조회 중 (track_uri={target_track_uri})")
            # 특정 트랙 재생 횟수를 배치로 계산
            cursor.execute("""
                SELECT 
                    m.user_id,
                    COUNT(*) AS play_count
                FROM music_playback_log m
                INNER JOIN users u ON m.user_id = u.user_id
                WHERE u.grade != '00' AND m.track_uri = %s
                GROUP BY m.user_id
            """, (target_track_uri,))
            
        elif achievement_type == "GENRE_PLAY" and target_genre:
            print(f"[배치 도전과제 체크] 장르 재생 횟수 조회 중 (genre={target_genre})")
            # 특정 장르 재생 횟수를 배치로 계산
            cursor.execute("""
                SELECT 
                    m.user_id,
                    COUNT(*) AS play_count
                FROM music_playback_log m
                INNER JOIN users u ON m.user_id = u.user_id
                WHERE u.grade != '00' AND LOWER(m.genre) = LOWER(%s)
                GROUP BY m.user_id
            """, (target_genre,))
        else:
            print(f"[배치 도전과제 체크] 잘못된 도전과제 타입 또는 파라미터")
            return {"processed_users": 0, "completed_users": 0}
        
        user_progresses = cursor.fetchall()
        total_users = len(user_progresses)
        print(f"[배치 도전과제 체크] {total_users}명 유저의 진행도 조회 완료")
        
        # 배치 INSERT를 위한 데이터 준비
        insert_data = []
        for row in user_progresses:
            user_id = row[0]
            play_count = row[1]
            
            if play_count > 0:
                is_completed = (play_count >= target_value)
                insert_data.append((user_id, achievement_id, play_count, is_completed))
        
        # 배치로 한 번에 INSERT/UPDATE
        if insert_data:
            # 완료된 것과 진행 중인 것을 분리하여 처리
            completed_data = [(uid, aid, pc) for uid, aid, pc, ic in insert_data if ic]
            in_progress_data = [(uid, aid, pc) for uid, aid, pc, ic in insert_data if not ic]
            
            print(f"[배치 도전과제 체크] 진행도 업데이트 준비 - 완료: {len(completed_data)}명, 진행중: {len(in_progress_data)}명")
            
            # 완료된 도전과제 배치 INSERT
            if completed_data:
                print(f"[배치 도전과제 체크] 완료된 도전과제 {len(completed_data)}명 DB 저장 중...")
                cursor.executemany("""
                    INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed, completed_at)
                    VALUES (%s, %s, %s, TRUE, NOW())
                    ON DUPLICATE KEY UPDATE
                        current_progress = VALUES(current_progress),
                        is_completed = TRUE,
                        completed_at = CASE WHEN completed_at IS NULL THEN NOW() ELSE completed_at END
                """, completed_data)
                completed_count = len(completed_data)
                print(f"[배치 도전과제 체크] 완료된 도전과제 {completed_count}명 저장 완료")
            
            # 진행 중인 도전과제 배치 INSERT
            if in_progress_data:
                print(f"[배치 도전과제 체크] 진행 중인 도전과제 {len(in_progress_data)}명 DB 저장 중...")
                cursor.executemany("""
                    INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed)
                    VALUES (%s, %s, %s, FALSE)
                    ON DUPLICATE KEY UPDATE
                        current_progress = VALUES(current_progress),
                        is_completed = FALSE
                """, in_progress_data)
                print(f"[배치 도전과제 체크] 진행 중인 도전과제 {len(in_progress_data)}명 저장 완료")
            
            conn.commit()
            processed_count = len(insert_data)
        else:
            print(f"[배치 도전과제 체크] 업데이트할 진행도 없음")
        
        print(f"[배치 도전과제 체크 완료] 처리된 유저: {processed_count}명, 완료된 유저: {completed_count}명")
        return {"processed_users": processed_count, "completed_users": completed_count}
        
    except Exception as e:
        print(f"기존 유저 진행도 체크 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"processed_users": processed_count, "completed_users": completed_count}


# -------------------------------------------------------------
# 칭호(도전과제) 선택 API
# -------------------------------------------------------------
@app.route("/api/users/<int:user_id>/selected_achievement", methods=["PUT"])
def update_selected_achievement(user_id):
    """
    사용자가 선택한 칭호(도전과제)를 업데이트합니다.
    
    Request JSON:
    {
        "achievement_id": 1 (선택한 도전과제 ID, null이면 칭호 해제)
    }
    """
    try:
        data = request.get_json()
        achievement_id = data.get("achievement_id")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # achievement_id가 None이면 칭호 해제
        if achievement_id is None:
            # selected_achievement_id를 NULL로 설정
            sql = """
            UPDATE users
            SET selected_achievement_id = NULL, modify_date = NOW()
            WHERE user_id = %s
            """
            cursor.execute(sql, (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({
                "success": True,
                "message": "칭호가 해제되었습니다.",
                "selected_achievement_id": None
            })
        
        # achievement_id가 제공된 경우, 해당 사용자가 완료한 도전과제인지 확인
        if achievement_id:
            cursor.execute("""
                SELECT is_completed
                FROM user_achievements
                WHERE user_id = %s AND achievement_id = %s AND is_completed = TRUE
            """, (user_id, achievement_id))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "완료하지 않은 도전과제는 칭호로 선택할 수 없습니다."
                }), 400
        
        # users 테이블에 selected_achievement_id 컬럼이 있는지 확인하고 없으면 추가
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN selected_achievement_id INT")
            conn.commit()
        except Exception as e:
            # 컬럼이 이미 존재하는 경우 무시
            pass
        
        # 외래키 제약조건 추가 (achievements 테이블이 존재하는 경우에만)
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_selected_achievement 
                FOREIGN KEY (selected_achievement_id) 
                REFERENCES achievements(achievement_id) 
                ON DELETE SET NULL
            """)
            conn.commit()
        except Exception as e:
            # 제약조건이 이미 존재하거나 achievements 테이블이 없는 경우 무시
            pass
        
        # selected_achievement_id 업데이트
        sql = """
        UPDATE users
        SET selected_achievement_id = %s, modify_date = NOW()
        WHERE user_id = %s
        """
        cursor.execute(sql, (achievement_id, user_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "칭호가 업데이트되었습니다.",
            "selected_achievement_id": achievement_id
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"칭호 업데이트 오류: {error_detail}")
        return jsonify({"success": False, "error": f"칭호 업데이트 중 오류: {str(e)}"}), 500


@app.route("/api/users/<int:user_id>/selected_achievement", methods=["GET"])
def get_selected_achievement(user_id):
    """
    사용자가 선택한 칭호(도전과제)를 조회합니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)
        
        # users 테이블에서 selected_achievement_id 조회
        cursor.execute("""
            SELECT selected_achievement_id
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "사용자를 찾을 수 없습니다."}), 404
        
        selected_achievement_id = user.get("selected_achievement_id")
        
        if selected_achievement_id:
            # 선택한 도전과제 정보 조회
            cursor.execute("""
                SELECT achievement_id, title, description, reward_points
                FROM achievements
                WHERE achievement_id = %s
            """, (selected_achievement_id,))
            
            achievement = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if achievement:
                return jsonify({
                    "success": True,
                    "selected_achievement": achievement
                })
            else:
                return jsonify({
                    "success": True,
                    "selected_achievement": None
                })
        else:
            cursor.close()
            conn.close()
            return jsonify({
                "success": True,
                "selected_achievement": None
            })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"칭호 조회 오류: {error_detail}")
        return jsonify({"success": False, "error": f"칭호 조회 중 오류: {str(e)}"}), 500






# -------------------------------------------------------------
# Flask 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000)
