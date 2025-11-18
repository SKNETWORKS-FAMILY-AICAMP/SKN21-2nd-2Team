"""
login.py (플랫폼 Login 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- users 테이블에서 Login Data 조회 후 로그인
- test 로그인 Data 로직
"""

import streamlit as st
import requests

API_URL = "http://localhost:5000/api"

def show_login_page():
    """
    로그인 화면 페이지
    """

    st.set_page_config(page_title="로그인", page_icon="🔐", layout="centered")

    st.title("🔐 로그인 페이지")

    # 세션 초기화 (최초 1회만)
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.logged_in = False
        st.session_state.user_info = None

    st.subheader("로그인 정보를 입력해 주세요.")

    # 입력
    user_id_input = st.text_input("아이디 (user_id)", placeholder="예: 1 또는 test")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        # st.write("➡ 버튼 클릭 감지됨")

        # ------------------------------
        # 관리자 임시 로그인 로직 (ID: test1 / PW: 1234 / grade:99)
        # ------------------------------
        if user_id_input.strip() == "test1" and password.strip() == "1234":
            st.success("임시 계정으로 로그인되었습니다.")

            # 메인 페이지에서 기대하는 형태와 동일하게 세션 데이터 구성
            st.session_state.logged_in = True
            st.session_state.user_info = {
                "user_id": 99,
                "name": "Test Admin",
                "grade": "99",
            }

            st.rerun()
            return  # 아래 실제 로그인 로직으로 내려가지 않도록 종료
        
        # ------------------------------
        # 유저 임시 로그인 로직 (ID: test2 / PW: 1234 / grade:01)
        # ------------------------------
        if user_id_input.strip() == "test2" and password.strip() == "1234":
            st.success("임시 계정으로 로그인되었습니다.")

            # 메인 페이지에서 기대하는 형태와 동일하게 세션 데이터 구성
            st.session_state.logged_in = True
            st.session_state.user_info = {
                "user_id": 00,
                "name": "Test User",
                "grade": "01",
            }

            st.rerun()
            return  # 아래 실제 로그인 로직으로 내려가지 않도록 종료

        # ------------------------------
        # 실제 API 로그인 로직 (숫자 user_id 전용)
        # ------------------------------

        # 숫자 검증
        if not user_id_input.strip().isdigit():
            st.error("아이디는 숫자만 입력 가능합니다. (또는 임시 계정: test / 1234)")
            return

        user_id = int(user_id_input.strip())

        try:
            # API 요청
            res = requests.post(
                f"{API_URL}/login",
                json={"user_id": user_id, "password": password}
            )
            # st.write("📡 API 응답 코드:", res.status_code)

            try:
                data = res.json()
                # st.write("📡 JSON 응답:", data)
            except Exception as e:
                st.error(f"JSON 파싱 오류: {e}")
                return

            # ------------------------------
            # 로그인 성공 여부 대체 판정 방식
            # user_id, name, grade 존재 여부로 판단
            # ------------------------------
            required_fields = ["user_id", "name", "grade"]
            is_valid = all(field in data for field in required_fields)

            if res.status_code == 200 and is_valid:
                st.session_state.logged_in = True
                st.session_state.user_info = data

                st.success("로그인 성공!")
                st.rerun()

            else:
                st.error("로그인 실패: 아이디 또는 비밀번호를 확인해 주세요.")

        except Exception as e:
            st.error(f"서버 연결 실패: {e}")

    # st.write("로그인 테스트 완료 영역 (오류 확인용)")

if __name__ == "__main__":
    show_login_page()
