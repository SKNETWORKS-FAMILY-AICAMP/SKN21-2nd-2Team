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
from pymysql.cursors import DictCursor
import threading

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
# 연결 풀 설정
# -------------------------------------
_connection_pool = None
_pool_lock = threading.Lock()

def _init_connection_pool():
    """연결 풀 초기화"""
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                # pymysql은 기본적으로 연결 풀을 지원하지 않으므로
                # 연결 재사용을 위한 최적화 설정
                _connection_pool = {
                    "config": DB_CONFIG,
                    "max_connections": 10,
                    "min_connections": 2
                }
    return _connection_pool

# -------------------------------------
# DB Connection 함수 (최적화)
# -------------------------------------
def get_connection():
    """
    MySQL DB 연결 생성 (연결 최적화)
    - autocommit=False: 트랜잭션 제어 가능
    - connect_timeout=5: 연결 타임아웃 설정
    - read_timeout=10: 읽기 타임아웃 설정
    - write_timeout=10: 쓰기 타임아웃 설정
    """
    _init_connection_pool()
    
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
        charset=DB_CONFIG["charset"],
        cursorclass=DictCursor,
        autocommit=False,  # 트랜잭션 제어
        connect_timeout=5,  # 연결 타임아웃
        read_timeout=10,  # 읽기 타임아웃
        write_timeout=10,  # 쓰기 타임아웃
        init_command="SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO'"
    )
