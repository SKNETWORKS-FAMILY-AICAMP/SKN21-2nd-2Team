"""
constants.py (공용 상수)
Auth: 박수빈
Date: 2025-11-18
Description
- 공용 상수 선언 파일
- 공용 상수는 대문자로 작성
"""

import pymysql

# DB SET VALUE
# Local에서 사용 시, 개인적으로 CONFIG 수정 필요.
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "test1234",
    "db": "skn21_2nd_team",
    "charset": "utf8mb4"
}

def get_connection():
    ''' DB Connect function'''
    return pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor
    )