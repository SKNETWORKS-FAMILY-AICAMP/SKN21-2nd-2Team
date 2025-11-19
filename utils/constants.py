"""
constants.py (공용 상수)
Auth: 박수빈
Date: 2025-11-18
Description
- 공용 상수 선언 파일
- 로컬 / 외부(팀원) 환경 자동 스위칭
"""

import os
import pymysql
from dotenv import load_dotenv

# -------------------------------------
# .env 파일 로드
# -------------------------------------
load_dotenv()

# -------------------------------------
# 현재 환경 설정 (LOCAL / TEAM)
# -------------------------------------
ENV = os.getenv("ENV", "LOCAL").upper()

# -------------------------------------
# 환경별 DB 설정
# -------------------------------------
if ENV == "LOCAL":
    # 로컬 개발 환경
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "test1234"),
        "db": os.getenv("DB_NAME", "skn21_2nd_team"),
        "charset": "utf8mb4"
    }

else:
    # 팀원 외부 접속 환경
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "192.168.0.152"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "team_user1"),
        "password": os.getenv("DB_PASSWORD", "test1234"),
        "db": os.getenv("DB_NAME", "skn21_2nd_team"),
        "charset": "utf8mb4"
    }

# -------------------------------------
# DB Connection 함수
# -------------------------------------
def get_connection():
    """MySQL DB 연결 생성"""
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor
    )
