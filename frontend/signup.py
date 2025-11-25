"""
signup.py (플랫폼 회원가입 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 신규 사용자 회원가입
- 사용자 정보 입력 및 검증
- 회원가입 후 로그인 페이지 이동
"""

import streamlit as st
import requests

API_URL = "http://localhost:5000/api"

# 좋아하는 음악 목록
MUSIC_OPTIONS = [
    "Ballad", "Hip-Hop", "K-Pop", "Pop", "R&B", "Rock", "Jazz", "EDM"
]


def show_signup_page():
    st.title("📝 회원가입")

    # -----------------------------
    # ID 입력 + 중복확인
    # -----------------------------
    st.subheader("사용자 ID 입력 (숫자만 가능)")
    col1, col2 = st.columns([2, 1])

    with col1:
        user_id = st.text_input("ID 입력", key="signup_user_id")

    with col2:
        if st.button("중복확인"):
            if not user_id.isdigit():
                st.error("ID는 숫자만 입력 가능합니다.")
                st.session_state["id_valid"] = False
            else:
                try:
                    res = requests.get(f"{API_URL}/check_user_id", params={"user_id": user_id})
                    data = res.json()

                    if data.get("exists"):
                        st.error("이미 존재하는 ID입니다.")
                        st.session_state["id_valid"] = False
                    else:
                        st.success("사용 가능한 ID입니다.")
                        st.session_state["id_valid"] = True

                except Exception as e:
                    st.error(f"서버 오류: {e}")

    # ID 중복확인 상태 초기값 설정
    if "id_valid" not in st.session_state:
        st.session_state["id_valid"] = False

    st.markdown("---")

    # -----------------------------
    # 이름 (텍스트 입력)
    # -----------------------------
    st.subheader("이름 입력")
    name = st.text_input("이름을 입력하세요")

    # -----------------------------
    # 좋아하는 음악 (셀렉트박스)
    # -----------------------------
    st.subheader("좋아하는 음악 선택")
    favorite_music = st.selectbox("좋아하는 음악", MUSIC_OPTIONS)

    # -----------------------------
    # 비밀번호 입력
    # -----------------------------
    st.subheader("비밀번호 설정")
    password = st.text_input("비밀번호", type="password")

    st.markdown("---")

    # -----------------------------
    # 회원가입 실행 버튼
    # -----------------------------
    if st.button("회원가입 완료"):
        # 필수 검증
        if not st.session_state["id_valid"]:
            st.error("ID 중복확인을 먼저 진행해 주세요.")
            return

        if not name:
            st.error("이름을 입력해 주세요.")
            return

        if not password:
            st.error("비밀번호를 입력해 주세요.")
            return

        payload = {
            "user_id": user_id,
            "name": name,
            "favorite_music": favorite_music,
            "password": password
        }

        try:
            res = requests.post(f"{API_URL}/signup", json=payload)
            data = res.json()

            if data.get("success"):
                st.success("회원가입이 완료되었습니다!")
                st.info("로그인 페이지로 이동합니다.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(f"회원가입 실패: {data.get('message')}")

        except Exception as e:
            st.error(f"서버 연결 오류: {e}")
