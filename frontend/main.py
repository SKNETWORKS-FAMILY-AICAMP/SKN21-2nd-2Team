"""
main.py (플랫폼 Main 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 기능 추가 예정
"""

import streamlit as st
import requests

API_URL = "http://localhost:5000/api"

# ----------------------------------------------------------
# API 호출 유틸 함수
# ----------------------------------------------------------
def call_api(endpoint: str):
    """
    Flask API(endpoint)를 GET 요청으로 호출하는 함수
    """
    try:
        res = requests.get(f"{API_URL}/{endpoint}")
        return True, res.json()
    except Exception as e:
        return False, {"error": str(e)}


# ----------------------------------------------------------
# 서브 페이지 함수들
# ----------------------------------------------------------
def show_home_page():
    st.subheader("🏠 홈 화면")
    st.write("환영합니다. 사이드바에서 기능을 선택할 수 있습니다.")


def show_profile_page():
    st.subheader("👤 내 정보")
    user = st.session_state.user_info

    st.markdown(f"""
    ### 사용자 정보
    - **ID:** {user['user_id']}
    - **이름:** {user['name']}
    - **등급:** {user['grade']}
    """)


def show_feature_a():
    st.subheader("기능 A")
    st.write("기능 A의 내용을 여기에 작성하세요.")


def show_feature_b():
    st.subheader("기능 B")
    st.write("기능 B의 내용을 여기에 작성하세요.")


# ----------------------------------------------------------
# 사용자 데이터 관리 도구 (API 호출 기반)
# ----------------------------------------------------------
def show_user_admin_tools():
    st.header("🛠 사용자 데이터 관리 도구")
    st.write("Flask API(app.py)에서 제공하는 기능을 실행합니다.")
    st.markdown("---")

    # 1. User 테이블 생성
    if st.button("📘 User Table 생성"):
        ok, res = call_api("init_user_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    # 2. CSV → DB Insert 실행
    if st.button("📥 CSV → DB Insert 실행"):
        ok, res = call_api("import_users_from_csv")
        if ok:
            st.success(res.get("message", "CSV Import 완료"))
        else:
            st.error(res)


# ----------------------------------------------------------
# 메인 화면 (로그인 후 진입)
# ----------------------------------------------------------
def show_main_page():
    """
    로그인 성공 후 보여지는 메인 화면
    """
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("로그인 후 이용 가능한 메뉴입니다.")
        st.stop()

    user = st.session_state.user_info
    grade = user.get("grade")
    
    st.title("📘 메인 화면")
    st.markdown(f"""
    ### 👤 사용자 정보
    - **ID:** {user['user_id']}
    - **이름:** {user['name']}
    - **등급:** {user['grade']}
    """)

    # -------------------------
    # 사이드바 메뉴
    # -------------------------
    menu_items = ["홈", "내 정보", "기능 A", "기능 B"]
    
    # grade = 99 → 관리자
    if grade == "99":
        menu_items.append("사용자 데이터 관리")

    menu = st.sidebar.radio("메뉴 선택", menu_items)

    if menu == "홈":
        show_home_page()
    elif menu == "내 정보":
        show_profile_page()
    elif menu == "기능 A":
        show_feature_a()
    elif menu == "기능 B":
        show_feature_b()
    elif menu == "사용자 데이터 관리":
        if grade == "99":
            show_user_admin_tools()
        else:
            st.error("권한이 없습니다.")

    # -------------------------
    # 로그아웃
    # -------------------------
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
