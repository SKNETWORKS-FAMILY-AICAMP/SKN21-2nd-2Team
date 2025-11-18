"""
user_insert.py (User_data.csv insert 모듈)
Auth: 박수빈
Date: 2025-11-18
Description
- User Data DB Insert (bcrypt 암호화)
"""

import csv
import bcrypt
from utils.constants import get_connection


def load_users_from_csv(csv_path):
    """
    CSV의 Password 값을 bcrypt 해시로 변환하여 DB에 Insert
    """

    print("\n-----------------------------------------")
    print("CSV → DB Insert 시작 (bcrypt 적용)")
    print(f"파일 경로: {csv_path}")
    print("-----------------------------------------")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("DB Connection 성공")
    except Exception as e:
        print("DB Connection 실패:", e)
        return

    # CSV 읽기
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"CSV 로드 완료: 총 {len(rows)}행")
        print("CSV Columns:", list(rows[0].keys()))
    except Exception as e:
        print("CSV 읽기 실패:", e)
        return

    inserted = 0
    failed = 0

    for i, row in enumerate(rows, start=1):
        try:
            print(f"[{i}/{len(rows)}] ➜ 삽입 중... id={row.get('user_id')}")

            # ----------------------------
            # ① Password bcrypt 해싱
            # ----------------------------
            raw_pw = row.get("Password")
            hashed_pw = bcrypt.hashpw(raw_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            sql = """
                INSERT INTO users 
                (user_id, name, favorite_music, password, join_date, modify_date, grade)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (
                row.get("user_id"),
                row.get("Name"),
                row.get("Favorite_Music"),
                hashed_pw,                       # ← bcrypt 해시 저장
                row.get("JoinDate") or None,
                row.get("ModifyDate") or None,
                row.get("Grade"),
            ))

            conn.commit()
            inserted += 1
            print(f"성공 (누적: {inserted})")

        except Exception as e:
            failed += 1
            print(f"실패 (누적: {failed}) → 이유: {e}")

    cursor.close()
    conn.close()

    print("\n-----------------------------------------")
    print("Insert 완료")
    print(f"성공: {inserted}")
    print(f"실패: {failed}")
    print("-----------------------------------------\n")
