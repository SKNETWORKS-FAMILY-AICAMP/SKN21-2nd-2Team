"""
login.py (플랫폼 Login 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 현재는 Login Test
"""

import streamlit as st
import requests

API_URL = "http://localhost:5000/api"

st.title("🎧 로그인")

# 세션 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

# ----------------------------------------------------------
# 로그인 화면
# ----------------------------------------------------------
if not st.session_state.logged_in:

    st.subheader("로그인")

    user_id_input = st.text_input("아이디 (user_id)", placeholder="예: 1 또는 1001")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):

        # 입력 검증
        if not user_id_input.strip().isdigit():
            st.error("아이디는 숫자만 입력 가능합니다.")
        else:
            user_id = int(user_id_input.strip())

            res = requests.post(f"{API_URL}/login", json={
                "user_id": user_id,
                "password": password
            })

            if res.status_code == 200 and res.json().get("success"):
                st.success("로그인 성공!")

                st.session_state.logged_in = True
                st.session_state.user_info = res.json()
                st.rerun()

            else:
                st.error("로그인 실패: 아이디 또는 비밀번호를 확인하세요.")


# ----------------------------------------------------------
# 로그인 성공 후 화면
# ----------------------------------------------------------
else:
    user = st.session_state.user_info

    st.success(f"반갑습니다, {user['name']}님!")
    st.write(f"회원등급: {user['grade']}")

    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
