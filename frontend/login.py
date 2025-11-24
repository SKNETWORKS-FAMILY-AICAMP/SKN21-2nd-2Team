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
from signup import show_signup_page
from utils.spotify_auth import get_token_from_code, get_login_url
from utils.state_manager import init_session, save_tokens

API_URL = "http://localhost:5000/api"

# ------------------------------
# 임시 로그인 계정 목록 (관리자/유저)
# ------------------------------
temp_accounts = {
    "test1": {  # 관리자 계정
        "password": "1234",
        "user_id": 99,
        "name": "Test Admin",
        "grade": "99",
        "favorite_music": "Rock"  # test 계정용 기본값
    },
    "test2": {  # 일반 유저 계정
        "password": "1234",
        "user_id": 1,
        "name": "Test User",
        "grade": "01",
        "favorite_music": "Pop"  # test 계정용 기본값
    }
}

def show_login_page():
    """
    로그인 화면 페이지
    """

    # set_page_config는 run_app.py에서 호출하므로 여기서는 제거

    # Spotify 세션 초기화
    init_session()

    # ------------------------------
    # Spotify 토큰 처리 (Redirect Callback)
    # ------------------------------
    query_params = st.query_params
    if "code" in query_params:
        code_value = query_params["code"]
        # 리스트인 경우 첫 번째 값, 문자열인 경우 그대로 사용
        code = code_value if isinstance(code_value, str) else (code_value[0] if code_value else None)
        
        if code:
            # 이미 처리된 코드인지 확인 (중복 처리 방지)
            processed_codes = st.session_state.get("processed_codes", set())
            
            if code not in processed_codes:
                # 코드를 처리 중으로 표시
                processed_codes.add(code)
                st.session_state.processed_codes = processed_codes
                
                try:
                    with st.spinner("Spotify 토큰 발급 중..."):
                        token_data = get_token_from_code(code)
                    save_tokens(token_data)
                    st.success("✅ Spotify 연동 완료!")
                    # 쿼리 파라미터 제거
                    st.query_params.clear()
                    
                    # 로그인 화면에 머물러서 로그인 폼 표시
                    # (다음 렌더링에서 access_token이 있으므로 로그인 폼이 표시됨)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Spotify 로그인 에러: {str(e)}")
                    processed_codes.discard(code)
                    st.session_state.processed_codes = processed_codes

    # FHD 화면에 맞는 CSS 스타일 추가
    st.markdown("""
    <style>
    /* 로그인 페이지 중앙 정렬 및 적절한 너비 */
    .main .block-container {
        max-width: 600px;
        padding-top: 3rem;
    }
    
    /* 입력 필드 스타일 */
    div[data-testid="stTextInput"] {
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

    # 중앙 정렬을 위한 컬럼 사용
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        st.title("🔐 로그인 페이지")
        
        # 세션 초기화 (최초 1회만, logged_in 상태는 유지)
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            if "logged_in" not in st.session_state:
                st.session_state.logged_in = False
            if "user_info" not in st.session_state:
                st.session_state.user_info = None
        
        # 이미 로그인되어 있으면 Main으로 자동 이동
        if st.session_state.get("logged_in"):
            st.session_state.page = "main"
            st.rerun()
            return
        
        # Spotify 인증 여부에 따라 UI 분기
        if not st.session_state.get("access_token"):
            # Spotify 인증 안 됨 → Spotify 연동 안내
            st.info("🎵 **음악 기능을 사용하려면 먼저 Spotify를 연동하세요**")
            st.markdown("""
            - Spotify Premium 계정이 필요합니다
            - 연동 후 플랫폼 로그인을 진행합니다
            - 로그인 후 바로 음악 검색 및 재생이 가능합니다
            """)
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                login_url = get_login_url()
                st.markdown(f'<a href="{login_url}" target="_self" style="display: block; text-align: center; padding: 1rem 2rem; background-color: #1DB954; color: white; text-decoration: none; border-radius: 0.5rem; font-weight: bold; font-size: 1.1rem;">🎵 Spotify로 시작하기</a>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.caption("💡 Spotify 연동 없이 로그인하려면 관리자에게 문의하세요")
            return
        
        # Spotify 인증 완료 → 로그인 폼 표시
        st.success("✅ Spotify 연동 완료!")
        st.info("이제 플랫폼 계정으로 로그인하세요")
        st.markdown("---")

        st.subheader("로그인 정보를 입력해 주세요.")
        st.markdown("---")

        # 입력 필드
        user_id_input = st.text_input("아이디 (user_id)", placeholder="ID를 입력해주세요 (또는 test1/test2)")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력해주세요")

        # 버튼 영역 (우측 정렬, 동일선상에 가로 배치, 적당한 간격)
        st.markdown("---")
        btn_col1, btn_col2, btn_col3 = st.columns([4, 1.1, 1.1])
        with btn_col1:
            pass  # 빈 공간
        with btn_col2:
            login_button = st.button("🔐 로그인", type="primary")
        with btn_col3:
            signup_button = st.button("📝 회원가입")
        
        if signup_button:
            st.session_state.page = "signup"
            st.rerun()
        
        if login_button:
            st.write("🔍 [LOG] 로그인 버튼 클릭 감지됨")
            st.write(f"🔍 [LOG] 입력된 아이디: '{user_id_input}'")
            st.write(f"🔍 [LOG] 입력된 비밀번호 길이: {len(password)}")

            # ------------------------------
            # 임시 로그인 공통 처리
            # ------------------------------
            if user_id_input.strip() in temp_accounts:
                st.write(f"🔍 [LOG] 임시 계정 체크: '{user_id_input.strip()}' 발견됨")
                acc = temp_accounts[user_id_input.strip()]

                if password.strip() == acc["password"]:
                    st.write("🔍 [LOG] 임시 계정 비밀번호 일치 확인")
                    st.write(f"🔍 [LOG] 계정 정보: user_id={acc['user_id']}, name={acc['name']}, grade={acc['grade']}")
                    
                    st.session_state.logged_in = True
                    st.session_state.user_info = {
                        "user_id": acc["user_id"],
                        "name": acc["name"],
                        "grade": acc["grade"],
                        "favorite_music": acc.get("favorite_music", ""),  # test 계정용 favorite_music 추가
                    }
                    st.session_state.page = "main"  # 페이지 상태 변경 추가
                    
                    st.write("🔍 [LOG] 세션 상태 설정 완료")
                    st.write(f"🔍 [LOG] logged_in: {st.session_state.logged_in}")
                    st.write(f"🔍 [LOG] user_info: {st.session_state.user_info}")
                    st.write(f"🔍 [LOG] page: {st.session_state.page}")
                    
                    st.success("임시 계정으로 로그인되었습니다.")
                    st.write("🔍 [LOG] st.rerun() 호출 전")
                    st.rerun()
                    st.write("🔍 [LOG] st.rerun() 호출 후 (이 메시지는 보이지 않아야 함)")
                    return
                else:
                    st.write("🔍 [LOG] 임시 계정 비밀번호 불일치")
                    st.error("비밀번호가 일치하지 않습니다.")
                    return
            else:
                st.write(f"🔍 [LOG] 임시 계정 아님: '{user_id_input.strip()}'")

            # ------------------------------
            # 실제 API 로그인 로직 (숫자 user_id 전용)
            # ------------------------------

            # 빈 문자열 검증
            if not user_id_input.strip():
                st.error("아이디를 입력해주세요.")
                return

            # 숫자 형식 검증 (임시 계정이 아닌 경우에만)
            if not user_id_input.strip().isdigit():
                st.write("🔍 [LOG] 숫자 형식 검증 실패")
                st.error("아이디는 숫자만 입력 가능합니다. (또는 임시 계정: test1/test2)")
                return

            st.write("🔍 [LOG] 숫자 형식 검증 통과")
            try:
                user_id = int(user_id_input.strip())
                st.write(f"🔍 [LOG] user_id 변환 완료: {user_id}")
            except ValueError as e:
                st.write(f"🔍 [LOG] user_id 변환 실패: {e}")
                st.error("아이디는 숫자만 입력 가능합니다.")
                return

            try:
                st.write(f"🔍 [LOG] API 요청 시작: {API_URL}/login")
                st.write(f"🔍 [LOG] 요청 데이터: user_id={user_id}, password 길이={len(password)}")
                
                # API 요청
                res = requests.post(
                    f"{API_URL}/login",
                    json={"user_id": user_id, "password": password}
                )
                st.write(f"🔍 [LOG] API 요청 완료: status_code={res.status_code}")

                try:
                    data = res.json()
                    # st.write("📡 JSON 응답:", data)
                except Exception as e:
                    st.error(f"JSON 파싱 오류: {e}")
                    return

                # ------------------------------
                # 로그인 성공 여부 판정
                # 백엔드 응답 구조: {"success": True, "user_id": ..., "name": ..., "grade": ...}
                # ------------------------------
                st.write(f"🔍 [LOG] API 응답 상태 코드: {res.status_code}")
                st.write(f"🔍 [LOG] API 응답 데이터: {data}")
                
                if res.status_code == 200 and data.get("success") == True:
                    st.write("🔍 [LOG] API 로그인 성공 조건 만족")
                    # 필수 필드 검증
                    required_fields = ["user_id", "name", "grade"]
                    if all(field in data for field in required_fields):
                        st.write("🔍 [LOG] 필수 필드 검증 통과")
                        st.session_state.logged_in = True
                        st.session_state.user_info = {
                            "user_id": data["user_id"],
                            "name": data["name"],
                            "grade": data["grade"]
                        }
                        st.session_state.page = "main"  # 페이지 상태 변경 추가
                        
                        st.write("🔍 [LOG] 세션 상태 설정 완료")
                        st.write(f"🔍 [LOG] logged_in: {st.session_state.logged_in}")
                        st.write(f"🔍 [LOG] user_info: {st.session_state.user_info}")
                        st.write(f"🔍 [LOG] page: {st.session_state.page}")
                        
                        st.success("로그인 성공!")
                        st.write("🔍 [LOG] st.rerun() 호출 전")
                        st.rerun()
                        st.write("🔍 [LOG] st.rerun() 호출 후 (이 메시지는 보이지 않아야 함)")
                    else:
                        st.write(f"🔍 [LOG] 필수 필드 검증 실패. 누락된 필드: {[f for f in required_fields if f not in data]}")
                        st.error("로그인 실패: 서버 응답 형식 오류")
                else:
                    st.write(f"🔍 [LOG] API 로그인 실패: status_code={res.status_code}, success={data.get('success')}")
                    # 백엔드에서 반환한 에러 메시지 표시
                    error_msg = data.get("message", "아이디 또는 비밀번호를 확인해 주세요.")
                    st.error(f"로그인 실패: {error_msg}")

            except requests.exceptions.ConnectionError:
                st.error("서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.")
            except requests.exceptions.RequestException as e:
                st.error(f"서버 요청 실패: {e}")
            except Exception as e:
                st.error(f"오류 발생: {e}")
    
    # st.write("로그인 테스트 완료 영역 (오류 확인용)")
    

if __name__ == "__main__":
    show_login_page()
