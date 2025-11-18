"""
main.py (플랫폼 Main 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 기능 추가 예정
"""

import streamlit as st
import requests
import pandas as pd

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

def call_api_post(endpoint: str, payload: dict):
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=payload)
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
    """
    개인 정보 확인 및 수정 페이지
    """

    st.subheader("👤 개인 정보 수정")

    user = st.session_state.user_info
    grade = user.get("grade")
    
    # 현재 값 가지기
    current_name = user["name"]
    current_fav_music = user.get("favorite_music", "")
    current_grade = user["grade"]

    # ------------------------------
    # 입력 폼
    # ------------------------------
    new_name = st.text_input("이름", value=current_name)
    new_music = st.text_input("좋아하는 음악", value=current_fav_music)

    # grade 수정은 관리자만 가능
    if grade == "99":
        new_grade = st.text_input("등급", value=current_grade)
    else:
        new_grade = current_grade
        st.info("등급은 관리자만 수정할 수 있습니다.")

    # ------------------------------
    # 저장 버튼
    # ------------------------------
    if st.button("💾 수정 내용 저장"):

        payload = {
            "user_id": user["user_id"],
            "name": new_name,
            "favorite_music": new_music,
            "grade": new_grade,
        }

        ok, res = call_api_post("update_user_data", payload)

        if ok and res.get("success"):
            st.success("정보가 성공적으로 수정되었습니다.")

            # 세션 정보도 업데이트 필요!
            st.session_state.user_info["name"] = new_name
            st.session_state.user_info["favorite_music"] = new_music
            st.session_state.user_info["grade"] = new_grade

            st.rerun()
        else:
            st.error(f"수정 실패: {res}")

# ----------------------------------------------------------
# 사용자 검색 함수
# ----------------------------------------------------------
def search_user():
    st.subheader("🔍 사용자 검색")

    # 검색 필드 UI
    st.markdown("### 검색 조건")
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        search_name = st.text_input("이름 검색")
    with col2:
        search_user_id = st.text_input("User ID")
    with col3:
        search_music = st.text_input("좋아하는 음악 검색")
    with col4:
        search_grade = st.text_input("등급 (예: 01, 99)")

    # 페이지 크기
    page_size = st.selectbox("페이지 크기", [10, 20, 30, 50], index=1)

    # 페이지 상태
    if "user_page" not in st.session_state:
        st.session_state.user_page = 1

    page = st.session_state.user_page

    # 검색 버튼
    if st.button("🔍 검색 실행"):
        st.session_state.user_page = 1  # 첫 페이지로 리셋
        st.rerun()

    # API 요청 URL 구성
    api_url = (
        f"users_search?page={page}&page_size={page_size}"
        f"&name={search_name}"
        f"&user_id={search_user_id}"
        f"&favorite_music={search_music}"
        f"&grade={search_grade}"
    )

    ok, res = call_api(api_url)

    if not ok or not res.get("success"):
        st.error("검색 중 오류가 발생하였습니다.")
        st.write(res)
        return

    rows = res["rows"]
    total_rows = res["total_rows"]
    total_pages = res["total_pages"]

    st.write(f"총 {total_rows}명, 페이지 {page}/{total_pages}")

    # 테이블 표시
    if rows:
        df = pd.DataFrame(rows)
        desired_order = ["user_id", "name", "favorite_music", "join_date", "grade"]
        df = df[desired_order]
        st.table(df)
    else:
        st.info("검색 결과가 없습니다.")
        return

    # 페이징 버튼 UI
    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("⬅ 이전 페이지"):
            if page > 1:
                st.session_state.user_page -= 1
                st.rerun()

    with colB:
        st.write(f"현재 페이지: {page}")

    with colC:
        if st.button("다음 페이지 ➡"):
            if page < total_pages:
                st.session_state.user_page += 1
                st.rerun()

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

    # User 테이블 생성
    if st.button("📘 User Table 생성"):
        ok, res = call_api("init_user_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    # CSV → DB Insert 실행
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
    
    # ---------------------------
    # 🔵 사용자 정보를 사이드바로 이동
    # ---------------------------
    with st.sidebar:
        st.markdown("### 👤 로그인 정보")
        st.write(f"**ID:** {user['user_id']}")
        st.write(f"**이름:** {user['name']}")
        st.write(f"**등급:** {user['grade']}")
        st.markdown("---")
        
    # ---------------------------
    # 메인 화면 제목
    # ---------------------------
    st.title("📘 메인 화면")

    # -------------------------
    # 사이드바 메뉴
    # -------------------------
    menu_items = ["홈", "내 정보", "기능 B"]
    
    # grade = 99 → 관리자
    if grade == "99":
        menu_items.extend(["사용자 데이터 관리", "유저 조회"])

    menu = st.sidebar.radio("메뉴 선택", menu_items)

    if menu == "홈":
        show_home_page()
    elif menu == "내 정보":
        show_profile_page()
    elif menu == "유저 조회":
        if grade == "99":
            search_user()
        else:
            st.error("권한이 없습니다.")
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
