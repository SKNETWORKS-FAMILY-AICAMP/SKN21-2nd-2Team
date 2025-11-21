"""
main.py (플랫폼 Main 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 홈 화면
- 내 정보 수정
- Admin 사용자 데이터 관리
- Admin 사용자 조회
"""

import streamlit as st
import requests
import pandas as pd
import os

API_URL = "http://localhost:5000/api"

# ----------------------------------------------------------
# 음악 카테고리 목록 로드 함수
# ----------------------------------------------------------
def get_music_categories():
    """
    user_data.csv에서 음악 카테고리 목록을 읽어옴
    """
    try:
        csv_path = os.path.join("data", "user_data.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if "Favorite_Music" in df.columns:
                categories = sorted(df["Favorite_Music"].dropna().unique().tolist())
                return categories
    except Exception as e:
        st.write(f"🔍 [LOG] 음악 카테고리 로드 오류: {e}")
    
    # 기본값 (CSV 로드 실패 시)
    return [
        "Alternative", "Blues", "Classical", "Country", "EDM",
        "Folk", "Hip Hop", "House", "Indie", "Jazz",
        "K-Pop", "Latin", "Metal", "Pop", "R&B",
        "Reggae", "Rock", "Soul", "Techno", "Trap"
    ]

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
    render_top_guide_banner()


# ----------------------------------------------------------
# 상단 배너
# ----------------------------------------------------------
def render_top_guide_banner():
    st.markdown(
        """
        <div style="
            background-color: #1f2937;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            color: white;
            font-size: 16px;
            border-left: 5px solid #3b82f6;
        ">
            <b style="font-size:17px;">📘 이용 가이드</b><br>
            • 왼쪽 사이드바에서 원하는 기능을 선택하세요.<br>
            • 권한(grade)에 따라 접근 가능한 메뉴가 달라질 수 있습니다.<br>
            • 관리자(99)는 추가 관리 기능을 사용할 수 있습니다.<br>
            • 모든 페이지 상단에 이 안내가 항상 표시됩니다.
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------------------------------------------
# 개인정보 수정 함수
# ----------------------------------------------------------
def show_profile_page():
    """
    개인 정보 확인 및 수정 페이지
    """

    # stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬을 위한 CSS
    st.markdown("""
    <style>
    /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
        padding-right: 0 !important;
        margin-right: 0 !important;
        justify-content: flex-end !important;
        display: flex !important;
        gap: 0.5rem !important;
    }
    
    /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
        padding-right: 0.25rem !important;
        padding-left: 0.25rem !important;
    }
    
    /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
        flex-grow: 1;
        min-width: 0;
    }
    
    /* 버튼이 있는 컬럼은 자동 크기 조정 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
        flex-shrink: 0;
    }
    
    /* 버튼 스타일 - 적절한 크기 */
    button[kind="primary"] {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    
    button:not([kind="primary"]) {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("👤 개인 정보 수정")

    user = st.session_state.user_info
    user_id = user.get("user_id")
    grade = user.get("grade")
    
    # ------------------------------
    # API에서 최신 사용자 정보 조회
    # test 계정(user_id 99, 1)인 경우 API 호출 건너뛰기
    # ------------------------------
    is_test_account = (user_id == 99 or user_id == 1)
    
    if is_test_account:
        # test 계정은 세션 정보만 사용
        current_name = user.get("name", "")
        current_fav_music = user.get("favorite_music", "")
        current_grade = user.get("grade", "")
        st.info("ℹ️ 테스트 계정입니다. 세션 정보를 사용합니다.")
    else:
        try:
            res = requests.get(f"{API_URL}/users/{user_id}")
            if res.status_code == 200:
                user_data = res.json()
                
                # 딕셔너리 형태로 반환되므로 직접 접근
                current_name = user_data.get("name", user.get("name", ""))
                current_fav_music = user_data.get("favorite_music", user.get("favorite_music", ""))
                current_grade = user_data.get("grade", user.get("grade", ""))
                
                # 세션 정보도 업데이트
                st.session_state.user_info["name"] = current_name
                st.session_state.user_info["favorite_music"] = current_fav_music
                st.session_state.user_info["grade"] = current_grade
                
                st.write("🔍 [LOG] API에서 최신 사용자 정보 조회 완료")
            else:
                # API 조회 실패 시 세션 정보 사용
                st.warning("⚠️ 최신 정보를 불러오지 못했습니다. 세션 정보를 사용합니다.")
                current_name = user.get("name", "")
                current_fav_music = user.get("favorite_music", "")
                current_grade = user.get("grade", "")
        except Exception as e:
            st.warning(f"⚠️ 사용자 정보 조회 중 오류 발생: {e}. 세션 정보를 사용합니다.")
            current_name = user.get("name", "")
            current_fav_music = user.get("favorite_music", "")
            current_grade = user.get("grade", "")

    # ------------------------------
    # 임시 입력값 저장용 세션 상태 초기화
    # ------------------------------
    if f"temp_profile_{user_id}_name" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_name"] = current_name
    if f"temp_profile_{user_id}_music" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_music"] = current_fav_music
    if f"temp_profile_{user_id}_grade" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_grade"] = current_grade

    # ------------------------------
    # 입력 폼
    # ------------------------------
    st.markdown("### 📝 정보 수정")
    st.info("💡 정보를 수정한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다.")
    
    # 이름 입력 (임시 세션 상태 사용)
    temp_name = st.text_input(
        "이름", 
        value=st.session_state[f"temp_profile_{user_id}_name"], 
        key=f"profile_name_{user_id}"
    )
    st.session_state[f"temp_profile_{user_id}_name"] = temp_name
    
    # 좋아하는 음악 selectbox (임시 세션 상태 사용)
    music_categories = get_music_categories()
    temp_music_value = st.session_state[f"temp_profile_{user_id}_music"]
    
    # 현재 값이 목록에 없으면 빈 문자열로 처리
    if temp_music_value and temp_music_value not in music_categories:
        # 현재 값이 목록에 없으면 첫 번째 옵션으로 설정하거나 빈 값 추가
        music_categories_with_empty = [""] + music_categories
        current_music_index = 0
    else:
        music_categories_with_empty = [""] + music_categories
        if temp_music_value:
            try:
                current_music_index = music_categories_with_empty.index(temp_music_value)
            except ValueError:
                current_music_index = 0
        else:
            current_music_index = 0
    
    selected_music = st.selectbox(
        "좋아하는 음악",
        options=music_categories_with_empty,
        index=current_music_index,
        key=f"profile_music_select_{user_id}",
        help="음악 장르를 선택한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다."
    )
    # 버튼 클릭 시에만 세션 상태 업데이트하도록 주석 처리
    # st.session_state[f"temp_profile_{user_id}_music"] = selected_music

    # grade 옵션 정의 (key: value 형태)
    grade_options = {
        "01": "일반회원",
        "99": "관리자"
    }
    
    # grade 수정은 관리자만 가능 (99가 아니면 disabled)
    if grade == "99":
        # 관리자는 select box로 선택 가능
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        # 임시 세션 상태의 grade에 맞는 인덱스 찾기
        temp_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        current_grade_index = 0
        for idx, (k, v) in enumerate(grade_options.items()):
            if k == temp_grade:
                current_grade_index = idx
                break
        
        # selectbox의 key를 고정하여 값 변경 시 자동 업데이트 방지
        # 버튼 클릭 시에만 값을 읽도록 처리
        selected_grade_display = st.selectbox(
            "등급",
            options=grade_display_options,
            index=current_grade_index,
            key=f"profile_grade_select_{user_id}",
            help="등급을 선택한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다."
        )
        # 선택된 값에서 key 추출 (예: "01: 일반회원" -> "01")
        # 버튼 클릭 시에만 세션 상태 업데이트하도록 주석 처리
        # temp_grade_value = selected_grade_display.split(":")[0].strip()
        # st.session_state[f"temp_profile_{user_id}_grade"] = temp_grade_value
    else:
        # 일반 사용자는 disabled select box
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        temp_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        current_grade_index = 0
        for idx, (k, v) in enumerate(grade_options.items()):
            if k == temp_grade:
                current_grade_index = idx
                break
        
        selected_grade_display = st.selectbox(
            "등급",
            options=grade_display_options,
            index=current_grade_index,
            disabled=True,
            help="등급은 관리자(99)만 수정할 수 있습니다.",
            key=f"profile_grade_disabled_{user_id}"
        )
        st.info("ℹ️ 등급은 관리자만 수정할 수 있습니다.")

    # 현재 정보 표시
    with st.expander("📋 현재 정보 확인", expanded=False):
        grade_display_name = grade_options.get(current_grade, current_grade)
        st.write(f"**사용자 ID:** {user_id}")
        st.write(f"**이름:** {current_name}")
        st.write(f"**좋아하는 음악:** {current_fav_music if current_fav_music else '(없음)'}")
        st.write(f"**등급:** {current_grade} ({grade_display_name})")

    # ------------------------------
    # 저장 버튼 (버튼 클릭 시에만 실제 저장, 우측 정렬, 동일선상에 가로 배치, 적당한 간격)
    # ------------------------------
    btn_col1, btn_col2, btn_col3 = st.columns([4, 1.1, 1.1])
    with btn_col1:
        pass  # 빈 공간
    with btn_col2:
        save_button = st.button("💾 저장", type="primary", key=f"save_button_{user_id}")
    with btn_col3:
        reset_button = st.button("🔄 초기화", key=f"reset_button_{user_id}")
    
    if reset_button:
            # 임시 세션 상태를 현재 DB 값으로 초기화
            st.session_state[f"temp_profile_{user_id}_name"] = current_name
            st.session_state[f"temp_profile_{user_id}_music"] = current_fav_music
            st.session_state[f"temp_profile_{user_id}_grade"] = current_grade
            
            # selectbox 값도 초기화 (rerun 후 자동으로 반영됨)
            # 하지만 명시적으로 초기화하려면 key를 삭제하거나 재설정
            if f"profile_music_select_{user_id}" in st.session_state:
                del st.session_state[f"profile_music_select_{user_id}"]
            if f"profile_grade_select_{user_id}" in st.session_state:
                del st.session_state[f"profile_grade_select_{user_id}"]
            
            st.success("입력값이 초기화되었습니다.")
            st.rerun()
    
    if save_button:
        # 임시 세션 상태에서 값 가져오기
        new_name = st.session_state[f"temp_profile_{user_id}_name"]
        
        # selectbox에서 현재 선택된 값을 읽어서 세션 상태에 저장
        # 좋아하는 음악 selectbox 값 읽기
        selected_music = st.session_state.get(f"profile_music_select_{user_id}", "")
        new_music = selected_music if selected_music else ""
        
        # grade selectbox 값 읽기
        if grade == "99":
            # selectbox의 key로 저장된 현재 값을 읽어옴
            # Streamlit은 selectbox의 값을 자동으로 session_state에 저장함
            selected_grade_display = st.session_state.get(f"profile_grade_select_{user_id}", f"{current_grade}: {grade_options.get(current_grade, '')}")
            new_grade = selected_grade_display.split(":")[0].strip()
        else:
            new_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        
        # 세션 상태 업데이트 (버튼 클릭 시에만)
        st.session_state[f"temp_profile_{user_id}_music"] = new_music
        st.session_state[f"temp_profile_{user_id}_grade"] = new_grade
        
        # 입력값 검증
        if not new_name.strip():
            st.error("이름은 필수 입력 항목입니다.")
            return

        # grade 값 검증 (01 또는 99만 허용)
        if new_grade not in grade_options:
            st.error(f"등급은 {', '.join(grade_options.keys())} 중 하나만 선택 가능합니다.")
            return

        # 변경사항 확인
        has_changes = (
            new_name.strip() != current_name or
            new_music.strip() != (current_fav_music or "") or
            new_grade != current_grade
        )
        
        if not has_changes:
            st.info("변경된 내용이 없습니다.")
            return

        # test 계정인 경우 API 호출 없이 세션 정보만 업데이트
        if is_test_account:
            st.info("ℹ️ 테스트 계정입니다. 세션 정보만 업데이트됩니다. (DB에는 저장되지 않습니다.)")
            
            # 세션 정보 업데이트
            st.session_state.user_info["name"] = new_name.strip()
            st.session_state.user_info["favorite_music"] = new_music.strip() if new_music else ""
            st.session_state.user_info["grade"] = new_grade
            
            # 임시 세션 상태도 업데이트 (최신 값으로 동기화)
            st.session_state[f"temp_profile_{user_id}_name"] = new_name.strip()
            st.session_state[f"temp_profile_{user_id}_music"] = new_music.strip() if new_music else ""
            st.session_state[f"temp_profile_{user_id}_grade"] = new_grade
            
            st.success("✅ 테스트 계정 정보가 업데이트되었습니다.")
            st.rerun()
        else:
            payload = {
                "user_id": user_id,
                "name": new_name.strip(),
                "favorite_music": new_music.strip() if new_music else "",
                "grade": new_grade,
            }

            st.write("🔍 [LOG] 수정 요청 데이터:", payload)
            
            with st.spinner("정보를 저장하는 중..."):
                ok, res = call_api_post("update_user_data", payload)

            if ok and res.get("success"):
                st.success("✅ 정보가 성공적으로 수정되었습니다.")

                # 세션 정보 업데이트
                st.session_state.user_info["name"] = payload["name"]
                st.session_state.user_info["favorite_music"] = payload["favorite_music"]
                st.session_state.user_info["grade"] = payload["grade"]
                
                # 임시 세션 상태도 업데이트 (최신 값으로 동기화)
                st.session_state[f"temp_profile_{user_id}_name"] = payload["name"]
                st.session_state[f"temp_profile_{user_id}_music"] = payload["favorite_music"]
                st.session_state[f"temp_profile_{user_id}_grade"] = payload["grade"]

                st.rerun()
            else:
                error_msg = res.get("error", "알 수 없는 오류가 발생했습니다.")
                st.error(f"❌ 수정 실패: {error_msg}")
                st.write("🔍 [LOG] API 응답:", res)

# ----------------------------------------------------------
# 사용자 조회 함수
# ----------------------------------------------------------
def search_user():
    st.subheader("🔍 사용자 조회")
    
    # FHD 화면에 맞는 CSS 스타일 추가
    st.markdown("""
    <style>
    /* 사용자 조회 페이지 최대 너비 확장 */
    div[data-testid="stVerticalBlock"] {
        max-width: 100%;
    }
    
    /* 필터 컬럼 간격 조정 */
    div[data-testid="column"] {
        padding: 0.25rem;
    }
    
    /* 입력 필드 너비 최적화 */
    div[data-testid="stTextInput"] {
        width: 100%;
    }
    
    div[data-testid="stSelectbox"] {
        width: 100%;
    }
    
    /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
        padding-right: 0 !important;
        margin-right: 0 !important;
        justify-content: flex-end !important;
        display: flex !important;
        gap: 0.5rem !important;
    }
    
    /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
        padding-right: 0.25rem !important;
        padding-left: 0.25rem !important;
    }
    
    /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
        flex-grow: 1;
        min-width: 0;
    }
    
    /* 버튼이 있는 컬럼은 자동 크기 조정 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
        flex-shrink: 0;
    }
    
    /* 버튼 스타일 - 적절한 크기 */
    button[kind="primary"] {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    
    button:not([kind="primary"]) {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 조회 필드 UI - 한 줄에 나열하여 보기 좋게 정리 (FHD 기준으로 더 넓게)
    st.markdown("### 조회 조건")
    
    # 필터 필드들을 한 줄에 나열 (FHD 화면에 맞게 비율 조정)
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2.5, 2.5, 2.5, 2.5, 1.5])
    
    with filter_col1:
        search_name = st.text_input("이름 조회", placeholder="이름을 입력하세요")
    with filter_col2:
        search_user_id = st.text_input("User ID", placeholder="사용자 ID를 입력하세요")
    with filter_col3:
        search_music = st.text_input("좋아하는 음악 조회", placeholder="음악 장르를 입력하세요")
    with filter_col4:
        # 등급을 selectbox로 변경
        grade_filter_options = ["전체", "01: 일반회원", "99: 관리자"]
        selected_grade_filter = st.selectbox("등급", options=grade_filter_options, key="search_grade_filter")
        if selected_grade_filter == "전체":
            search_grade = ""
        else:
            search_grade = selected_grade_filter.split(":")[0].strip()
    with filter_col5:
        page_size = st.selectbox("페이지 크기", [10, 20, 30, 50], index=1)

    # 페이지 상태 및 조회 실행 여부 관리
    if "user_page" not in st.session_state:
        st.session_state.user_page = 1
    if "search_executed" not in st.session_state:
        st.session_state.search_executed = False
    if "search_params" not in st.session_state:
        st.session_state.search_params = {}

    page = st.session_state.user_page

    # 조회 버튼 (우측 정렬)
    st.markdown("---")
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        pass  # 빈 공간
    with col_btn2:
        search_button = st.button("🔍 조회 실행", type="primary")
    
    if search_button:
        # 조회 실행 시 세션 상태 업데이트
        st.session_state.user_page = 1  # 첫 페이지로 리셋
        st.session_state.search_executed = True
        st.session_state.search_params = {
            "name": search_name,
            "user_id": search_user_id,
            "favorite_music": search_music,
            "grade": search_grade,
            "page_size": page_size
        }
        st.rerun()

    # 조회가 실행되지 않았으면 조회 결과를 표시하지 않음
    if not st.session_state.search_executed:
        st.info("💡 조회 조건을 입력한 후 '조회 실행' 버튼을 클릭하세요.")
        return

    # 저장된 조회 파라미터 사용 (버튼 클릭 시에만 업데이트)
    saved_params = st.session_state.search_params
    current_search_name = saved_params.get("name", "")
    current_search_user_id = saved_params.get("user_id", "")
    current_search_music = saved_params.get("favorite_music", "")
    current_search_grade = saved_params.get("grade", "")
    current_page_size = saved_params.get("page_size", page_size)

    # API 요청 URL 구성
    api_url = (
        f"users_search?page={page}&page_size={current_page_size}"
        f"&name={current_search_name}"
        f"&user_id={current_search_user_id}"
        f"&favorite_music={current_search_music}"
        f"&grade={current_search_grade}"
    )

    ok, res = call_api(api_url)

    if not ok or not res.get("success"):
        st.error("조회 중 오류가 발생하였습니다.")
        st.write(res)
        return

    rows = res["rows"]
    total_rows = res["total_rows"]
    total_pages = res["total_pages"]

    st.write(f"총 {total_rows}명, 페이지 {page}/{total_pages}")

    # 테이블 표시 및 grade 수정 기능
    if rows:
        st.markdown("### 사용자 목록 및 등급 수정")
        st.info("💡 각 사용자의 등급을 선택한 후 '저장' 버튼을 클릭하여 수정할 수 있습니다.")
        
        # grade 옵션 정의
        grade_options = {
            "01": "일반회원",
            "99": "관리자"
        }
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        
        # 각 row의 실제 값 길이를 모두 고려하여 컬럼 비율 동적 계산
        # 모든 row의 각 컬럼 값 길이를 수집
        user_id_lengths = [len(str(row.get('user_id', ''))) for row in rows]
        name_lengths = [len(str(row.get('name', ''))) for row in rows]
        music_lengths = [len(str(row.get('favorite_music', '') or '(없음)')) for row in rows]
        date_lengths = [len(str(row.get('join_date', ''))) for row in rows]
        
        # 최대값과 평균값을 모두 고려 (최대값이 너무 크면 평균값도 고려)
        max_user_id_len = max(user_id_lengths, default=5)
        avg_user_id_len = sum(user_id_lengths) / len(user_id_lengths) if user_id_lengths else 5
        
        max_name_len = max(name_lengths, default=10)
        avg_name_len = sum(name_lengths) / len(name_lengths) if name_lengths else 10
        
        max_music_len = max(music_lengths, default=15)
        avg_music_len = sum(music_lengths) / len(music_lengths) if music_lengths else 15
        
        max_date_len = max(date_lengths, default=10)
        avg_date_len = sum(date_lengths) / len(date_lengths) if date_lengths else 10
        
        # 헤더 텍스트 길이도 고려
        header_id_len = len("ID")
        header_name_len = len("이름")
        header_music_len = len("좋아하는 음악")
        header_date_len = len("가입일")
        header_grade_len = len("등급")
        header_action_len = len("작업")
        
        # 각 컬럼의 최대 길이 계산 (헤더, 최대값, 평균값의 가중 평균)
        # 최대값에 70%, 평균값에 20%, 헤더에 10% 가중치 부여
        col_id_max = max(max_user_id_len, header_id_len) * 0.7 + avg_user_id_len * 0.2 + header_id_len * 0.1
        col_name_max = max(max_name_len, header_name_len) * 0.7 + avg_name_len * 0.2 + header_name_len * 0.1
        col_music_max = max(max_music_len, header_music_len) * 0.7 + avg_music_len * 0.2 + header_music_len * 0.1
        col_date_max = max(max_date_len, header_date_len) * 0.7 + avg_date_len * 0.2 + header_date_len * 0.1
        col_grade_max = max(len("99: 관리자"), header_grade_len)  # grade dropdown 최대 길이
        col_action_max = max(len("💾 저장"), header_action_len)  # 버튼 텍스트 길이
        
        # 컬럼 비율 조정 (길이에 비례하되 최소/최대값 제한)
        # FHD 화면 기준으로 더 넓은 비율 사용
        base_ratio = 1.5  # 기본 비율 증가
        id_ratio = max(1.5, min(3.5, col_id_max / 3 + base_ratio))
        name_ratio = max(3.0, min(8.0, col_name_max / 4 + base_ratio * 2))
        music_ratio = max(3.0, min(8.0, col_music_max / 4 + base_ratio * 2))
        date_ratio = max(2.5, min(5.0, col_date_max / 6 + base_ratio * 1.5))
        grade_ratio = max(3.0, min(5.0, col_grade_max / 5 + base_ratio * 1.8))
        action_ratio = max(2.5, min(4.5, col_action_max / 4 + base_ratio * 1.5))
        
        col_ratios = [id_ratio, name_ratio, music_ratio, date_ratio, grade_ratio, action_ratio]
        
        # CSS 스타일 추가로 텍스트 줄바꿈 및 컬럼 너비 최적화 (FHD 기준)
        st.markdown("""
        <style>
        /* 메인 컨테이너 최대 너비 확장 */
        .main .block-container {
            max-width: 95%;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        
        /* 컬럼 너비 최적화 */
        .user-table-container {
            overflow-x: auto;
            width: 100%;
        }
        
        .user-table-container div[data-testid="column"] {
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
            min-width: fit-content;
        }
        
        /* 테이블 행 스타일 개선 */
        div[data-testid="column"] {
            padding: 0.5rem;
        }
        
        /* selectbox 너비 최적화 */
        div[data-testid="stSelectbox"] {
            width: 100%;
        }
        
        /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
            padding-right: 0 !important;
            margin-right: 0 !important;
            justify-content: flex-end !important;
            display: flex !important;
            gap: 0.5rem !important;
        }
        
        /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
            padding-right: 0.25rem !important;
            padding-left: 0.25rem !important;
        }
        
        /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
            flex-grow: 1;
            min-width: 0;
        }
        
        /* 버튼이 있는 컬럼은 자동 크기 조정 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
            flex-shrink: 0;
        }
        
        /* 버튼 스타일 - 적절한 크기로 조정 및 우측 정렬 */
        .button-container {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
            align-items: center;
        }
        
        button[kind="primary"] {
            min-height: 2.5rem;
            font-size: 1rem;
            padding: 0.5rem 1.5rem;
        }
        
        button:not([kind="primary"]) {
            min-height: 2.5rem;
            font-size: 1rem;
            padding: 0.5rem 1.5rem;
        }
        
        /* 버튼 호버 효과 */
        button:hover {
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 헤더 행
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns(col_ratios)
        with header_col1:
            st.markdown("**ID**")
        with header_col2:
            st.markdown("**이름**")
        with header_col3:
            st.markdown("**좋아하는 음악**")
        with header_col4:
            st.markdown("**가입일**")
        with header_col5:
            st.markdown("**등급**")
        with header_col6:
            st.markdown("**작업**")
        
        st.markdown("---")
        
        # 각 row에 대해 수정 가능한 UI 생성
        for idx, row in enumerate(rows):
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns(col_ratios)
                
                with col1:
                    st.write(f"**{row['user_id']}**")
                
                with col2:
                    # 텍스트가 잘리지 않도록 처리 (줄바꿈 허용)
                    name_text = str(row.get('name', ''))
                    if len(name_text) > 20:
                        # 긴 이름은 줄바꿈 표시
                        st.markdown(f"<div style='word-wrap: break-word;'>{name_text}</div>", unsafe_allow_html=True)
                    else:
                        st.write(name_text)
                
                with col3:
                    # 텍스트가 잘리지 않도록 처리 (줄바꿈 허용)
                    music_text = str(row.get('favorite_music', '') or '(없음)')
                    if len(music_text) > 20:
                        # 긴 음악명은 줄바꿈 표시
                        st.markdown(f"<div style='word-wrap: break-word;'>{music_text}</div>", unsafe_allow_html=True)
                    else:
                        st.write(music_text)
                
                with col4:
                    join_date = row.get('join_date', '')
                    if join_date:
                        st.write(str(join_date))
                    else:
                        st.write("")
                
                with col5:
                    # 현재 grade에 맞는 인덱스 찾기
                    current_grade = row.get('grade', '01')
                    current_grade_index = 0
                    for i, (k, v) in enumerate(grade_options.items()):
                        if k == current_grade:
                            current_grade_index = i
                            break
                    
                    # grade dropdown (수정용) - 현재 값이 이미 매핑되어 있음
                    selected_grade_display = st.selectbox(
                        "등급",
                        options=grade_display_options,
                        index=current_grade_index,
                        key=f"user_grade_select_{row['user_id']}_{page}",
                        label_visibility="collapsed"
                    )
                    selected_grade = selected_grade_display.split(":")[0].strip()
                
                with col6:
                    # 저장 버튼 (적절한 크기로 조정)
                    if st.button("💾 저장", key=f"save_grade_{row['user_id']}_{page}", type="primary"):
                        # grade가 변경되었는지 확인
                        if selected_grade != current_grade:
                            # API 호출하여 grade 수정
                            payload = {
                                "user_id": row['user_id'],
                                "name": row['name'],
                                "favorite_music": row.get('favorite_music', ''),
                                "grade": selected_grade
                            }
                            
                            with st.spinner(f"사용자 {row['user_id']}의 등급을 수정하는 중..."):
                                ok, res = call_api_post("update_user_data", payload)
                            
                            if ok and res.get("success"):
                                st.success(f"✅ 사용자 {row['name']} (ID: {row['user_id']})의 등급이 '{selected_grade}'로 변경되었습니다.")
                                st.rerun()
                            else:
                                error_msg = res.get("error", "알 수 없는 오류가 발생했습니다.")
                                st.error(f"❌ 수정 실패: {error_msg}")
                        else:
                            st.info("변경된 내용이 없습니다.")
                
                if idx < len(rows) - 1:  # 마지막 행이 아니면 구분선 표시
                    st.markdown("---")
        
        # 기존 테이블 형식도 유지 (참고용)
        with st.expander("📋 테이블 형식 보기", expanded=False):
            df = pd.DataFrame(rows)
            desired_order = ["user_id", "name", "favorite_music", "join_date", "grade"]
            df = df[desired_order]
            st.table(df)
    else:
        st.info("조회 결과가 없습니다.")
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
    # 사용자 정보 사이드바 출력
    # ---------------------------
    with st.sidebar:
        st.markdown("### 👤 로그인 정보")
        st.write(f"**ID:** {user['user_id']}")
        st.write(f"**이름:** {user['name']}")
        st.write(f"**등급:** {user['grade']}")
        st.markdown("---")
        
    # # ---------------------------
    # # 메인 화면 제목
    # # ---------------------------
    # st.title("📘 메인 화면")

    # -------------------------
    # 사이드바 메뉴
    # -------------------------
    menu_items = ["홈", "내 정보", "기능 B"]
    
    # grade = 99 → 관리자
    if grade == "99":
        menu_items.extend(["사용자 데이터 관리", "사용자 조회"])

    menu = st.sidebar.radio("메뉴 선택", menu_items)

    if menu == "홈":
        show_home_page()
    elif menu == "내 정보":
        show_profile_page()
    elif menu == "사용자 조회":
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
