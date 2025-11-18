"""
user_Inserter.py (DB에 UserData Insert 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- Local에서 테스트 하기 위한 Data Insert화면
"""

import streamlit as st
import requests
import json

API_URL = "http://localhost:5000/api"

st.title("User Data Management")

def safe_request(url):
    """안정적으로 요청하고 JSON/텍스트를 모두 처리하는 함수"""
    try:
        res = requests.get(url)

        # JSON으로 파싱 시도
        try:
            return True, res.json()
        except json.JSONDecodeError:
            # JSON이 아니면 텍스트(HTML 오류 등)를 반환
            return False, {"raw": res.text}

    except Exception as e:
        # 요청 자체가 실패한 경우
        return False, {"error": str(e)}


# -----------------------------
# Create Table
# -----------------------------
if st.button("Create User Table"):
    ok, data = safe_request(f"{API_URL}/init_user_table")

    if ok:
        st.success(data["message"])
    else:
        st.error("요청 실패 (JSON 아님)")
        st.code(data, language="json")


# -----------------------------
# Import CSV Users
# -----------------------------
if st.button("Import CSV Users"):
    ok, data = safe_request(f"{API_URL}/import_users_from_csv")

    if ok:
        st.success(data["message"])
    else:
        st.error("요청 실패 (JSON 아님)")
        st.code(data, language="json")
