"""
user_insert.py (User_data.csv insert 모듈)
Auth: 박수빈
Date: 2025-11-18
Description
- User Data DB에 Insert
"""

import csv
import bcrypt
from utils.constants import get_connection

def hash_password(raw_password: str) -> str:
    """
    bcrypt 기반 비밀번호 해시 함수.
    평문을 bcrypt 60자 문자열로 변환한다.
    """
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def load_users_from_csv(csv_path: str):
    """
    CSV 파일을 읽어 users 테이블에 insert한다.
    CSV 컬럼:
    Name,Favorite_Music,Password,JoinDate,ModifyDate,Grade
    """

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO users (
        name, favorite_music, password, join_date, modify_date, grade
    ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            hashed_pw = hash_password(row["Password"])

            cursor.execute(sql, (
                row["Name"],
                row["Favorite_Music"],
                hashed_pw,
                row["JoinDate"],
                row["ModifyDate"],
                row["Grade"]
            ))

    conn.commit()
    cursor.close()
    conn.close()

    return True
